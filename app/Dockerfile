FROM python:3.12-slim

WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY assistant ./assistant
COPY knowledge_base ./knowledge_base

RUN useradd --uid 10001 --no-create-home app
USER app

EXPOSE 8080
CMD ["uvicorn", "assistant.main:app", "--host", "0.0.0.0", "--port", "8080"]
