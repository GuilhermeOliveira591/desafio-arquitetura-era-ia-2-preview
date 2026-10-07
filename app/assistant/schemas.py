from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)


class Source(BaseModel):
    document_id: str
    title: str


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]
    origin: str


class DocumentRequest(BaseModel):
    doc_id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{0,63}$")
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=50000)
