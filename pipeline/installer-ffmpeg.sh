#!/usr/bin/env bash
# ffmpeg pour GitHub Actions. apt d'abord, avec des délais courts : un miroir apt muet a déjà figé l'installation
# 25 min, plusieurs fois. Sinon, un build statique de BtbN publié sur GitHub (ajouté au PATH des étapes suivantes) :
# une version stable d'abord (le build « master », de développement, a figé un encodage AAC de HyperFrames).
# FFMPEG_STATIQUE=1 force le build statique (pour le tester).
set -uo pipefail
ok() { ffmpeg -hide_banner -version | head -1; }
if [ "${FFMPEG_STATIQUE:-0}" != 1 ]; then
  if command -v ffmpeg >/dev/null && command -v ffprobe >/dev/null; then ok; exit 0; fi
  APT="-o Acquire::Retries=2 -o Acquire::http::Timeout=20 -o Acquire::https::Timeout=20"
  JOURNAL="${RUNNER_TEMP:-/tmp}/apt.log"
  if sudo timeout 150 apt-get $APT update > "$JOURNAL" 2>&1 \
     && sudo timeout 150 apt-get $APT install -y -qq ffmpeg >> "$JOURNAL" 2>&1; then
    ok; exit 0
  fi
  echo "apt n'a pas abouti, ffmpeg statique depuis GitHub. Fin du journal apt :"
  tail -5 "$JOURNAL"
fi
DEST="${RUNNER_TEMP:-/tmp}/ffmpeg"
BTBN=https://github.com/BtbN/FFmpeg-Builds/releases/download/latest
for NOM in ffmpeg-n8.1-latest-linux64-gpl-8.1 ffmpeg-n9.0-latest-linux64-gpl-9.0 ffmpeg-master-latest-linux64-gpl; do
  rm -rf "$DEST" && mkdir -p "$DEST"
  if curl -fsSL --retry 3 --max-time 300 "$BTBN/$NOM.tar.xz" | tar -xJ -C "$DEST" --strip-components=1; then break; fi
  echo "$NOM indisponible"
done
[ -x "$DEST/bin/ffmpeg" ] || { echo "ffmpeg : ni apt ni un build statique"; exit 1; }
[ -n "${GITHUB_PATH:-}" ] && echo "$DEST/bin" >> "$GITHUB_PATH"
export PATH="$DEST/bin:$PATH"
ok
