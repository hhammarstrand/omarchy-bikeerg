#!/usr/bin/env bash
set -euo pipefail
plugin_dir="$HOME/.config/omarchy/plugins/hhammarstrand.bikeerg"
source_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [[ "$source_dir" != "$plugin_dir" ]]; then
  echo "Clone the repository into $plugin_dir before running install.sh" >&2
  exit 1
fi
command -v uv >/dev/null
command -v omarchy >/dev/null
uv venv --allow-existing "$HOME/.local/share/bikeerg/venv"
uv pip install --python "$HOME/.local/share/bikeerg/venv/bin/python" -r "$source_dir/requirements.txt"
mkdir -p "$HOME/.config/systemd/user"
cp "$source_dir/systemd/bikeerg.service" "$HOME/.config/systemd/user/bikeerg.service"
systemctl --user daemon-reload
systemctl --user enable --now bikeerg.service
omarchy-shell shell rescanPlugins
omarchy plugin enable hhammarstrand.bikeerg
omarchy bar move hhammarstrand.bikeerg --section center --after omarchy.clock
