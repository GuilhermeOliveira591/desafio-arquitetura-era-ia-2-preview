"""Cliente do sistema de RH, para as perguntas sobre a situação do próprio colaborador."""

import re

import httpx

from . import config

_client = httpx.Client(base_url=config.HR_BASE_URL, timeout=5.0)

PERSONAL = re.compile(r"\b(eu|meu|minha|meus|minhas)\b", re.IGNORECASE)


def is_personal(question: str) -> bool:
    return bool(PERSONAL.search(question))


def get_employee(tenant_id: str, employee_id: str) -> dict | None:
    response = _client.get(f"/tenants/{tenant_id}/employees/{employee_id}")
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()
