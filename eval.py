import json
import sys
import time
from collections import Counter
from pathlib import Path

import torch

from ocr_core import OCR, normalize

folder = Path(sys.argv[1] if len(sys.argv) > 1 else "samples")
expected = json.loads((folder / "expected.json").read_text())

t0 = time.time()
ocr = OCR()
print(f"load {time.time() - t0:.1f}s", flush=True)

total, passed, slowest = Counter(), Counter(), 0.0
for name, want in expected.items():
    t = time.time()
    got = ocr.read(folder / name)
    took = time.time() - t
    slowest = max(slowest, took)
    ok = normalize(got) == normalize(want)
    category = name.split("_")[0]
    total[category] += 1
    passed[category] += ok
    print(f"{'PASS' if ok else 'FAIL'} {name} {took:.2f}s got={got!r} want={want!r}", flush=True)

for category in total:
    print(f"{category:10} {passed[category]}/{total[category]}")
print(f"score {sum(passed.values())}/{sum(total.values())}  slowest {slowest:.2f}s  "
      f"peak_vram {torch.cuda.max_memory_allocated() / 2**30:.1f} GiB")
