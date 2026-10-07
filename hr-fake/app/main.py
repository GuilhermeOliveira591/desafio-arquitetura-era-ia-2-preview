"""Sistema de RH simulado: cadastro, folha e saldo de férias dos colaboradores de cada empresa cliente."""

import copy

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

SEED = {
    "estrela": {
        "E001": {"name": "Ana Souza", "cpf": "418.273.905-61", "salary": "R$ 4.850,00",
                 "vacation_days": 18, "benefits": ["vale-refeição", "plano de saúde", "auxílio academia"]},
        "E002": {"name": "Carlos Lima", "cpf": "702.115.638-40", "salary": "R$ 3.200,00",
                 "vacation_days": 7, "benefits": ["vale-refeição", "plano de saúde"]},
    },
    "boreal": {
        "B001": {"name": "Bruno Alves", "cpf": "315.948.207-83", "salary": "R$ 7.400,00",
                 "vacation_days": 25, "benefits": ["vale-alimentação", "plano de saúde", "auxílio home office"]},
        "B002": {"name": "Daniela Rocha", "cpf": "529.360.481-12", "salary": "R$ 5.950,00",
                 "vacation_days": 12, "benefits": ["vale-alimentação", "plano de saúde"]},
    },
}

employees = copy.deepcopy(SEED)

app = FastAPI(title="hr-fake", docs_url=None, redoc_url=None)


def not_found():
    return JSONResponse({"error": "colaborador não encontrado"}, status_code=404)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/tenants/{tenant_id}/employees/{employee_id}")
async def get_employee(tenant_id: str, employee_id: str):
    employee = employees.get(tenant_id, {}).get(employee_id)
    if employee is None:
        return not_found()
    return {"tenant_id": tenant_id, "employee_id": employee_id, **employee}


@app.patch("/admin/tenants/{tenant_id}/employees/{employee_id}")
async def update_employee(tenant_id: str, employee_id: str, request: Request):
    employee = employees.get(tenant_id, {}).get(employee_id)
    if employee is None:
        return not_found()
    try:
        body = await request.json()
    except Exception:
        body = None
    if not isinstance(body, dict) or not set(body) <= {"vacation_days", "salary", "benefits"}:
        return JSONResponse({"error": "campos aceitos: vacation_days, salary, benefits"}, status_code=400)
    employee.update(body)
    return {"tenant_id": tenant_id, "employee_id": employee_id, **employee}


@app.post("/admin/reset")
async def reset():
    employees.clear()
    employees.update(copy.deepcopy(SEED))
    return {"status": "ok"}
