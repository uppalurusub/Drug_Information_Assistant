# Drug Information Assistant

A FastAPI-based **Drug Information Assistant** that combines **Retrieval-Augmented Generation (RAG)**, **LangChain**, **Chroma vector search**, **Hugging Face sentence embeddings**, an **OpenAI-compatible LLM endpoint**, and **MLflow observability** to answer drug-information queries.

> **Important:** This repository is an educational/reference implementation. It should not be treated as a clinical decision-support system or a substitute for a qualified pharmacist/physician or authoritative prescribing information.

---

## 1. Overview

The application exposes a REST API through FastAPI.

For a drug-information request, the application:

1. Receives the drug name through the `/drug/information` endpoint.
2. Validates and normalizes the input in the service layer.
3. Retrieves relevant content from the local drug knowledge base.
4. Uses Chroma as the vector store and `all-MiniLM-L6-v2` as the embedding model.
5. Builds a controlled prompt containing the retrieved context and drug name.
6. Sends the prompt to the configured OpenAI-compatible LLM endpoint.
7. Requests structured output using the Pydantic `DrugResponse` model.
8. Returns the generated drug information through FastAPI.
9. Records request/execution information in MLflow.
10. Writes application and error logs using Loguru.

---

## 2. High-Level Architecture

```text
                         ┌──────────────────────┐
                         │      Client/User     │
                         └──────────┬───────────┘
                                    │
                                    │ POST /drug/information
                                    ▼
                         ┌──────────────────────┐
                         │      FastAPI API     │
                         │   drug_router.py     │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │     DrugService      │
                         │  Validation + MLflow │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │  DrugImplementation  │
                         │   RAG + LLM logic    │
                         └───────┬───────┬──────┘
                                 │       │
                    Retrieval    │       │ Prompt + LLM
                                 │       │
                                 ▼       ▼
                       ┌─────────────┐  ┌────────────────┐
                       │   Chroma    │  │ OpenAI-Compat. │
                       │ Vector DB   │  │      LLM       │
                       └──────┬──────┘  └───────┬────────┘
                              │                  │
                              ▼                  ▼
                       ┌─────────────┐    ┌──────────────┐
                       │ Embeddings  │    │ Structured   │
                       │ MiniLM      │    │ DrugResponse │
                       └─────────────┘    └──────┬───────┘
                                                  │
                                                  ▼
                                           API Response

             ┌────────────────────────────────────────────┐
             │ MLflow Tracking + Loguru Application Logs  │
             └────────────────────────────────────────────┘
```

---

## 3. Project Structure

```text
app/
├── main.py
│
├── config/
│   └── llm_config.py
│
├── models/
│   ├── request_model.py
│   └── response_model.py
│
├── routers/
│   └── drug_router.py
│
├── services/
│   └── drug_service.py
│
├── implementations/
│   └── drug_impl.py
│
├── prompts/
│   └── drug_prompt.py
│
└── utils/
    ├── logger.py
    └── vector_store.py
```

The uploaded archive currently contains the Python application source and compiled `__pycache__` files. It does **not** contain a `data/drugs.txt`, `.env`, `requirements.txt`, `pyproject.toml`, Dockerfile, or MLflow configuration file. These need to be supplied separately for a reproducible deployment.

---

## 4. Layered Design

The project follows a useful:

```text
Router → Service → Implementation → RAG / LLM
```

pattern.

### Router

`app/routers/drug_router.py`

Responsibilities:

- Define HTTP endpoints.
- Receive Pydantic request models.
- Invoke the service layer.
- Translate validation/unexpected errors into HTTP responses.
- Define API tags and response models.

Endpoint:

```text
POST /drug/information
```

---

### Service

`app/services/drug_service.py`

Responsibilities:

- Validate the drug name.
- Normalize input using `strip()`.
- Start and manage MLflow runs.
- Measure execution time.
- Invoke `DrugImplementation`.
- Return a `DrugResponse`.

---

### Implementation

`app/implementations/drug_impl.py`

Responsibilities:

- Initialize the LLM.
- Load the vector store.
- Create a retriever.
- Retrieve relevant documents.
- Construct the RAG prompt.
- Invoke the LLM.
- Request structured Pydantic output.

This is the core RAG/LLM implementation layer.

---

### Prompt

`app/prompts/drug_prompt.py`

The prompt instructs the LLM to:

- Explain drug usage.
- Provide dosage information.
- List common side effects.
- Mention warnings when available.
- Use only retrieved context.
- Avoid hallucinating.
- Return a predefined response structure.

---

### Vector Store

