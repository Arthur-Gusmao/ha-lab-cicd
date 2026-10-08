# Reproduction scope

## Available now

The repository contains the application, container definition, CI workflow,
local CD controller, remote deployment script, installation procedure,
controller tests, and project documentation. The main README explains how to
build and run the application locally. `deploy/README.md` explains the existing
lab prerequisites and how to install the controller.

## Infrastructure still needed for a clean rebuild

The current repository is not yet a complete VM provisioning solution. The
following should be collected from the actual lab and reviewed before publishing:

- Rocky Linux versions, VM CPU/RAM/storage, and VirtualBox network settings.
- HAProxy backend/frontend definitions and health-check settings on both LBs.
- Keepalived interface, VIP, priority, and peer configuration on both LBs.
- Host firewall rules and SELinux-related configuration, if any.
- Web-host bootstrap procedure and original Quadlet template.

Replace passwords, authentication values and unrelated infrastructure details
with explicit placeholders. Do not export SSH private keys, authorized_keys,
complete home directories, shell history, or unfiltered system logs.

## Suggested milestones

- [x] Containerized static application.
- [x] CI builds and validates the application.
- [x] Tested image published to GHCR.
- [x] Local polling and automatic sequential deployment.
- [x] Successful application-change deployment recorded.
- [ ] Publish reviewed infrastructure configuration templates.
- [ ] Automate VM/host provisioning.
- [ ] Validate backend and load-balancer failover.
- [ ] Exercise live rollback in a controlled failure test.
- [ ] Introduce HAProxy connection draining.
- [ ] Restrict the deployment account's privileges.
- [ ] Add deployment failure notifications and independent health monitoring.
