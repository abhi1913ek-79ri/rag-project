# RAGLens

RAGLens is a document-grounded workspace for asking questions, retrieving evidence, and inspecting claim verification results. The frontend is a Next.js App Router application using JavaScript, JSX, Tailwind CSS, and Lucide React. The existing FastAPI service remains responsible for PDF validation, extraction, retrieval, generation, citations, and auditing.

## Architecture

```text
Browser -> Next.js app and route handlers (port 3000) -> FastAPI RAG service (port 8000)
                                                        -> local PDF metadata, chunks, embeddings, Gemini
```

## Setup

### 1. Configure the RAG service

From `rag-services`:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# Set GEMINI_API_KEY in .env; never put it in client files.
uvicorn main:app --reload --port 8000
```

### 2. Install and start RAGLens

From `client`:

```powershell
npm install
Copy-Item .env.example .env.local
npm run dev
```

Open <http://127.0.0.1:3000>. The Next.js route handler proxies `/api/upload`, `/api/documents`, and `/api/audit` to FastAPI using the server-only `RAG_SERVICE_URL` setting.

## Validation

```powershell
Set-Location client
npm run build

Set-Location ..\rag-services
python -m compileall -q main.py services
```

The existing `test_*.py` files are executable experiments rather than pytest-collected tests. They may invoke the embedding model or Gemini and should be run only with the Python environment and credentials configured.

## Current limitations

- Document metadata and the processed-document cache are local to the Python process and are not persistent across restarts.
- There is no authentication or multi-user authorization layer yet. Deploy behind an authenticated trusted boundary before exposing it beyond a local/demo environment.
- Only PDF uploads are supported, with the FastAPI service enforcing a 10 MB limit.
