#!/usr/bin/env bash
# Build a self-contained Kali/Debian installer on Kali Linux.
set -euo pipefail

PACKAGE_NAME="nexora-lead-finder"
VERSION="1.0.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BUILD_ROOT="$PROJECT_ROOT/.build/kali-deb"
VENV_DIR="$BUILD_ROOT/venv"
DIST_DIR="$BUILD_ROOT/dist"
STAGE_DIR="$BUILD_ROOT/stage"
OUTPUT_DIR="$PROJECT_ROOT/dist"

command -v python3 >/dev/null || { echo "Python 3 is required." >&2; exit 1; }
command -v dpkg-deb >/dev/null || { echo "Run this script on Kali/Debian, where dpkg-deb is available." >&2; exit 1; }

rm -rf "$BUILD_ROOT"
mkdir -p "$BUILD_ROOT" "$DIST_DIR" "$STAGE_DIR/DEBIAN" "$STAGE_DIR/opt/$PACKAGE_NAME" "$STAGE_DIR/usr/local/bin" "$STAGE_DIR/usr/share/applications"

python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r "$PROJECT_ROOT/requirements.txt" pyinstaller

# The executable includes Python and the app dependencies, so end users do not
# need to install Python or pip after installing the .deb.
cd "$PROJECT_ROOT"
"$VENV_DIR/bin/pyinstaller" --clean --noconfirm --onefile --name "$PACKAGE_NAME" \
  --distpath "$DIST_DIR" --workpath "$BUILD_ROOT/pyinstaller-work" \
  --specpath "$BUILD_ROOT" --add-data "nexora_leads/templates:nexora_leads/templates" main.py

install -m 755 "$DIST_DIR/$PACKAGE_NAME" "$STAGE_DIR/opt/$PACKAGE_NAME/$PACKAGE_NAME"
install -m 755 "$SCRIPT_DIR/nexora-lead-finder" "$STAGE_DIR/usr/local/bin/$PACKAGE_NAME"
install -m 644 "$SCRIPT_DIR/nexora-lead-finder.desktop" "$STAGE_DIR/usr/share/applications/$PACKAGE_NAME.desktop"

cat > "$STAGE_DIR/DEBIAN/control" <<EOF
Package: $PACKAGE_NAME
Version: $VERSION
Section: utils
Priority: optional
Architecture: amd64
Maintainer: Nexora Cyber Tech
Depends: xdg-utils
Description: Local public-business lead finder for Nexora Cyber Tech
 Public-business lead research, passive website footprint summaries,
 manual review, and manually sendable outreach drafts.
EOF

mkdir -p "$OUTPUT_DIR"
dpkg-deb --build --root-owner-group "$STAGE_DIR" "$OUTPUT_DIR/${PACKAGE_NAME}_${VERSION}_amd64.deb"
echo "Built: $OUTPUT_DIR/${PACKAGE_NAME}_${VERSION}_amd64.deb"
