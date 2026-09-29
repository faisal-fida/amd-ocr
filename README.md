# PlateSign OCR on AMD ROCm

Reads licence plates and road signs from noisy, blurred or angled images. Built for Mini-Challenge 2 (Optical Character Recognition) of the lablab.ai x AMD AI Academy Challenge.

## How it works

- Model: [Qwen3-VL-8B-Instruct](https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct) in BF16, run with Hugging Face Transformers on ROCm.
- `server.py` loads the model once when the container starts, warms up the GPU, then listens on a Unix socket.
- `app.py` is the entry point the grader calls for each image. It uses only the standard library, sends the image path to the server, and writes `/app/output/<name>_output.json`.
- `ocr_core.py` holds the prompt with the transcription rules: plate number only on US plates, province character kept on Chinese plates, every printed word kept on signs, multi-line text joined top to bottom.

```
python3 /app/app.py --input-image /app/input/image_01.png
# writes /app/output/image_01_output.json  ->  {"text": "7ABC123"}
```

## Build

```
docker build -t ocr .
```

The final stage is `FROM rocm/pytorch:rocm10.0_ubuntu26.04_py3.14_pytorch_release_2.13.0`, not squashed. Model weights are baked into `/models` at a pinned revision.

## Test

- `make_samples.py` extracts the 10 sample images and expected answers from the challenge rules PDF.
- `eval.py` scores the model directly against those samples.
- `grader_test.sh <image>` mimics the grading harness: starts the container, times startup and each `docker exec` call, checks every output, and samples peak VRAM.

Result on an AMD Instinct MI300X:

| Check | Result | Limit |
|---|---|---|
| Sample accuracy | 10/10 | |
| Startup | 20 s | 600 s |
| Per image | 0.16 to 0.35 s | 30 s |
| Peak VRAM | 18.4 GB | 1 to 48 GiB |
| Uncompressed size | 45.7 GiB | 60 GiB |
