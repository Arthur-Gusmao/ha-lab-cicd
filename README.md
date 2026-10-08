# HA Lab CI/CD

[![CI](https://github.com/Arthur-Gusmao/ha-lab-cicd/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/Arthur-Gusmao/ha-lab-cicd/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

A hands-on infrastructure lab combining load balancing, containerized web
servers, GitHub Actions, and automatic deployment from WSL Debian.

**Demonstrated outcome:** a change pushed to `master` was tested, published as a
container image, and deployed to both web servers without manual commands on
the servers. [Read the recorded evidence](docs/validation.md).

## Architecture

```mermaid
flowchart TD
    Client[HTTP client] --> VIP["Virtual IP: 192.168.56.10"]
    VIP --> LB["LB01 / LB02<br/>HAProxy + Keepalived"]
    LB --> W1["WEB01: 192.168.56.11:8080<br/>Rocky Linux / Podman / Nginx"]
    LB --> W2["WEB02: 192.168.56.12:8080<br/>Rocky Linux / Podman / Nginx"]
```

The VIP belongs to the active load balancer. This diagram describes the lab
topology; it does not claim that failover has been tested.

## From commit to deployment

```mermaid
flowchart LR
    Push[Push to master] --> CI[GitHub Actions tests]
    CI --> Registry[GHCR image tagged with commit SHA]
    CI --> API[Successful workflow result]
    API --> Poll[WSL systemd timer polls GitHub]
    Registry --> Pull[Both hosts pull image]
    Poll --> Pull
    Pull --> First[Update and validate WEB01]
    First --> Second[Update and validate WEB02]
    Second --> Check[Validate ten VIP responses]
    First -. Failure .-> Restore[Restore previous Quadlet configuration]
    Second -. Failure .-> Restore
    Check -. Failure .-> Restore
```

- **CI:** tests the deployment controller, builds the Nginx image, and compares
  its HTTP response with the committed `index.html`.
- **Publication:** successful master builds push the tested image to GHCR with
  the full commit SHA as its tag. Pull requests do not publish images.
- **CD:** a local WSL timer checks approximately every five minutes. Only a
  successful push workflow for the current master commit qualifies.
- **Deployment:** SSH runs a locally installed script on each web host. Both
  pulls must resolve to the same digest, which is written into Podman Quadlet.
- **Recovery:** changed hosts are restored after deployment validation failure;
  interrupted transactions are recovered on the next invocation.

The controller is not a GitHub self-hosted runner and does not automatically
download new controller code. Windows, WSL, and the lab VMs must be available.

## Explore the project

- [Architecture and design](docs/architecture.md)
- [Recorded validation](docs/validation.md)
- [Five-minute presentation and demonstration](docs/demo.md)
- [Deployment installation and operations](deploy/README.md)
- [Reproduction scope and next steps](docs/reproduction.md)
- [Contribution guide](CONTRIBUTING.md)

```text
.github/workflows/ci.yml   Tests, container build, HTTP check, GHCR publication
deploy/                   Local CD controller, remote script, installer, tests
docs/                     Architecture, evidence, demo, reproduction scope
Containerfile             Nginx application image
index.html                Static web application
LICENSE                   MIT license
```

## Run the application locally

Requires Git, Podman, and an available local TCP port 8080.

```bash
git clone https://github.com/Arthur-Gusmao/ha-lab-cicd.git
cd ha-lab-cicd
podman build -f Containerfile -t localhost/ha-webapp:local .
podman run --rm -d --name ha-webapp -p 127.0.0.1:8080:80 localhost/ha-webapp:local
curl --fail http://127.0.0.1:8080/
podman stop ha-webapp
```

Docker may be used in place of Podman for these local commands.

## Run controller tests

```bash
python3 -m unittest discover -s deploy -p 'test_*.py' -v
```

## Current limits

Host provisioning and HAProxy/Keepalived configuration are not yet included.
Sequential restarts do not guarantee zero dropped requests: connection draining
is not implemented. Failover and a deliberately failed live deployment have
not been recorded as validated tests. The controller uses root SSH in this lab;
a restricted deployment account is a planned improvement.

The HTTP check is designed for this static application. The `Already deployed`
message reads local deployment state; it is not a continuous health check.

## License

Code and documentation are available under the [MIT License](LICENSE).
