import os

APP_ENV = os.environ.get("APP_ENV", "production")

PROVIDER_BASE_URL = os.environ.get("PROVIDER_BASE_URL", "http://provider-fake:8090/openai/v1")
PROVIDER_API_KEY = os.environ.get("FAKE_OPENAI_KEY", "")
CHAT_MODEL = os.environ.get("CHAT_MODEL", "gpt-fake-large")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-fake")
EMBEDDING_DIMENSIONS = int(os.environ.get("EMBEDDING_DIMENSIONS", "256"))

HR_BASE_URL = os.environ.get("HR_BASE_URL", "http://hr-fake:8091")
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://vereda:vereda@postgres:5432/vereda")
KNOWLEDGE_BASE_DIR = os.environ.get("KNOWLEDGE_BASE_DIR", "/srv/knowledge_base")

SEMANTIC_CACHE_THRESHOLD = float(os.environ.get("SEMANTIC_CACHE_THRESHOLD", "0.92"))
RETRIEVAL_TOP_K = int(os.environ.get("RETRIEVAL_TOP_K", "4"))
CHUNK_MAX_CHARS = 1200

OTEL_SERVICE_NAME = os.environ.get("OTEL_SERVICE_NAME", "vereda-assistant")
OTEL_EXPORTER_OTLP_ENDPOINT = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://jaeger:4318")

TENANT_NAMES = {
    "estrela": "Padaria Estrela",
    "boreal": "Metalúrgica Boreal",
}
