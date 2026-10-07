# HA Lab CI/CD

Open-source laboratory for high availability, load balancing, containerized
web applications, and continuous integration.

## Lab architecture

```text
                     Client
                        |
                VIP 192.168.56.10
                        |
             +----------+----------+
             |                     |
            LB01                  LB02
          HAProxy               HAProxy
         Keepalived            Keepalived
             |                     |
             +----------+----------+
                        |
               +--------+--------+
               |                 |
             WEB01             WEB02
         Rocky + Podman    Rocky + Podman
          Nginx :8080       Nginx :8080
```

This diagram describes the lab topology. This repository contains the web
application and its CI workflow; it does not provision the hosts, configure
HAProxy or Keepalived, or deploy to the lab automatically.

## Repository layout

```text
.github/workflows/ci.yml   Build and HTTP smoke test
.gitignore                Local files excluded from version control
Containerfile             Nginx container image definition
index.html                Application page
LICENSE                   MIT license
README.md                 Project documentation
```

## Run locally with Podman

Requirements: Git, Podman, and an available local TCP port 8080.
Run these commands from the repository root:

```bash
podman build -f Containerfile -t localhost/ha-webapp:local .
podman run --rm -d --name ha-webapp -p 127.0.0.1:8080:80 localhost/ha-webapp:local
curl --fail http://127.0.0.1:8080
podman stop ha-webapp
```

Docker can also build and run this Containerfile by replacing `podman` with
`docker` in the commands above.

## Continuous integration

GitHub Actions runs on pushes to `master`, pull requests targeting `master`,
and manual workflow dispatches. The workflow builds the existing Containerfile,
starts an Nginx container, and verifies that its HTTP response matches index.html.
The job uses a GitHub-hosted runner and read-only repository permissions.

CI does not publish images or deploy to WEB01 and WEB02. Registry publication
and automated deployment are future extensions.

## Contributing

Create a branch, make a focused change, test the container locally, and open a
pull request targeting `master`. Never commit passwords, private keys, or real
environment files. Use `.env.example` with placeholder values when needed.

## License

Distributed under the MIT License. See [LICENSE](LICENSE).
