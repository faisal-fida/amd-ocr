import os
import re

import torch
from PIL import Image, ImageOps
from transformers import AutoProcessor, Qwen3VLForConditionalGeneration

MODEL_ID = os.environ.get("OCR_MODEL", "Qwen/Qwen3-VL-8B-Instruct")
MAX_SIDE = int(os.environ.get("OCR_MAX_SIDE", "1600"))

PROMPT = """Read the text on the licence plate or road sign in this image.

Rules:
- Output only the characters that belong to the plate number or the sign text, in reading order.
- Licence plates: output only the registration number. Drop state or country names, slogans, and any text printed around the number (for example CALIFORNIA, NEW YORK, EXCELSIOR).
- Chinese plates: keep the leading province character and letter, they are part of the number (for example 京A·12345).
- Signs: output every word and number printed on the sign (for example SPEED LIMIT 65). Do not add units or words that are not printed.
- Multi-line text: read top to bottom and join the lines with a single space.
- No labels, no explanation, no quotes. Output the text only."""


class OCR:
    def __init__(self, model_id=MODEL_ID):
        self.processor = AutoProcessor.from_pretrained(model_id)
        self.model = Qwen3VLForConditionalGeneration.from_pretrained(
            model_id, dtype=torch.bfloat16, device_map="cuda"
        ).eval()

    @staticmethod
    def load_image(path):
        img = Image.open(path)
        img = ImageOps.exif_transpose(img).convert("RGB")
        img.thumbnail((MAX_SIDE, MAX_SIDE))
        return img

    @torch.inference_mode()
    def read(self, path):
        messages = [{"role": "user", "content": [
            {"type": "image", "image": self.load_image(path)},
            {"type": "text", "text": PROMPT},
        ]}]
        inputs = self.processor.apply_chat_template(
            messages, tokenize=True, add_generation_prompt=True,
            return_dict=True, return_tensors="pt",
        ).to(self.model.device)
        out = self.model.generate(**inputs, max_new_tokens=64, do_sample=False)
        text = self.processor.batch_decode(
            out[:, inputs.input_ids.shape[1]:], skip_special_tokens=True
        )[0]
        return clean(text)


def clean(text):
    lines = [l.strip() for l in text.strip().strip('"\'`').splitlines() if l.strip()]
    return re.sub(r"\s+", " ", " ".join(lines))


def normalize(text):
    return re.sub(r"[\s\-.·_]", "", text.upper())
