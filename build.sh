#!/bin/bash
# Builds a self-contained "PR Clippings Filer.app" (Python bundled) and a clean, verified zip to send.
# Output: dist/ (and copies of the app + zip on the Desktop). Re-run after editing clippings_filer.py.
set -e
SRC="$(cd "$(dirname "$0")" && pwd)"
NAME="PR Clippings Filer"
DIST="$SRC/dist"
OUT="$DIST/$NAME.app"
RES="$OUT/Contents/Resources"

# Download the standalone Python builds once (pinned + checksum-verified) into vendor/.
PBS="https://github.com/astral-sh/python-build-standalone/releases/download/20261026"
mkdir -p "$SRC/vendor"
cat > "$SRC/vendor/want.txt" <<'SUMS'
353d5f1b4fd2715e7053f12f068435d5bbad16b91e057006b5d01e0925709a7e  cpython-3.12.16+20261026-aarch64-apple-darwin-install_only_stripped.tar.gz
37c38fda76fec1fbf310adcbafb7f0d96af13b5511bf8ea954c3aa8eec185734  cpython-3.12.16+20261026-x86_64-apple-darwin-install_only_stripped.tar.gz
SUMS
while read -r _ f; do
  [ -f "$SRC/vendor/$f" ] || curl -sSLf -o "$SRC/vendor/$f" "$PBS/$f"
done < "$SRC/vendor/want.txt"
(cd "$SRC/vendor" && shasum -a 256 -c want.txt >/dev/null) || { echo "Python download checksum mismatch"; exit 1; }

# Build the app (outside iCloud-synced folders, so no sync metadata gets baked in).
rm -rf "$DIST" && mkdir -p "$DIST"
osacompile -o "$OUT" -e 'do shell script "/bin/bash " & quoted form of (POSIX path of (path to me) & "Contents/Resources/launch.sh") & " > /dev/null 2>&1 &"'
cp "$SRC/clippings_filer.py" "$SRC/launch.sh" "$RES/"
# Custom icon (made with make_icon.py) if present, otherwise the default script-app icon.
[ -f "$SRC/AppIcon.icns" ] && cp "$SRC/AppIcon.icns" "$RES/applet.icns"
cat "$SRC/clippings_filer.py" "$SRC/launch.sh" "$SRC/vendor/want.txt" | shasum -a 256 | cut -c1-16 > "$RES/BUILD_ID"

# Bundle Python (both chips), trimmed of parts the app never uses.
for arch in arm64:aarch64 x86_64:x86_64; do
  name="${arch%%:*}"; triple="${arch##*:}"
  mkdir -p "$RES/python-$name"
  tar -xzf "$SRC"/vendor/cpython-*-"$triple"-apple-darwin-install_only_stripped.tar.gz -C "$RES/python-$name" --strip-components 1
  L="$(echo "$RES/python-$name"/lib/python3.*)"
  rm -rf "$RES/python-$name"/{include,share} "$L"/{test,idlelib,tkinter,turtledemo,ensurepip,lib2to3,pydoc_data,site-packages/pip*} \
         "$RES/python-$name"/lib/{libtcl*,libtk*,tcl*,tk*,itcl*,thread*} "$L"/config-* 2>/dev/null || true
  find "$RES/python-$name" -name __pycache__ -prune -exec rm -rf {} +
done

# Strip extended attributes, sign (ad-hoc), and verify the seal.
xattr -cr "$OUT"
codesign --force --deep -s - "$OUT" 2>/dev/null
codesign --verify --deep --strict "$OUT"

# Zip without resource forks / extended attributes, then prove it unpacks to a valid app.
ZIP="$DIST/$NAME.zip"
(cd "$DIST" && ditto -c -k --norsrc --noextattr --noacl --keepParent "$NAME.app" "$NAME.zip")
CHECK="$(mktemp -d)"
ditto -x -k "$ZIP" "$CHECK"
codesign --verify --deep --strict "$CHECK/$NAME.app"
rm -rf "$CHECK"

# Copies on the Desktop for convenience.
pkill -f "PR Clippings Filer/clippings_filer.py" 2>/dev/null || true
rm -rf "$HOME/Desktop/$NAME.app" "$HOME/Desktop/$NAME.zip"
ditto --norsrc --noextattr "$OUT" "$HOME/Desktop/$NAME.app"
cp "$ZIP" "$HOME/Desktop/$NAME.zip"
echo "Built and verified: $OUT ($(du -sh "$OUT" | cut -f1))"
echo "Send:               $HOME/Desktop/$NAME.zip ($(du -sh "$ZIP" | cut -f1))"
