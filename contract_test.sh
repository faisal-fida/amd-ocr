#!/bin/bash
# Mimics the grader: one fresh app.py process per image, then checks outputs.
cd /workspace/ocr
export OCR_OUTPUT_DIR=/workspace/ocr/output
rm -rf output
for f in samples/image_*; do
  s=$(date +%s.%N)
  python3 app.py --input-image "$f" || echo "APP_FAILED $f"
  echo "$(basename $f) $(echo "$(date +%s.%N) - $s" | bc)s"
done
/workspace/venv/bin/python - <<'PY'
import json
from ocr_core import normalize
exp = json.load(open("samples/expected.json"))
ok = 0
for name, want in exp.items():
    got = json.load(open(f"output/{name.rsplit('.', 1)[0]}_output.json"))["text"]
    ok += normalize(got) == normalize(want)
    print(name, repr(got), "PASS" if normalize(got) == normalize(want) else "FAIL")
print(f"contract score {ok}/{len(exp)}")
PY
