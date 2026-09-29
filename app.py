"""Grader entry point: python3 /app/app.py --input-image <path>

Sends the image path to the resident server (server.py) and writes
/app/output/<name>_output.json. Uses only the standard library so it starts fast.
"""
import argparse
import json
import os
import socket
import time
from pathlib import Path

SOCKET = os.environ.get("OCR_SOCKET", "/tmp/ocr.sock")
OUTPUT_DIR = Path(os.environ.get("OCR_OUTPUT_DIR", "/app/output"))
CONNECT_WAIT_S = 25


def ask_server(path):
    deadline = time.time() + CONNECT_WAIT_S
    while True:
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                s.connect(SOCKET)
                s.sendall(json.dumps({"path": path}).encode() + b"\n")
                return json.loads(s.makefile("rb").readline())
        except (FileNotFoundError, ConnectionRefusedError):
            if time.time() > deadline:
                raise
            time.sleep(0.5)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-image", required=True)
    args = parser.parse_args()

    image = Path(args.input_image).resolve()
    reply = ask_server(str(image))
    if "error" in reply:
        raise SystemExit(reply["error"])

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUTPUT_DIR / f"{image.stem}_output.json"
    out.write_text(json.dumps({"text": reply["text"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
