from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from pathlib import Path
import hashlib
import json
import pymupdf

from services.rag_pipeline import run_rag_query,document_cache

app = FastAPI(
    title="Document Intelligence RAG API",
    description="RAG with verifiable source citations",
    version="1.0.0"
)

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "documents" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

METADATA_FILE = BASE_DIR / "documents" / "document_metadata.json"
METADATA_FILE.parent.mkdir(parents=True, exist_ok=True)
if not METADATA_FILE.exists():
    METADATA_FILE.write_text("{}", encoding="utf-8")


def get_pdf_path_by_id(document_id: str) -> Path:
    if not document_id or len(document_id) != 64:
        raise HTTPException(
            status_code=400,
            detail="Invalid document ID."
        )

    try:
        with METADATA_FILE.open("r", encoding="utf-8") as file:
            metadata = json.load(file)

    except (OSError, json.JSONDecodeError):
        raise HTTPException(
            status_code=500,
            detail="Could not read document metadata."
        )

    document = metadata.get(document_id)

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found."
        )

    pdf_path = Path(document["pdf_path"]).resolve()

    # Ensure the file belongs to the upload directory
    if not pdf_path.is_relative_to(UPLOAD_DIR.resolve()):
        raise HTTPException(
            status_code=400,
            detail="Invalid document path."
        )

    if not pdf_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="PDF file not found."
        )

    return pdf_path

def save_document_metadata(
    document_id: str,
    filename: str,
    file_path: Path
):
    with METADATA_FILE.open("r", encoding="utf-8") as file:
        metadata = json.load(file)

    metadata[document_id] = {
        "document_id": document_id,
        "filename": filename,
        "pdf_path": str(file_path.resolve())
    }

    temp_file = METADATA_FILE.with_suffix(".tmp")

    try:
        with temp_file.open("w", encoding="utf-8") as file:
            json.dump(metadata, file, indent=4)

        temp_file.replace(METADATA_FILE)

    finally:
        temp_file.unlink(missing_ok=True)
# Request body schema
class AuditRequest(BaseModel):
    query: str
    document_id: str


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

        # Resolve document ID to its stored PDF
        pdf_path = get_pdf_path_by_id(
            request.document_id
        )

        # Run the existing RAG pipeline
        result = run_rag_query(
            query=request.query,
            pdf_path=str(pdf_path)
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

    # Step 3: Save the uploaded file with a size limit
    total_size = 0

    try:
        with file_path.open("wb") as destination:
            while chunk := await file.read(1024 * 1024):

                total_size += len(chunk)

                if total_size > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail="File too large. Maximum allowed size is 10 MB."
                    )

                destination.write(chunk)

    except HTTPException:
        file_path.unlink(missing_ok=True)
        raise

    except Exception:
        file_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=500,
            detail="Failed to save the uploaded file."
        )

    finally:
        await file.close()
    # Step 4: Validate the actual PDF file
    try:
        with pymupdf.open(file_path) as document:

            if document.is_encrypted:
                raise HTTPException(
                    status_code=400,
                    detail="Encrypted PDFs are not supported."
                )

            if len(document) == 0:
                raise HTTPException(
                    status_code=400,
                    detail="PDF must contain at least one page."
                )

    except HTTPException:
        file_path.unlink(missing_ok=True)
        raise

    except Exception as error:
        print(f"PDF validation failed: {type(error).__name__}: {error}")

        file_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=400,
            detail="Invalid or corrupted PDF file."
        )
    # Generate a stable document ID from the saved PDF
    sha256 = hashlib.sha256()

    with file_path.open("rb") as uploaded_file:
        for chunk in iter(
            lambda: uploaded_file.read(1024 * 1024),
            b""
        ):
            sha256.update(chunk)

    document_id = sha256.hexdigest()

    # Check whether the document already exists
    try:
        with METADATA_FILE.open("r", encoding="utf-8") as file:
            metadata = json.load(file)

    except (OSError, json.JSONDecodeError):
        file_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=500,
            detail="Could not read document metadata."
        )

    if document_id in metadata:
        existing_document = metadata[document_id]

        # Remove the newly uploaded duplicate copy
        file_path.unlink(missing_ok=True)

        return {
            "message": "Document already exists. Existing document reused.",
            "document_id": document_id,
            "filename": existing_document["filename"],
            "pdf_path": existing_document["pdf_path"],
            "duplicate": True
        }

    # save doc meta data
    save_document_metadata(
        document_id=document_id,
        filename=filename,
        file_path=file_path
    )
    # Step 4: Return document information
    return {
        "message": "PDF uploaded successfully.",
        "document_id": document_id,
        "filename": filename,
        "pdf_path": str(file_path)
    }

@app.get("/documents/{document_id}")
def get_document(document_id: str):
    pdf_path = get_pdf_path_by_id(document_id)

    return {
        "message": "Document found.",
        "filename": pdf_path.name
    }

# Get all uploaded documents
@app.get("/documents")
def get_all_documents():
    try:
        with METADATA_FILE.open("r", encoding="utf-8") as file:
            metadata = json.load(file)

        documents = []

        for document_id, document in metadata.items():
            pdf_path = Path(document["pdf_path"])

            # Include only documents whose files still exist
            if pdf_path.is_file():
                documents.append({
                    "document_id": document_id,
                    "filename": document["filename"],
                    "pdf_path": str(pdf_path)
                })

        return {
            "total_documents": len(documents),
            "documents": documents
        }

    except (OSError, json.JSONDecodeError):
        raise HTTPException(
            status_code=500,
            detail="Could not read document metadata."
        )


# Delete an uploaded document
@app.delete("/documents/{document_id}")
def delete_document(document_id: str):

    # Step 1: Find the PDF using document ID
    pdf_path = get_pdf_path_by_id(document_id)

    # Step 2: Read existing metadata
    try:
        with METADATA_FILE.open("r", encoding="utf-8") as file:
            metadata = json.load(file)

    except (OSError, json.JSONDecodeError):
        raise HTTPException(
            status_code=500,
            detail="Could not read document metadata."
        )

    # Step 3: Remove the document metadata
    metadata.pop(document_id, None)

    # Step 4: Save updated metadata
    try:
        with METADATA_FILE.open("w", encoding="utf-8") as file:
            json.dump(metadata, file, indent=4)

    except OSError:
        raise HTTPException(
            status_code=500,
            detail="Could not update document metadata."
        )

    # Step 5: Delete the PDF file
    try:
        pdf_path.unlink()

    except OSError:
        raise HTTPException(
            status_code=500,
            detail="Metadata deleted, but PDF file could not be deleted."
        )

    # Step 6: Remove cached chunks and embeddings
    document_cache.pop(document_id, None)

    return {
        "message": "Document deleted successfully.",
        "document_id": document_id,
        "filename": pdf_path.name
    }