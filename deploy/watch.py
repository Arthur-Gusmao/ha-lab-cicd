#!/usr/bin/env python3
"""Poll trusted master CI and deploy from a locally installed script copy."""
import argparse
import base64
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import urllib.parse
import urllib.request
import uuid

REPO = 'Arthur-Gusmao/ha-lab-cicd'
IMAGE = 'ghcr.io/arthur-gusmao/ha-lab-cicd'
HOSTS = ('192.168.56.11', '192.168.56.12')
STATE_DIR = Path.home() / '.local/state/ha-lab-deploy'
STATE = STATE_DIR / 'state.json'
REMOTE = Path(__file__).with_name('remote.sh')
KEY = Path.home() / '.ssh/ha_lab_deploy'


def api(path):
    request = urllib.request.Request(
        f'https://api.github.com/repos/{REPO}/{path}',
        headers={'Accept': 'application/vnd.github+json',
                 'User-Agent': 'ha-lab-local-deploy',
                 'X-GitHub-Api-Version': '2022-11-28'})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def save(state):
    temp = STATE.with_suffix('.tmp')
    temp.write_text(json.dumps(state, indent=2) + '\n')
    temp.replace(STATE)


def remote(host, action, transaction, image, expected='unused'):
    command = shlex.join(['bash', '-s', '--', action, transaction, image, expected])
    result = subprocess.run(
        ['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
         '-o', 'IdentitiesOnly=yes', '-o', 'ConnectTimeout=10',
         '-o', 'ServerAliveInterval=15', '-o', 'ServerAliveCountMax=3',
         '-i', str(KEY), f'root@{host}', command],
        input=REMOTE.read_text(), text=True, capture_output=True, timeout=600)
    if result.returncode:
        raise RuntimeError(f'{host}: {action} failed\n{result.stderr[-4000:]}')
    return result.stdout.strip()


def recover(state):
    pending = state['pending']
    errors = []
    for host in reversed(pending['touched']):
        try:
            remote(host, 'rollback', pending['id'], 'unused', pending['old_hashes'][host])
            print(f'Rollback verified: {host}', flush=True)
        except Exception as exc:
            errors.append(str(exc))
    if errors:
        raise RuntimeError('Rollback incomplete; transaction retained.\n' + '\n'.join(errors))
    state['failed_sha'] = pending['sha']
    del state['pending']
    save(state)


def eligible(run, sha):
    return (run.get('head_sha') == sha and run.get('head_branch') == 'master'
            and run.get('event') == 'push' and run.get('status') == 'completed'
            and run.get('conclusion') == 'success'
            and run.get('head_repository', {}).get('full_name', '').lower() == REPO.lower())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true', help='Read-only CI check; no deployment')
    parser.add_argument('--retry', action='store_true', help='Retry a previously failed commit')
    args = parser.parse_args()
    os.umask(0o077)
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with (STATE_DIR / 'lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state = json.loads(STATE.read_text()) if STATE.exists() else {}
        if state.get('pending'):
            if args.check:
                raise RuntimeError('An interrupted transaction needs recovery.')
            recover(state)
        if args.retry:
            state.pop('failed_sha', None)
            save(state)
        sha = api('commits/master')['sha']
        if not re.fullmatch('[a-f0-9]{40}', sha):
            raise ValueError('Invalid commit SHA')
        if sha == state.get('deployed_sha'):
            print(f'Already deployed: {sha}')
            return
        if sha == state.get('failed_sha'):
            print(f'Commit blocked after failure: {sha}. Review logs before using --retry.')
            return
        query = urllib.parse.urlencode({'branch': 'master', 'event': 'push', 'head_sha': sha, 'per_page': 1})
        runs = api('actions/workflows/ci.yml/runs?' + query)['workflow_runs']
        if not runs or not eligible(runs[0], sha):
            print(f'Waiting for successful push CI on current master: {sha}')
            return
        print(f'Approved CI: {runs[0]["html_url"]}', flush=True)
        if args.check:
            print(f'Would deploy {IMAGE}:{sha} to {", ".join(HOSTS)}')
            return
        content = api('contents/index.html?ref=' + sha)
        if content.get('encoding') != 'base64':
            raise ValueError('Expected a small, base64-encoded index.html')
        expected = hashlib.sha256(base64.b64decode(content['content'])).hexdigest()
        pending = {'id': uuid.uuid4().hex, 'sha': sha, 'touched': [], 'old_hashes': {}}
        digests = []
        # Pull and snapshot both hosts before changing either running service.
        for host in HOSTS:
            output = remote(host, 'prepare', pending['id'], f'{IMAGE}:{sha}')
            digest, old_hash = output.split()
            if not re.fullmatch('sha256:[a-f0-9]{64}', digest) or not re.fullmatch('[a-f0-9]{64}', old_hash):
                raise ValueError(f'Invalid preparation response from {host}')
            digests.append(digest)
            pending['old_hashes'][host] = old_hash
        if len(set(digests)) != 1:
            raise RuntimeError('Hosts pulled different image digests; deployment cancelled.')
        if api('commits/master')['sha'] != sha:
            print('Master changed during preparation; waiting for the next check.')
            return
        pinned_image = IMAGE + '@' + digests[0]
        state['pending'] = pending
        save(state)
        try:
            for host in HOSTS:
                pending['touched'].append(host)
                save(state)
                remote(host, 'deploy', pending['id'], pinned_image, expected)
                print(f'Deployment verified: {host}', flush=True)
            for _ in range(10):
                with urllib.request.urlopen('http://192.168.56.10/', timeout=10) as response:
                    body = response.read()
                if hashlib.sha256(body).hexdigest() != expected:
                    raise RuntimeError('VIP content does not match the approved commit.')
        except Exception:
            recover(state)
            raise
        del state['pending']
        state.update(deployed_sha=sha, deployed_image=pinned_image, ci_run=runs[0]['html_url'])
        state.pop('failed_sha', None)
        save(state)
        print(f'Deployment complete; both hosts and VIP verified: {sha}', flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(f'ERROR: {exc}', file=sys.stderr, flush=True)
        sys.exit(1)