`app/utils/vector_store.py`

The vector-store workflow is:

```text
data/drugs.txt
      │
      ▼
TextLoader
      │
      ▼
RecursiveCharacterTextSplitter
chunk_size = 500
chunk_overlap = 50
      │
      ▼
Hugging Face Embeddings
all-MiniLM-L6-v2
      │
      ▼
Chroma
persist_directory = vector_db
      │
      ▼
Retriever
k = 3
```

If `vector_db/` already exists, it is loaded instead of being rebuilt.

---

## 5. RAG Flow

For a request such as:

```json
{
  "drug_name": "Paracetamol"
}
```

the application performs:

```text
"Paracetamol"
      │
      ▼
Vector similarity search
      │
      ▼
Top 3 relevant chunks
      │
      ▼
Context construction
      │
      ▼
Drug Information Prompt
      │
      ▼
Configured LLM
      │
      ▼
Structured DrugResponse
      │
      ▼
FastAPI JSON response
```

This is a **retrieval-grounded generation** design. The LLM is expected to answer from the retrieved knowledge-base context rather than relying solely on its pretrained knowledge.

---

## 6. API Endpoints

### Root

```http
GET /
```

Example response:

```json
{
  "application": "Drug Information Assistant",
  "version": "1.0.0",
  "status": "Running"
}
```

---

### Application Health

```http
GET /health
```

Example response:

```json
{
  "status": "UP",
  "application": "Drug Information Assistant"
}
```

---

### Drug Service Health

```http
GET /drug/health
```

Example response:

```json
{
  "status": "UP",
  "service": "Drug Information Assistant",
  "message": "Service is running successfully"
}
```

---

### Drug Information

```http
POST /drug/information
Content-Type: application/json
```

Request:

```json
{
  "drug_name": "Paracetamol",
  "language": "English",
  "user_id": "user123",
  "session_id": "session001"
}
```

The current implementation primarily uses `drug_name`. The `language`, `user_id`, and `session_id` fields are defined in the request model but are not currently propagated into the prompt or processing logic.

Expected successful response shape:

```json
{
  "drug_name": "Paracetamol",
  "usage": "...",
  "dosage": "...",
  "side_effects": [
    "..."
  ],
  "source": "Drug Knowledge Base",
  "status": "SUCCESS"
}
```

---

## 7. Request Model

Defined in:

```text
app/models/request_model.py
```

```text
DrugRequest
├── drug_name: str
├── language: str = "English"
├── user_id: Optional[str]
└── session_id: Optional[str]
```

`drug_name` is required.

---

## 8. Response Model

Defined in:

```text
app/models/response_model.py
```

Current fields:

```text
DrugResponse
├── drug_name
├── usage
├── dosage
├── side_effects
├── source
└── status
```

The implementation currently attempts to populate a `warnings` field in error responses, but `DrugResponse` does not currently declare `warnings`. This should be corrected before production use.

---

## 9. LLM Configuration

The application loads environment variables using `python-dotenv`.

`app/config/llm_config.py` expects:

```text
fallback_model_2
openrouter_api_key
base_url
```

Conceptually:

```env
fallback_model_2=<model-name>
openrouter_api_key=<api-key>
base_url=<openai-compatible-base-url>
```

Example for an OpenRouter-style setup:

```env
fallback_model_2=<your-model>
openrouter_api_key=<your-key>
base_url=<your-openai-compatible-base-url>
```

Do **not** commit real API keys to source control.

---

## 10. Required Python Dependencies

The archive does not contain a dependency manifest. Based on the source code, the project requires packages from the following ecosystem:

```text
fastapi
uvicorn
pydantic
python-dotenv
loguru
mlflow
langchain
langchain-core
langchain-community
langchain-text-splitters
langchain-openai
langchain-huggingface
langchain-chroma
chromadb
sentence-transformers
```

Depending on the installed versions, additional transitive dependencies may be required.

A proper project should pin compatible versions in `requirements.txt` or `pyproject.toml`.

---

## 11. Installation

Create a virtual environment:

```bash
python -m venv .venv
```

### Windows

```bash
.venv\Scripts\activate
```

### Linux/macOS

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

If a requirements file has not yet been created, install the dependencies listed above and then generate a reproducible dependency file:

```bash
pip freeze > requirements.txt
```

---

## 12. Knowledge Base

The vector-store implementation expects:

```text
data/drugs.txt
```

The file should contain authoritative drug information that the application is permitted to use.

Recommended structure:

```text
Drug: Paracetamol

Usage:
...

Dosage:
...

Side Effects:
...

Warnings:
...
```

