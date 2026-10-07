"""Traces da aplicação, exportados por OTLP/HTTP."""

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from . import config


def setup() -> None:
    resource = Resource.create({"service.name": config.OTEL_SERVICE_NAME,
                                "deployment.environment.name": config.APP_ENV})
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=f"{config.OTEL_EXPORTER_OTLP_ENDPOINT}/v1/traces")
    provider.add_span_processor(BatchSpanProcessor(exporter, schedule_delay_millis=1000))
    trace.set_tracer_provider(provider)


tracer = trace.get_tracer("assistant")
