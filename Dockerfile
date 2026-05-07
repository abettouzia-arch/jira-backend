FROM python:3.12-slim AS base
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY shared/ ./shared/
ENV PYTHONPATH=/app

FROM base AS gateway
COPY gateway/ ./gateway/
CMD ["python", "gateway/app.py"]

FROM base AS parsing_service
COPY parsing_service/ ./parsing_service/
CMD ["python", "parsing_service/app.py"]

FROM base AS compatibility_service
COPY compatibility_service/ ./compatibility_service/
CMD ["python", "compatibility_service/app.py"]

FROM base AS knowledge_service
COPY knowledge_service/ ./knowledge_service/
CMD ["python", "knowledge_service/app.py"]

FROM base AS report_service
COPY report_service/ ./report_service/
CMD ["python", "report_service/app.py"]

FROM base AS worker
COPY worker/ ./worker/
CMD ["python", "worker/app.py"]