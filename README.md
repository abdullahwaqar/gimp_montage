# GIMP Montage

A GIMP 3 plug-in that arranges your layers in a grid to make a quick photo collage.

## Features

- Live preview: the collage updates as you change settings
- Set columns and rows
- Top-to-bottom or bottom-to-top layer order
- **Fit photos to cells**: scales each photo to fit its cell without distortion, centered
- **Spacing**: gap in pixels between photos
- Works on a copy, so your original image is left alone
- Layers that don't fit in the grid are hidden

## Requirements

GIMP 3.0 or newer, with Python plug-in support (included in most distro and Flatpak builds).

## Install

### Linux

```bash
git clone https://github.com/YOUR_USERNAME/gimp_montage.git
cd gimp_montage
./install.sh            # distro GIMP
./install.sh --flatpak  # Flatpak GIMP
```

### Manual (any OS)

Copy the `montage` folder (with `montage.py` inside) into your GIMP plug-ins folder:

| OS              | Path                                                 |
| --------------- | ---------------------------------------------------- |
| Linux           | `~/.config/GIMP/3.0/plug-ins/`                       |
| Linux (Flatpak) | `~/.var/app/org.gimp.GIMP/config/GIMP/3.0/plug-ins/` |
| Windows         | `%APPDATA%\GIMP\3.0\plug-ins\`                       |
| macOS           | `~/Library/Application Support/GIMP/3.0/plug-ins/`   |

Use your actual version folder (for example `3.2`) if it differs. On Linux and macOS, make sure `montage.py` is executable (`chmod +x`).

## Usage

1. **File > Open as Layers** and select your photos.
2. **Filters > Montage...**
3. Set columns, rows, and spacing, then click OK.

Gaps between photos are transparent. For a colored border, add a filled layer and move it to the bottom.

## Troubleshooting

If the menu entry doesn't show up, start GIMP from a terminal (`gimp`) and check the output for errors from `montage.py`.
