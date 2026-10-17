from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from pathlib import Path

from services.rag_pipeline import run_rag_query

app = FastAPI(
    title="Document Intelligence RAG API",
    description="RAG with verifiable source citations",
    version="1.0.0"
)

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "documents" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# Request body schema
class AuditRequest(BaseModel):
    query: str
    pdf_path: str = "documents/sample.pdf"


# Health check endpoint
@app.get("/")
def home():
    return {
        "message": "RAG Service is running"
    }


# RAG audit endpoint
@app.post("/audit")
def audit_document(request: AuditRequest):
    try:
        if not request.query.strip():
            raise HTTPException(
                status_code=400,
                detail="Query cannot be empty."
            )

        result = run_rag_query(
            query=request.query,
            pdf_path=request.pdf_path
        )

        return result

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"RAG processing failed: {str(error)}"
        )

# upload file endpoint
@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):

    # Step 1: Check file extension
    if Path(file.filename or "").suffix.lower() != ".pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed."
        )

    # Step 2: Generate a safe, unique filename
    import uuid

    filename = f"{uuid.uuid4().hex}.pdf"

    file_path = UPLOAD_DIR / filename

    # Step 3: Save the uploaded file
    try:
        with file_path.open("wb") as destination:
            while chunk := await file.read(1024 * 1024):
                destination.write(chunk)

    except Exception:
        file_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=500,
            detail="Failed to save the uploaded file."
        )

    finally:
        await file.close()

    # Step 4: Return document information
    return {
        "message": "PDF uploaded successfully.",
        "filename": filename,
        "pdf_path": str(file_path)
    }