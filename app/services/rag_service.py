import os
import json
from typing import Optional
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

FAISS_DIR = "faiss_indexes"
GLOBAL_INDEX_PATH = "faiss_store/global"

os.makedirs(FAISS_DIR, exist_ok=True)
os.makedirs("faiss_store", exist_ok=True)

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Load global index on startup
global_db = None

def load_global_index():
    global global_db
    if os.path.exists(GLOBAL_INDEX_PATH):
        try:
            global_db = FAISS.load_local(
                GLOBAL_INDEX_PATH,
                embeddings,
                allow_dangerous_deserialization=True
            )
            print(f"✅ Global brain loaded from {GLOBAL_INDEX_PATH}")
        except Exception as e:
            print(f"⚠️ Could not load global brain: {e}")
            global_db = None
    else:
        print("ℹ️ No global brain found. Run brain.py to build one.")
        global_db = None

# Load on import
load_global_index()

def get_user_index_path(user_id: str) -> str:
    return os.path.join(FAISS_DIR, f"user_{user_id}")

def extract_text_from_pdf(file_path: str) -> str:
    try:
        loader = PyPDFLoader(file_path)
        docs = loader.load()
        full_text = "\n".join([
            d.page_content for d in docs
            if d.page_content.strip()
        ])
        if full_text and len(full_text.strip()) > 50:
            return full_text
    except Exception as e:
        print(f"PyPDF error: {e}")

    # Try OCR for scanned PDFs
    print("Trying OCR...")
    try:
        import pytesseract
        from pdf2image import convert_from_path
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        pages = convert_from_path(file_path, dpi=200,
            poppler_path=r'C:\poppler\Library\bin')
        texts = []
        for page in pages:
            text = pytesseract.image_to_string(page, lang='eng')
            if text.strip():
                texts.append(text)
        full_text = "\n".join(texts)
        if full_text.strip():
            return full_text
    except Exception as e:
        print(f"OCR error: {e}")

    return ""

def process_pdf(file_path: str, user_id: str) -> int:
    print(f"Processing: {file_path}")

    full_text = extract_text_from_pdf(file_path)

    if not full_text or len(full_text.strip()) < 50:
        print("Using fallback text")
        filename = os.path.basename(file_path)
        full_text = f"Document uploaded: {filename}"

    print(f"Extracted {len(full_text)} characters")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=50
    )
    chunks = splitter.create_documents(
        [full_text],
        metadatas=[{"source": os.path.basename(file_path), "type": "user"}]
    )

    if not chunks:
        chunks = [Document(page_content=full_text)]

    print(f"Created {len(chunks)} chunks")

    index_path = get_user_index_path(user_id)

    if os.path.exists(index_path):
        try:
            db = FAISS.load_local(
                index_path,
                embeddings,
                allow_dangerous_deserialization=True
            )
            db.add_documents(chunks)
        except Exception:
            db = FAISS.from_documents(chunks, embeddings)
    else:
        db = FAISS.from_documents(chunks, embeddings)

    db.save_local(index_path)
    return len(chunks)

def process_text(text: str, user_id: str) -> int:
    if not text or len(text.strip()) < 10:
        return 0

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=50
    )
    chunks = splitter.create_documents([text])

    if not chunks:
        return 0

    index_path = get_user_index_path(user_id)

    if os.path.exists(index_path):
        try:
            db = FAISS.load_local(
                index_path,
                embeddings,
                allow_dangerous_deserialization=True
            )
            db.add_documents(chunks)
        except Exception:
            db = FAISS.from_documents(chunks, embeddings)
    else:
        db = FAISS.from_documents(chunks, embeddings)

    db.save_local(index_path)
    return len(chunks)

def search_documents(user_id: str, query: str, k: int = 3) -> Optional[str]:
    results = []

    # Search global brain first
    if global_db is not None:
        try:
            global_results = global_db.similarity_search(query, k=k)
            for r in global_results:
                source = r.metadata.get("source", "knowledge base")
                results.append(f"[From {source}]: {r.page_content}")
        except Exception as e:
            print(f"Global search error: {e}")

    # Search user index
    index_path = get_user_index_path(user_id)
    if os.path.exists(index_path):
        try:
            user_db = FAISS.load_local(
                index_path,
                embeddings,
                allow_dangerous_deserialization=True
            )
            user_results = user_db.similarity_search(query, k=k)
            for r in user_results:
                source = r.metadata.get("source", "your document")
                results.append(f"[From {source}]: {r.page_content}")
        except Exception as e:
            print(f"User search error: {e}")

    if not results:
        return None

    return "\n\n".join(results[:k * 2])

def delete_user_index(user_id: str):
    index_path = get_user_index_path(user_id)
    if os.path.exists(index_path):
        import shutil
        shutil.rmtree(index_path)

def reload_global_index():
    """Call this after running brain.py to reload without restart"""
    load_global_index()
    return global_db is not None
