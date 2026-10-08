# Architecture and design

## Components

The application is a static HTML page served by an Nginx container. Two Rocky
Linux web hosts run Podman containers managed by systemd through Quadlet.
HAProxy routes traffic to the web backends; Keepalived manages the shared VIP
across the two load-balancer hosts.

Confirmed web endpoints are `192.168.56.11:8080` (WEB01) and
`192.168.56.12:8080` (WEB02). The client endpoint is `192.168.56.10:80`.
The actual load-balancer configuration files have not yet been exported into
this repository; their detailed configuration must be reviewed separately.

## CI responsibilities

The GitHub-hosted job runs on pushes to master, pull requests targeting master,
and manual workflow dispatches. Tests and the HTTP smoke test precede image
publication. GHCR publication uses the workflow's GITHUB_TOKEN and package-write
permission. Pull-request runs cannot enter the publication step.

## CD responsibilities

`ha-lab-deploy.timer` activates a local systemd user service in WSL. The Python
controller reads the public GitHub API without a token. It checks current master
and the latest push run of `ci.yml` for that exact SHA; it does not deploy a
previous successful commit while current master is failing or still running.

Both hosts download the image before either service is changed. A matching
digest is required on both hosts. Each previous Quadlet and HTTP content hash
is recorded. The controller then updates WEB01, checks the service, image ID
and exact HTTP body, and repeats for WEB02. Finally, it validates ten VIP
responses. These requests demonstrate the returned content, not independent
proof that both backends were selected by the load balancer.

## Failure behavior

Deployment state is saved before changes. A failure in the update/verification
phase triggers restoration of each touched host in reverse order. If recovery
cannot finish, the transaction remains pending and blocks new deployments.
A successfully recovered failed commit requires explicit retry or a new commit.
Preparation failures do not modify the running service.

The process lock prevents two local controller instances from updating hosts
concurrently. It cannot coordinate an unrelated administrator or another WSL
installation performing deployment at the same time.

## Trust boundaries

The public repository contains code and documentation. SSH private keys and
local runtime state remain outside it. The installed controller is a local
copy; updating deployment logic requires a deliberate reinstall.

Application images are executable code. Only trusted maintainers should be
allowed to push or merge into master. Root SSH currently gives the local
controller administrative access to both web hosts. This is a lab constraint,
not a production security recommendation.

## Scheduling

The timer waits five minutes after the service becomes inactive. Scheduler
coalescing and deployment duration can make the observed interval longer;
this is not a strict five-minute delivery SLA. WSL must be running. Windows
sleep or shutdown suspends the controller, and no wake-up mechanism is included.
