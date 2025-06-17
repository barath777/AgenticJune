# FROM python:3.10-slim

# WORKDIR /app

# # Install system dependencies
# RUN apt-get update && apt-get install -y \
#     gcc \
#     libpq-dev \
#     && rm -rf /var/lib/apt/lists/*

# # Install Python packages with optimization flags
# COPY requirements.txt .
# RUN pip install --no-cache-dir \
#     --find-links https://download.pytorch.org/whl/torch_stable.html \
#     --prefer-binary \
#     -r requirements.txt

# COPY . .

# ENV PYTHONUNBUFFERED=1 \
#     PYTHONPATH=/app

# CMD ["sh", "-c", "\
#     if [ \"$RUN_MODE\" = \"batch\" ]; then \
#         python Orchestrator/orchestration.py; \
#     else \
#         uvicorn api.app:app --host 0.0.0.0 --port 8000; \
#     fi"]

FROM python:3.10-slim

WORKDIR /app

COPY . .

# RUN pip install --no-cache-dir -r requirements.txt

# Install Python packages with optimization flags
COPY requirements.txt .
RUN pip install --no-cache-dir \
    --find-links https://download.pytorch.org/whl/torch_stable.html \
    --prefer-binary \
    -r requirements.txt


EXPOSE 8000

CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]