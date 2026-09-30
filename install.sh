#!/usr/bin/env bash
# Install the Montage plugin for GIMP 3 (distro or Flatpak).
set -e

SRC="$(cd "$(dirname "$0")" && pwd)/montage"

if [ -d "$HOME/.var/app/org.gimp.GIMP/config/GIMP" ] && [ "$1" = "--flatpak" ]; then
  BASE="$HOME/.var/app/org.gimp.GIMP/config/GIMP"
else
  BASE="$HOME/.config/GIMP"
fi

# Pick the newest 3.x config folder, default to 3.0.
VER=$(ls -1 "$BASE" 2>/dev/null | grep -E '^3\.[0-9]+$' | sort -V | tail -n1)
VER=${VER:-3.0}

DEST="$BASE/$VER/plug-ins/montage"
mkdir -p "$DEST"
cp "$SRC/montage.py" "$DEST/montage.py"
chmod +x "$DEST/montage.py"

echo "Installed to $DEST"
echo "Restart GIMP, then use Filters > Montage..."
