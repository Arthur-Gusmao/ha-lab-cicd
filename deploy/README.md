# Local continuous deployment

All deployment code is MIT-licensed and public. No GitHub self-hosted runner is
registered. A local systemd user timer polls the public GitHub API every five
minutes while WSL Debian is running. No GitHub token is required.

The deployment target is the current `master` commit, and only a successful
`push` run of `.github/workflows/ci.yml` for that exact commit qualifies.
Pull requests and manual workflow runs do not trigger deployment.

## Lab prerequisites

- WSL Debian with Python 3, OpenSSH client, systemd and an active user manager.
- Public repository `Arthur-Gusmao/ha-lab-cicd` and public GHCR image.
- Root SSH access to WEB01 (`192.168.56.11`) and WEB02 (`192.168.56.12`).
- Local private key `~/.ssh/ha_lab_deploy` and verified host keys in known_hosts.
- Existing root-managed Podman Quadlet `/etc/containers/systemd/webapp.container`.
- Each host serves its container on port 8080; VIP is `192.168.56.10:80`.

These are lab-specific settings; edit the scripts before using another topology.
Never commit private keys, passwords, or the local deployment state.

## Installation

From the repository root in WSL, as the regular user with the deployment key:

```bash
bash deploy/install.sh
python3 ~/.local/lib/ha-lab-deploy/watch.py --check
systemctl --user enable --now ha-lab-deploy.timer
```

Installation copies scripts to `~/.local/lib/ha-lab-deploy`. The service does not
pull or execute changed deployment scripts from GitHub. Review script changes
and stop the timer/service before reinstalling. Application images are still
code: only trusted maintainers should be able to push/merge to master.

## Deployment and recovery

Both hosts pull the commit-tagged image before any restart. The image digest must
match on both hosts, and Quadlet then references that digest. WEB01 is updated
and verified before WEB02. Validation checks the active service, running image,
and exact HTTP body against index.html at the approved commit. Ten requests to
the VIP must then match. This smoke test is intended for this static Nginx app.

A failure after changes begin restores the previous Quadlet on every touched
host and verifies its previous HTTP body. A failed commit is blocked until a new
commit arrives or an operator explicitly retries it. Pending transactions are
stored before each change: the next invocation attempts rollback after an
interruption. If rollback cannot complete, the pending state is retained and
new deployments are blocked until recovery succeeds.

Backups remain in `/var/lib/ha-lab-deploy` on each host. State is in
`~/.local/state/ha-lab-deploy/state.json` on WSL. Do not delete pending state to
bypass recovery. Preparation failures leave the running application unchanged.

Sequential restarts do not guarantee zero dropped requests: this version does
not drain connections in HAProxy. Failover testing and connection draining are
separate improvements. WSL shutdown/sleep suspends deployment; the timer does
not wake Windows. On the next WSL user session it resumes checks.

```bash
# See recent outcomes and timer status.
journalctl --user -u ha-lab-deploy.service -n 80 --no-pager
systemctl --user list-timers ha-lab-deploy.timer

# Run a check/deployment now (the process lock prevents concurrent changes).
systemctl --user start ha-lab-deploy.service

# Pause future deployments; allow an active deployment to finish.
systemctl --user stop ha-lab-deploy.timer

# After diagnosing a failed deployment, explicitly retry its commit.
python3 ~/.local/lib/ha-lab-deploy/watch.py --retry
```

API/network errors fail the current check and are logged; the timer checks again
later. There are no external notifications configured. Root SSH is inherited
from this lab; a restricted deployment account is a future hardening step.
