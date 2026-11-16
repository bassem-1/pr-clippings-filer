#!/bin/bash
# Launcher for PR Clippings Filer.app.
# The app bundle is never modified. On first launch (or after an update) the bundled Python and app code are
# copied to ~/Library/Application Support, which works even when macOS runs the app from a read-only location.
HERE="$(cd "$(dirname "$0")" && pwd)"
URL="http://localhost:8000"
SUPPORT="$HOME/Library/Application Support/PR Clippings Filer"
LOG="$HOME/Library/Logs/PRClippingsFiler.log"

fail() {
  osascript -e "display dialog \"PR Clippings Filer could not start.\n\n$1\" buttons {\"OK\"} default button 1 with title \"PR Clippings Filer\" with icon caution" >/dev/null 2>&1
  exit 1
}

# Already running? Just open the page.
if curl -s --max-time 2 "$URL" | grep -q "PR Clippings Filer"; then open "$URL"; exit 0; fi

# Something else using the port?
if lsof -nP -iTCP:8000 -sTCP:LISTEN >/dev/null 2>&1; then
  fail "Another program is using port 8000. Quit it (or restart the Mac) and try again."
fi

# Install / update the runtime copy when this build is new.
case "$(uname -m)" in arm64) ARCH=arm64 ;; *) ARCH=x86_64 ;; esac
if [ "$(cat "$SUPPORT/BUILD_ID" 2>/dev/null)" != "$(cat "$HERE/BUILD_ID")" ]; then
  TMP="$SUPPORT.installing"
  rm -rf "$TMP" && mkdir -p "$TMP" || fail "Could not write to $SUPPORT"
  ditto "$HERE/python-$ARCH" "$TMP/python" && cp "$HERE/clippings_filer.py" "$HERE/BUILD_ID" "$TMP/" \
    || fail "Could not copy app files."
  xattr -cr "$TMP" 2>/dev/null
  rm -rf "$SUPPORT" && mv "$TMP" "$SUPPORT" || fail "Could not install to $SUPPORT"
fi

# Start the server in the background (it opens the browser itself).
mkdir -p "$(dirname "$LOG")"
nohup "$SUPPORT/python/bin/python3" "$SUPPORT/clippings_filer.py" >"$LOG" 2>&1 </dev/null &
for _ in $(seq 1 30); do
  curl -s --max-time 1 "$URL" | grep -q "PR Clippings Filer" && exit 0
  sleep 0.5
done
fail "Details are in ~/Library/Logs/PRClippingsFiler.log"
