import os
from typing import Optional
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

FAISS_DIR = "faiss_indexes"
os.makedirs(FAISS_DIR, exist_ok=True)

embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2"
)

def get_user_index_path(user_id: str) -> str:
    return os.path.join(FAISS_DIR, f"user_{user_id}")

def extract_text_from_pdf(file_path: str) -> str:
    try:
        loader = PyPDFLoader(file_path)
        docs = loader.load()
        full_text = "\n".join([d.page_content for d in docs if d.page_content.strip()])
        return full_text
    except Exception as e:
        print(f"PyPDF error: {e}")
        return ""

def process_pdf(file_path: str, user_id: str) -> int:
    print(f"Processing: {file_path}")

    # Extract text
    full_text = extract_text_from_pdf(file_path)

    # If PDF extraction fails use filename as fallback
    if not full_text or len(full_text.strip()) < 50:
        print("PDF text extraction failed or too short, using fallback")
        filename = os.path.basename(file_path)
        full_text = f"Document uploaded: {filename}. Content could not be fully extracted."

    print(f"Extracted {len(full_text)} characters")

    # Split into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=50
    )

    # Create document objects
    chunks = splitter.create_documents([full_text])

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
    print(f"Saved to {index_path}")
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
    index_path = get_user_index_path(user_id)

    if not os.path.exists(index_path):
        return None

    try:
        db = FAISS.load_local(
            index_path,
            embeddings,
            allow_dangerous_deserialization=True
        )
        results = db.similarity_search(query, k=k)
        if not results:
            return None
        context = "\n\n".join([r.page_content for r in results])
        return context
    except Exception as e:
        print(f"Search error: {e}")
        return None

def delete_user_index(user_id: str):
    index_path = get_user_index_path(user_id)
    if os.path.exists(index_path):
        import shutil
        shutil.rmtree(index_path)