For production healthcare use, the knowledge base should be sourced, versioned, reviewed, and governed by qualified clinical/pharmacy professionals.

---

## 13. Running the Application

From the project root:

```bash
uvicorn app.main:app --reload
```

The API should then be available at:

```text
http://localhost:8000
```

Swagger/OpenAPI UI:

```text
http://localhost:8000/docs
```

ReDoc:

```text
http://localhost:8000/redoc
```

---

## 14. Starting MLflow

The service is configured to send tracking data to:

```text
http://localhost:5000
```

Start MLflow separately, for example:

```bash
mlflow ui --host 0.0.0.0 --port 5000
```

Then open the MLflow UI at:

```text
http://localhost:5000
```

The configured experiment is:

```text
Drug_Information_Assistant_Interface
```

The service records:

- Input drug name.
- Start time.
- End time.
- Execution time.
- Endpoint metadata.
- Source metadata.

---

## 15. Logging

Logging is implemented with **Loguru**.

The logger creates:

```text
logs/
├── healthcare.log
└── error.log
```

`main.py` also configures:

```text
logs/drug_information_assistant.log
```

with rotation and retention settings.

The project therefore currently has overlapping logger configuration in `app/utils/logger.py` and `app/main.py`. A production implementation should centralize logging configuration in one place.

---

## 16. Vector Database Lifecycle

The application uses:

```text
Chroma
```

with:

```text
vector_db/
```

as the persistence directory.

First startup:

```text
drugs.txt
   ↓
load documents
   ↓
split into chunks
   ↓
generate embeddings
   ↓
create Chroma database
```

Subsequent startup:

```text
vector_db/
   ↓
load existing Chroma database
```

If the source knowledge base changes substantially, the vector database should be rebuilt or versioned rather than blindly reusing stale embeddings.

---

## 17. Example cURL Request

```bash
curl -X POST "http://localhost:8000/drug/information" \
  -H "Content-Type: application/json" \
  -d "{\"drug_name\":\"Paracetamol\",\"language\":\"English\"}"
```

---

## 18. Example Python Client

```python
import requests

payload = {
    "drug_name": "Paracetamol",
    "language": "English"
}

response = requests.post(
    "http://localhost:8000/drug/information",
    json=payload
)

print(response.status_code)
print(response.json())
```

---

## 19. Error Handling

The router distinguishes between:

### Validation errors

A `ValueError` from the service layer is returned as:

```text
HTTP 400 Bad Request
```

### Unexpected errors

Unexpected exceptions are returned as:

```text
HTTP 500 Internal Server Error
```

The implementation layer also returns a `DrugResponse` with:

```text
status = "FAILED"
```

when an exception occurs.

A future production version should establish a consistent exception-handling strategy rather than mixing returned failure objects and HTTP exceptions.

---

# 20. Important Code Review Findings

The archive was reviewed as supplied. The following items should be addressed.

## 20.1 Missing `data/drugs.txt`

`vector_store.py` expects:

```text
data/drugs.txt
```

but the uploaded archive does not contain this file.

Without it, initial vector-store creation will fail.

**Recommendation:** Add:

```text
data/drugs.txt
```

and document its source/version.

---

## 20.2 Missing dependency manifest

The archive does not contain:

```text
requirements.txt
```

or:

```text
pyproject.toml
```

This makes environment reproduction difficult.

**Recommendation:** Add a pinned `requirements.txt` or modern `pyproject.toml`.

---

## 20.3 Response model mismatch

`drug_impl.py` creates:

```python
DrugResponse(
    ...
    warnings=[],
    ...
)
```

but `response_model.py` does not define a `warnings` field.

This is a design inconsistency and can produce Pydantic validation problems.

**Recommendation:** Add:

```python
warnings: List[str] = Field(
    default_factory=list,
    description="Important warnings and precautions"
)
```

if warnings are part of the intended response contract.

---

## 20.4 Error response references an undeclared field

The same `warnings` mismatch appears in the exception path.

The implementation should return only fields defined by `DrugResponse`, or the model should be expanded.

---

## 20.5 MLflow `log_param` usage

The service currently does:

```python
mlflow.log_param("response", response)
```

where `response` is a Pydantic object.

MLflow parameters should be logged as supported scalar/string values rather than arbitrary model objects.

**Recommendation:**

```python
mlflow.log_param(
    "response_status",
    response.status
)
```

and, if needed, log the serialized response as an artifact:

```python
mlflow.log_text(
    response.model_dump_json(),
    "response.json"
)
```

---

## 20.6 MLflow tracking server is hard-coded

