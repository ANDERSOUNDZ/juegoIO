#!/usr/bin/env bash
# download-vendor.sh — Descarga todas las dependencias frontend para offline total
set -euo pipefail

VENDOR_DIR="static/vendor"
FONTS_DIR="$VENDOR_DIR/fonts"
MP_DIR="$VENDOR_DIR/mediapipe"
WASM_DIR="$MP_DIR/wasm"

mkdir -p "$VENDOR_DIR"/phaser \
         "$VENDOR_DIR"/fomantic \
         "$VENDOR_DIR"/jquery \
         "$VENDOR_DIR"/chart.js \
         "$VENDOR_DIR"/nostalgist \
         "$FONTS_DIR" \
         "$WASM_DIR"

log()  { echo "[$1/$TOTAL] $2"; }
curl_() { curl -sL --fail --retry 3 "$1" -o "$2"; }

TOTAL=15

# ── 1. Phaser 3.80.1 ──────────────────────────────────────────────
log 1 "Phaser 3.80.1"
curl_ "https://cdn.jsdelivr.net/npm/phaser@3.80.1/dist/phaser.min.js" \
      "$VENDOR_DIR/phaser/phaser.min.js"

# ── 2-3. Fomantic UI 2.9.3 ────────────────────────────────────────
log 2 "Fomantic UI CSS"
curl_ "https://cdn.jsdelivr.net/npm/fomantic-ui@2.9.3/dist/semantic.min.css" \
      "$VENDOR_DIR/fomantic/semantic.min.css"

log 3 "Fomantic UI JS"
curl_ "https://cdn.jsdelivr.net/npm/fomantic-ui@2.9.3/dist/semantic.min.js" \
      "$VENDOR_DIR/fomantic/semantic.min.js"

# ── 4. jQuery 3.7.1 ───────────────────────────────────────────────
log 4 "jQuery 3.7.1"
curl_ "https://cdn.jsdelivr.net/npm/jquery@3.7.1/dist/jquery.min.js" \
      "$VENDOR_DIR/jquery/jquery.min.js"

# ── 5. Chart.js 4 ─────────────────────────────────────────────────
log 5 "Chart.js 4"
curl_ "https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js" \
      "$VENDOR_DIR/chart.js/chart.umd.min.js"

# ── 6. Nostalgist.js ──────────────────────────────────────────────
log 6 "Nostalgist.js"
curl_ "https://cdn.jsdelivr.net/npm/nostalgist/dist/nostalgist.min.js" \
      "$VENDOR_DIR/nostalgist/nostalgist.min.js"

# ── 7. MediaPipe Hands (legacy) ───────────────────────────────────
log 7 "MediaPipe Hands (legacy)"
curl_ "https://cdn.jsdelivr.net/npm/@mediapipe/hands@0.4.1675469240/hands.min.js" \
      "$MP_DIR/hands.min.js"

# ── 8. MediaPipe Tasks Vision (ESM bundle) ────────────────────────
log 8 "MediaPipe Tasks Vision ESM"
curl_ "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.35/vision_bundle.mjs" \
      "$MP_DIR/vision_bundle.mjs"

# ── 9-10. MediaPipe Tasks Vision WASM ─────────────────────────────
for f in vision_wasm_internal.js vision_wasm_internal.wasm; do
    case "$f" in
        *.js)   log 9 "MediaPipe WASM: $f" ;;
        *.wasm) log 10 "MediaPipe WASM: $f" ;;
    esac
    curl_ "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.35/wasm/$f" \
          "$WASM_DIR/$f"
done

# ── 11. Hand Landmarker model (~12 MB) ────────────────────────────
log 11 "Hand Landmarker model (~12 MB)"
curl_ "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task" \
      "$MP_DIR/hand_landmarker.task"

# ── 12-15. Google Fonts: Plus Jakarta Sans ────────────────────────
log 12 "Google Fonts CSS"
FONT_API="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap"
curl_ "$FONT_API" "/tmp/fonts-google.css"

log 13 "Google Fonts: descargando archivos"
urls=$(grep -oP 'url\(\K[^)]+' /tmp/fonts-google.css | sort -u || true)
count=1
for url in $urls; do
    filename=$(basename "$url" | sed 's/\?.*//')
    echo "  Font $count: $filename"
    curl_ "$url" "$FONTS_DIR/$filename"
    count=$((count + 1))
done

log 14 "Google Fonts: reescribiendo CSS con rutas locales"
sed -E 's|url\(https://fonts\.gstatic\.com[^)]+/([^/)]+)\)|url(/static/vendor/fonts/\1)|g' \
    /tmp/fonts-google.css > "$FONTS_DIR/fonts.css"

log 15 "¡Descarga completa!"
echo ""
echo "Resumen de archivos descargados:"
find "$VENDOR_DIR" -type f -exec ls -lh {} \; 2>/dev/null | awk '{print "  " $5 "  " $NF}' || find "$VENDOR_DIR" -type f | sort
