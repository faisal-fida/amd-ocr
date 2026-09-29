"""Extracts the 10 sample images from the rules PDF into samples/ with expected.json."""
import json
import os
import urllib.request

import pymupdf
from PIL import Image

PDF_URL = "https://storage.googleapis.com/lablab-static-eu/events/LabLab_AMD%20AI%20Challenge%20-%20Mini%20Challenge.pdf"
EXPECTED = [
    ("png", "7ABC123"), ("png", "京A·12345"), ("jpg", "JHT 2951"), ("png", "5XYZ891"),
    ("jpg", "沪B·88888"), ("png", "STOP"), ("tiff", "STOP"), ("jpg", "SPEED LIMIT 65"),
    ("png", "ROAD WORK AHEAD"), ("tiff", "35"),
]

pdf = pymupdf.open(stream=urllib.request.urlopen(PDF_URL).read())
images = []
for page in range(8, 13):
    for xref, *_ in pdf[page].get_images(full=True):
        pix = pymupdf.Pixmap(pdf, xref)
        if pix.n - pix.alpha > 3:
            pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
        images.append(Image.frombytes("RGB" if not pix.alpha else "RGBA", (pix.width, pix.height), pix.samples))

os.makedirs("samples", exist_ok=True)
labels = {}
for i, (img, (ext, text)) in enumerate(zip(images, EXPECTED), 1):
    name = f"image_{i:02d}.{ext}"
    img.convert("RGB").save(f"samples/{name}")
    labels[name] = text
json.dump(labels, open("samples/expected.json", "w"), ensure_ascii=False, indent=1)
print(len(labels), "samples")
