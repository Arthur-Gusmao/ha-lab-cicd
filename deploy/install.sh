#!/usr/bin/env bash
set -euo pipefail
source_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
target="$HOME/.local/lib/ha-lab-deploy"
units="$HOME/.config/systemd/user"
command -v python3 >/dev/null
command -v ssh >/dev/null
[[ -f "$HOME/.ssh/ha_lab_deploy" ]]
systemctl --user show-environment >/dev/null
mkdir -p "$target" "$units"
chmod 700 "$target"
install -m 700 "$source_dir/watch.py" "$source_dir/remote.sh" "$target/"
cat > "$units/ha-lab-deploy.service" <<'EOF'
[Unit]
Description=Deploy approved HA Lab images from public GitHub CI

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 %h/.local/lib/ha-lab-deploy/watch.py
TimeoutStartSec=45min
UMask=0077
EOF
cat > "$units/ha-lab-deploy.timer" <<'EOF'
[Unit]
Description=Check HA Lab CI every five minutes while WSL is running

[Timer]
OnStartupSec=60
OnUnitInactiveSec=5min
Unit=ha-lab-deploy.service

[Install]
WantedBy=timers.target
EOF
systemctl --user daemon-reload
printf '%s\n' 'Installed. Check readiness:' \
  'python3 ~/.local/lib/ha-lab-deploy/watch.py --check' \
  'Enable automatic deployments:' \
  'systemctl --user enable --now ha-lab-deploy.timer'
