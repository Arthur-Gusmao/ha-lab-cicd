#!/usr/bin/env bash
set -Eeuo pipefail
action=$1
transaction=$2
image=$3
expected=$4
[[ "$transaction" =~ ^[a-f0-9]{32}$ ]]
unit=/etc/containers/systemd/webapp.container
backup="/var/lib/ha-lab-deploy/$transaction.container"

health() {
    local actual
    for attempt in {1..30}; do
        if systemctl is-active --quiet webapp.service &&
           actual=$(curl --fail --silent --max-time 3 http://127.0.0.1:8080/ | sha256sum); then
            if [[ "${actual%% *}" == "$expected" ]]; then return 0; fi
        fi
        sleep 2
    done
    echo 'HTTP content or service validation failed.' >&2
    return 1
}

case "$action" in
    prepare)
        [[ -f "$unit" && ! -L "$unit" ]]
        [[ $(grep -c '^Image=' "$unit") == 1 ]]
        systemctl is-active --quiet webapp.service
        mkdir -p /var/lib/ha-lab-deploy
        chmod 700 /var/lib/ha-lab-deploy
        cp -p "$unit" "$backup"
        old_hash=$(curl --fail --silent --show-error --max-time 5 http://127.0.0.1:8080/ | sha256sum)
        podman pull "$image" >&2
        digest=$(podman image inspect "$image" --format '{{.Digest}}')
        [[ "$digest" =~ ^sha256:[a-f0-9]{64}$ ]]
        printf '%s %s\n' "$digest" "${old_hash%% *}"
        ;;
    deploy)
        [[ "$image" =~ ^ghcr.io/arthur-gusmao/ha-lab-cicd@sha256:[a-f0-9]{64}$ ]]
        [[ -f "$backup" ]]
        sed -i "s|^Image=.*|Image=$image|" "$unit"
        systemctl daemon-reload
        systemctl restart webapp.service
        health
        actual_id=$(podman inspect webapp --format '{{.Image}}')
        expected_id=$(podman image inspect "$image" --format '{{.Id}}')
        [[ "${actual_id#sha256:}" == "${expected_id#sha256:}" ]]
        ;;
    rollback)
        cp -p "$backup" "$unit"
        systemctl daemon-reload
        systemctl restart webapp.service
        health
        ;;
    *) exit 2 ;;
esac
