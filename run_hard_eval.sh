#!/bin/bash
# On a GPU host: score ocr_core.py from this folder on a generated hard set,
# inside the given image (default: the submitted one pulled from its registry).
# Usage: run_hard_eval.sh <image> [per_category] [seed]
set -eu
IMAGE=$1
PER_CAT=${2:-12}
SEED=${3:-7}
cd "$(dirname "$0")"

docker pull -q "$IMAGE" >/dev/null 2>&1 || true
docker run --rm --device=/dev/kfd --device=/dev/dri --group-add video \
  --security-opt seccomp=unconfined -v "$PWD:/w" -w /w "$IMAGE" \
  bash -c "rm -rf hard && python3 make_hard.py $PER_CAT $SEED && python3 eval.py hard"
