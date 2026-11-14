# Dose-Safe Translator, as a Hugging Face Docker Space (free CPU tier).
FROM python:3.12-slim

# Spaces run the container as user 1000.
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    HF_HOME=/home/user/.cache/huggingface \
    PYTHONUNBUFFERED=1
WORKDIR /home/user/app

# CPU-only PyTorch: the GPU build is several GB larger and the free tier has no GPU.
COPY --chown=user requirements-app.txt .
RUN pip install --no-cache-dir --user --extra-index-url https://download.pytorch.org/whl/cpu -r requirements-app.txt

# Download the translation model (about 2.5 GB) while building, so a waking Space doesn't have to.
RUN python -c "from transformers import AutoModelForSeq2SeqLM, AutoTokenizer; \
m = 'facebook/nllb-200-distilled-600M'; AutoTokenizer.from_pretrained(m); AutoModelForSeq2SeqLM.from_pretrained(m)"

COPY --chown=user . .
EXPOSE 7860
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "7860"]
