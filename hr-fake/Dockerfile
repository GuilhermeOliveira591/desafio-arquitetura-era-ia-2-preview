FROM python:3.12-slim

WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app

RUN useradd --uid 10001 --no-create-home fake
USER fake

EXPOSE 8091
HEALTHCHECK --interval=5s --timeout=3s --retries=10 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8091/health')"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8091", "--no-access-log"]
