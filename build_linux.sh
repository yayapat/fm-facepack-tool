#!/usr/bin/env bash
# build_linux.sh - Build AppImage for FM Player Face Tool Pro
#
# Prerequisites:
#   pip install pyinstaller
#   wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
#   chmod +x appimagetool-x86_64.AppImage
#
# Usage:
#   chmod +x build_linux.sh
#   ./build_linux.sh

set -euo pipefail

APP_NAME="FMFaceTool"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="$SCRIPT_DIR/build"
DIST_DIR="$SCRIPT_DIR/dist"
APPDIR="$BUILD_DIR/${APP_NAME}.AppDir"

echo "=== Step 1: Build with PyInstaller ==="
pyinstaller "$SCRIPT_DIR/build.spec" --clean --noconfirm

echo "=== Step 2: Create AppDir structure ==="
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"

cp "$DIST_DIR/$APP_NAME" "$APPDIR/usr/bin/$APP_NAME"
cp "$SCRIPT_DIR/assets/icon.png" "$APPDIR/usr/share/icons/hicolor/256x256/apps/${APP_NAME}.png"
cp "$SCRIPT_DIR/assets/icon.png" "$APPDIR/${APP_NAME}.png"

# Desktop entry
cat > "$APPDIR/${APP_NAME}.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=FM Player Face Tool Pro
Exec=FMFaceTool
Icon=FMFaceTool
Categories=Graphics;Utility;
Comment=FM face background removal, resize, and facepack builder
EOF

# AppRun launcher
cat > "$APPDIR/AppRun" <<'APPRUN'
#!/bin/bash
HERE="$(dirname "$(readlink -f "$0")")"
exec "$HERE/usr/bin/FMFaceTool" "$@"
APPRUN
chmod +x "$APPDIR/AppRun"

echo "=== Step 3: Package AppImage ==="
if command -v appimagetool &>/dev/null; then
    APPIMAGETOOL="appimagetool"
elif [ -f "$SCRIPT_DIR/appimagetool-x86_64.AppImage" ]; then
    APPIMAGETOOL="$SCRIPT_DIR/appimagetool-x86_64.AppImage"
else
    echo "Error: appimagetool not found."
    echo "Download it from: https://github.com/AppImage/AppImageKit/releases"
    echo "  wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
    echo "  chmod +x appimagetool-x86_64.AppImage"
    exit 1
fi

ARCH=x86_64 "$APPIMAGETOOL" "$APPDIR" "$DIST_DIR/${APP_NAME}-x86_64.AppImage"

echo ""
echo "=== Done ==="
echo "AppImage: $DIST_DIR/${APP_NAME}-x86_64.AppImage"