The service contains:

```python
mlflow.set_tracking_uri(
    "http://localhost:5000"
)
```

This makes deployment environment-specific.

**Recommendation:** Use an environment variable:

```env
MLFLOW_TRACKING_URI=http://localhost:5000
```

and:

```python
mlflow.set_tracking_uri(
    os.getenv("MLFLOW_TRACKING_URI")
)
```

---

## 20.7 LLM configuration naming

The environment variable names:

```text
fallback_model_2
openrouter_api_key
base_url
```

are not strongly self-documenting.

**Recommendation:** Prefer names such as:

```env
LLM_MODEL=
OPENROUTER_API_KEY=
LLM_BASE_URL=
LLM_TEMPERATURE=0
```

---

## 20.8 Unused imports

`drug_impl.py` imports:

```python
from langchain_openai import ChatOpenAI
```

but uses:

```python
from app.config.llm_config import get_llm
```

The direct `ChatOpenAI` import is unnecessary.

Similarly, `get_retriever()` exists in `vector_store.py`, but the implementation constructs the retriever directly.

**Recommendation:** Remove unused imports and centralize retriever creation.

---

## 20.9 Embedding model initialized at module import

`vector_store.py` creates:

```python
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)
```

at module import time and then creates another embedding instance inside `load_vectorstore()`.

This can cause unnecessary initialization and resource usage.

**Recommendation:** Create the embedding object once through a factory or dependency/lifecycle mechanism.

---

## 20.10 `language` is not used

The request model supports:

```json
"language": "English"
```

but the prompt does not receive the requested language.

Therefore, changing the language field currently does not necessarily change the generated response language.

**Recommendation:** Add `{language}` to the prompt and pass it from the service/implementation layer.

---

## 20.11 `user_id` and `session_id` are not used

The request model defines:

```text
user_id
session_id
```

but these values are not currently used for:

- tracing,
- audit,
- personalization,
- conversation memory,
- access control,
- MLflow metadata.

If they are not required, remove them. If they are required, integrate them intentionally and securely.

---

## 20.12 No authentication/authorization

The current API does not implement authentication or authorization.

For a healthcare/clinical application, production deployment should consider:

```text
Authentication
Authorization / RBAC
Audit logging
Secrets management
Rate limiting
Input validation
Data protection
API security
```

---

## 20.13 No explicit medical safety guardrail

The prompt says:

```text
Do not hallucinate information.
```

That is useful but insufficient as a clinical safety mechanism.

A production medical assistant should add:

```text
Evidence validation
Source attribution
Clinical safety guardrails
Out-of-scope detection
Uncertainty handling
High-risk query escalation
Human/pharmacist review where appropriate
```

---

## 20.14 Knowledge-base source is not returned

The response contains:

```text
source = "Drug Knowledge Base"
```

but does not identify the actual document/chunk/source used for the answer.

For auditable RAG, consider returning structured citation metadata such as:

```json
{
  "source_documents": [
    {
      "document": "drugs.txt",
      "chunk_id": "...",
      "score": 0.87
    }
  ]
}
```

The exact design should avoid exposing sensitive internal information.

---

## 20.15 Retriever relevance is not evaluated

The application retrieves:

```text
k = 3
```

documents, but there is no explicit relevance threshold.

A query with poor retrieval quality may still be passed to the LLM.

**Recommendation:** Consider:

- similarity thresholding,
- reranking,
- query normalization,
- retrieval evaluation,
- "insufficient evidence" handling.

---

## 21. Recommended Production Architecture

For a more robust healthcare-grade implementation:

```text
Client
  │
  ▼
API Gateway
  │
  ├── Authentication
  ├── Authorization
  ├── Rate Limiting
  └── Audit
  │
  ▼
FastAPI Router
  │
  ▼
Service Layer
  │
  ├── Validation
  ├── Safety Policy
  ├── Observability
  └── Workflow
  │
  ▼
RAG Implementation
  │
  ├── Query Processing
  ├── Retriever
  ├── Reranker
  ├── Context Validation
  └── LLM
       │
       ▼
  Structured Output
       │
       ├── Schema Validation
       ├── Safety Validation
       ├── Citation Validation
       └── Confidence / Evidence Check
       │
       ▼
  Response
```

---

## 22. Recommended Enhancements

### Architecture

- Add dependency injection.
- Separate configuration from application code.
- Centralize vector-store initialization.
- Centralize logging configuration.
- Add repository/data-access abstraction.
- Add explicit RAG service.
- Add LLM factory.
- Add model configuration abstraction.

