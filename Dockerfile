FROM rocm/pytorch:rocm10.0_ubuntu26.04_py3.14_pytorch_release_2.13.0

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

RUN hf download Qwen/Qwen3-VL-8B-Instruct \
        --revision 0c351dd01ed87e9c1b53cbc748cba10e6187ff3b \
        --local-dir /models/Qwen3-VL-8B-Instruct \
    && rm -rf /models/Qwen3-VL-8B-Instruct/.cache

ENV OCR_MODEL=/models/Qwen3-VL-8B-Instruct \
    HF_HUB_OFFLINE=1 \
    PYTHONUNBUFFERED=1

COPY app.py server.py ocr_core.py /app/
RUN mkdir -p /app/input /app/output

WORKDIR /app
HEALTHCHECK --interval=5s --start-period=600s CMD test -S /tmp/ocr.sock
CMD ["python3", "/app/server.py"]
