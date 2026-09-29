#!/bin/bash
# Mimics the grading harness against a built image. Usage: grader_test.sh <image>
set -u
IMAGE=$1
NAME=ocr-grader-test

echo "== size (uncompressed, bytes)"
docker image inspect "$IMAGE" --format '{{.Size}}' | awk '{printf "%.1f GiB\n", $1/2^30}'

docker rm -f $NAME >/dev/null 2>&1
start=$(date +%s)
docker run -d --name $NAME --device=/dev/kfd --device=/dev/dri --group-add video \
  --security-opt seccomp=unconfined -v "$PWD/samples:/app/input:ro" "$IMAGE" >/dev/null

( peak=0; while docker inspect $NAME >/dev/null 2>&1; do
    v=$(amd-smi metric --mem --json 2>/dev/null | python3 -c "import sys,json;d=json.load(sys.stdin);d=d if isinstance(d,list) else d.get('gpu_data',[d]);print(max(int(g['mem_usage']['used_vram']['value']) for g in d))" 2>/dev/null || echo 0)
    [ "$v" -gt "$peak" ] && peak=$v && echo "$peak" > /tmp/peak_vram_mb
    sleep 3
  done ) &

until [ "$(docker inspect -f '{{.State.Health.Status}}' $NAME)" = healthy ]; do
  [ "$(docker inspect -f '{{.State.Running}}' $NAME)" = true ] || { docker logs $NAME | tail -20; exit 1; }
  sleep 2
done
echo "== startup $(( $(date +%s) - start ))s (limit 600s)"

echo "== per image (limit 30s)"
run_start=$(date +%s)
for f in samples/image_*; do
  n=$(basename "$f")
  s=$(date +%s%N)
  docker exec $NAME python3 /app/app.py --input-image "/app/input/$n" || echo "FAILED $n"
  echo "$n $(( ($(date +%s%N) - s) / 1000000 ))ms"
done
echo "== total run $(( $(date +%s) - run_start ))s (limit 600s)"

echo "== outputs"
python3 - <<'PY'
import json, re, subprocess
exp = json.load(open("samples/expected.json"))
norm = lambda t: re.sub(r"[\s\-.·_]", "", t.upper())
ok = 0
for name, want in exp.items():
    out = f"/app/output/{name.rsplit('.', 1)[0]}_output.json"
    got = json.loads(subprocess.run(["docker", "exec", "ocr-grader-test", "cat", out], capture_output=True, text=True).stdout)["text"]
    ok += norm(got) == norm(want)
    print(("PASS" if norm(got) == norm(want) else "FAIL"), name, repr(got))
print(f"score {ok}/{len(exp)}")
PY
sleep 4
echo "== peak VRAM $(cat /tmp/peak_vram_mb 2>/dev/null) MB (limit 1024 to 49152 MB)"
docker rm -f $NAME >/dev/null
