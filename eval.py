import json
import sys
import time
from pathlib import Path

import torch

from ocr_core import OCR, normalize

folder = Path(sys.argv[1] if len(sys.argv) > 1 else "samples")
expected = json.loads((folder / "expected.json").read_text())

t0 = time.time()
ocr = OCR()
print(f"load {time.time() - t0:.1f}s", flush=True)

passed = 0
for name, want in expected.items():
    t = time.time()
    got = ocr.read(folder / name)
    ok = normalize(got) == normalize(want)
    passed += ok
    print(f"{'PASS' if ok else 'FAIL'} {name} {time.time() - t:.2f}s got={got!r} want={want!r}", flush=True)

print(f"score {passed}/{len(expected)}  peak_vram {torch.cuda.max_memory_allocated() / 2**30:.1f} GiB")