### RAG

- Add document metadata.
- Add source citations.
- Add similarity thresholds.
- Add reranking.
- Add retrieval evaluation.
- Version the knowledge base.
- Version embeddings/vector indexes.

### LLM

- Add configurable model.
- Add configurable temperature.
- Add timeout and retry policy.
- Add fallback model strategy.
- Add structured-output validation.
- Add prompt versioning.

### Observability

Track:

```text
request count
latency
retrieval latency
LLM latency
token usage
retrieval count
retrieval relevance
error rate
model name
prompt version
knowledge-base version
```

MLflow can be used together with application metrics and distributed tracing.

### Security

Add:

```text
API authentication
RBAC
secret management
audit trails
input sanitization
rate limiting
PII/PHI controls
secure logging
```

### Testing

Add:

```text
tests/
├── unit/
├── integration/
├── api/
├── rag/
├── evaluation/
└── safety/
```

---

## 23. Suggested Improved Project Structure

```text
drug-information-assistant/
│
├── app/
│   ├── main.py
│   │
│   ├── api/
│   │   └── routers/
│   │       └── drug_router.py
│   │
│   ├── config/
│   │   ├── settings.py
│   │   └── llm_config.py
│   │
│   ├── models/
│   │   ├── request_model.py
│   │   └── response_model.py
│   │
│   ├── services/
│   │   ├── drug_service.py
│   │   └── rag_service.py
│   │
│   ├── implementations/
│   │   └── drug_impl.py
│   │
│   ├── prompts/
│   │   └── drug_prompt.py
│   │
│   ├── retrieval/
│   │   ├── vector_store.py
│   │   ├── retriever.py
│   │   └── reranker.py
│   │
│   ├── guardrails/
│   │   ├── input_guardrail.py
│   │   ├── output_guardrail.py
│   │   └── clinical_guardrail.py
│   │
│   ├── observability/
│   │   ├── logging.py
│   │   ├── metrics.py
│   │   └── tracing.py
│   │
│   └── utils/
│
├── data/
│   └── drugs.txt
│
├── vector_db/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── api/
│   └── evaluation/
│
├── logs/
│
├── .env.example
├── .gitignore
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 24. End-to-End Execution Sequence

```text
1. Application starts
       ↓
2. FastAPI initializes
       ↓
3. DrugService is created
       ↓
4. DrugImplementation is created
       ↓
5. LLM configuration is loaded
       ↓
6. Chroma vector store is loaded/created
       ↓
7. /drug/information receives request
       ↓
8. DrugService validates input
       ↓
9. MLflow run starts
       ↓
10. Retriever searches drug knowledge base
       ↓
11. Top-k documents are returned
       ↓
12. Prompt is constructed
       ↓
13. LLM generates structured response
       ↓
14. Pydantic validates response
       ↓
15. MLflow records metrics
       ↓
16. FastAPI returns JSON
```

---

## 25. Security and Clinical Disclaimer

This implementation is suitable as a **technical RAG/LLM demonstration**.

Before using it in a real clinical or pharmacy environment, additional controls are required. In particular:

- Drug information must come from authoritative, current sources.
- Dosage information requires careful clinical governance.
- Patient-specific recommendations should not be generated without appropriate clinical context and safeguards.
- High-risk medication questions should be escalated appropriately.
- User and session identifiers should be protected.
- Secrets must not be stored in source code.
- Logs must be reviewed for sensitive data exposure.
- The system should provide traceable evidence for generated answers.
- Model outputs should be validated before being used operationally.

---

## 26. Summary

The uploaded project implements a clean initial pattern for a **FastAPI + LangChain + RAG + Chroma + LLM + MLflow** Drug Information Assistant.

The strongest architectural concept is the separation:

```text
Router
   ↓
Service
   ↓
Implementation
   ↓
Retriever + Prompt + LLM
```

The primary work required before the project is reproducible and production-ready is:

1. Add the missing `data/drugs.txt`.
2. Add a dependency manifest.
3. Add `.env.example`.
4. Correct the `DrugResponse`/`warnings` mismatch.
5. Correct MLflow response logging.
6. Externalize MLflow and LLM configuration.
7. Implement the currently unused language/session fields or remove them.
8. Centralize logging and embedding/vector-store initialization.
9. Add RAG citations and retrieval-quality controls.
10. Add authentication, authorization, auditability, and clinical safety guardrails.
11. Add automated unit, integration, RAG-evaluation, and API tests.
12. Add Docker/deployment configuration for reproducible execution.

This README documents the application based on the contents of the supplied ZIP archive.
