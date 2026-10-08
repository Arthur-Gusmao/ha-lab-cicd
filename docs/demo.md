# Presentation and demonstration

## 1. State the objective

"This lab connects source control to a running containerized application.
A push to master passes CI, publishes an image, and triggers sequential
deployment to two web servers through a local controller."

Show the architecture and pipeline diagrams in the main README.

## 2. Explain the implementation

Open `.github/workflows/ci.yml` and show the test, build, HTTP validation and
publication steps. Then show `deploy/watch.py` and `deploy/remote.sh`: the
controller qualifies a commit, uses SSH, pins the image digest, validates
each host, and restores prior configuration if deployment fails.

Mention that the entire implementation is public under MIT, while SSH keys
remain local. The CD component is a WSL systemd service, not a GitHub runner.

## 3. Show recorded evidence

Open [validation.md](validation.md) and its linked CI run. Explain the actual
application change and the successful WEB01, WEB02 and VIP checks.

## 4. Optional live demonstration

Before starting, boot the four lab VMs and WSL, verify SSH connectivity, and
confirm the timer is active. A live demo may take several minutes after CI
finishes; allow time for the polling interval.

In WSL:

```bash
cd ~/ha-webapp
git status --short
systemctl --user list-timers ha-lab-deploy.timer
curl --fail --silent --show-error http://192.168.56.10/
```

With a clean working tree, edit only the heading in `index.html`, inspect the
diff, then commit and push:

```bash
git diff -- index.html
git add index.html
git commit -m "demo: update application heading"
git push origin master
```

Watch Actions in the browser. In a second terminal, follow the local CD log:

```bash
journalctl --user -u ha-lab-deploy.service -f
```

After `Deployment complete`, use another terminal to show the new response:

```bash
curl --fail --silent --show-error http://192.168.56.10/
```

Do not type shell commands into the journal viewer; exit it with Ctrl+C first
or use a second terminal. Do not claim completion while the old commit is
still reported or the workflow remains pending.

## 5. Explain the limits

The lab demonstrates CI/CD and a redundant topology. Connection draining,
failover validation, restricted deployment permissions, and reproducible VM
provisioning remain improvements. Sequential deployment alone does not prove
zero downtime. Explain these distinctions when discussing reliability.
