# Reading licence plates and road signs with Qwen3-VL on AMD ROCm

A practical walkthrough of my solution to Mini-Challenge 2 (OCR) of the lablab.ai x AMD AI Academy Challenge: what the grader expects, how I packaged a vision-language model so it passes every hard gate, and how I tested it against images harder than the samples.

Code: https://github.com/faisal-fida/amd-ocr

## 1. What the grader actually checks

The challenge runs your Docker image on an AMD GPU and calls one script per test image:

```
python3 /app/app.py --input-image /app/input/image_01.png
```

Your script writes `/app/output/image_01_output.json` containing `{"text": "..."}`. Ten hidden images, 20 points each, pass or fail after normalization (uppercase, whitespace and `- . · _` removed).

Before scoring, three hard gates can zero the whole submission:

- The final build stage must start `FROM rocm/pytorch:rocm10.0_ubuntu26.04_py3.14_pytorch_release_2.13.0`. The check compares image layers, so never squash or flatten the image.
- 60 GiB maximum, measured uncompressed.
- Startup within 10 minutes, each image within 30 seconds, all ten within 10 minutes. Peak VRAM between 1 and 48 GiB.

Most lost points in this challenge come from packaging, not model quality.

## 2. The key design choice: load once, answer many times

The grader starts a new Python process for every image. Loading an 8B model takes 30 to 40 seconds, which alone would blow the 30-second per-image budget.

So the container's main process is a small server:

- `server.py` loads the model once at container start (inside the 10-minute startup budget), runs one warm-up inference, then listens on a Unix socket.
- `app.py`, the script the grader calls, uses only the Python standard library. It sends the image path over the socket and writes the JSON answer. Each call takes well under a second.

The warm-up matters. The first GPU inference compiles kernels and took about 10 seconds on an MI300X. Doing it before the server reports ready means no graded image pays that cost.

## 3. Model and prompt

I used `Qwen/Qwen3-VL-8B-Instruct` in BF16 with Hugging Face Transformers on ROCm. About 17 GB of weights, 18 GB peak VRAM, and it reads Chinese characters natively, which the Chinese plates need.

The transcription rules live in the prompt, not in post-processing:

- US plates: return the registration number only, not the state name or slogan (`CALIFORNIA 7ABC123` becomes `7ABC123`).
- Chinese plates: keep the province character and letter, they are part of the number (`京A·12345`).
- Signs: keep every printed word (`SPEED LIMIT 65`), add no units.
- Multi-line text: read top to bottom, join with single spaces (`ROAD WORK AHEAD`).

Weights are baked into `/models` at a pinned revision, and `HF_HUB_OFFLINE=1` is set after the download step, so the container never depends on the network at grading time.

## 4. Test like the grader, before you submit

`grader_test.sh` reproduces the harness on a GPU machine: it starts the container, waits for the health check, times each `docker exec`, checks every output file, and samples peak VRAM every 3 seconds. Result on an AMD Instinct MI300X:

| Check | Result | Limit |
|---|---|---|
| Sample accuracy | 10/10 | |
| Startup | 20 s | 600 s |
| Per image | 0.16 to 0.35 s | 30 s |
| Peak VRAM | 18.4 GB | 1 to 48 GiB |
| Uncompressed size | 45.7 GiB | 60 GiB |

## 5. Going beyond the ten samples

The graded set is deliberately harder than the samples. `make_hard.py` generates a synthetic set across every category in the brief: US plates from 12 state designs with slogans, Chinese plates, stop signs, speed limits, advisory plaques and multi-line warning signs. Each image gets random blur, motion blur, noise, low light, glare, perspective, rotation, heavy JPEG, very low resolution or very large size.

Results with the submitted image on 432 generated images across three random seeds: 71/72, 179/180 and 178/180. The remaining misses are Chinese plates or warning signs under strong glare or extreme low resolution.

One lesson: I tried a confidence-based second pass on an illumination-corrected copy of low-confidence images. On an unseen seed it scored exactly the same as without it, so I removed it. Measure on data you did not tune on before keeping a change.

## 6. Practical lessons from the infrastructure

- The free notebook pod has a 3-hour daily GPU quota and no Docker. Develop and test there, build elsewhere.
- In the pod, a plain virtual environment can pull the CUDA build of PyTorch as a dependency. Point the venv at the base image's ROCm packages instead.
- Build the image on an AMD Developer Cloud GPU droplet: x86, Docker preinstalled, fast network, and you can run the final container on a real Instinct GPU. Destroy the droplet when done, since a powered-off droplet still bills.
- New ghcr.io packages are private. The grader must pull anonymously, so make the package public and verify the manifest with an anonymous token before submitting.
