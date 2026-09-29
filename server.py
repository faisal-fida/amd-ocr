"""Loads the model once and answers OCR requests over a Unix socket.

Started as the container's main process, so model load happens inside the
startup budget and each app.py call only pays for inference.
"""
import json
import os
import socketserver
import tempfile

from PIL import Image

from ocr_core import OCR

SOCKET = os.environ.get("OCR_SOCKET", "/tmp/ocr.sock")


class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        request = json.loads(self.rfile.readline())
        try:
            reply = {"text": ocr.read(request["path"])}
        except Exception as e:
            reply = {"error": repr(e)}
        self.wfile.write(json.dumps(reply, ensure_ascii=False).encode() + b"\n")


if __name__ == "__main__":
    ocr = OCR()
    # The first GPU inference compiles kernels (~10 s on MI300X); pay it before
    # reporting ready so no graded image hits the 30 s per-image budget.
    with tempfile.NamedTemporaryFile(suffix=".png") as warmup:
        Image.new("RGB", (640, 320), "white").save(warmup.name)
        ocr.read(warmup.name)
    if os.path.exists(SOCKET):
        os.remove(SOCKET)
    with socketserver.UnixStreamServer(SOCKET, Handler) as server:
        print(f"ready on {SOCKET}", flush=True)
        server.serve_forever()
