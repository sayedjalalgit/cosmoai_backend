import os
import json
import sys
sys.path.insert(0, '.')

print("🛸 COSMOAI Brain Builder")
print("=" * 40)

# Check documents folder
DOCUMENTS_DIR = "documents"
FAISS_STORE_DIR = "faiss_store"
GLOBAL_INDEX_PATH = os.path.join(FAISS_STORE_DIR, "global")
METADATA_PATH = os.path.join(FAISS_STORE_DIR, "global_meta.json")

os.makedirs(DOCUMENTS_DIR, exist_ok=True)
os.makedirs(FAISS_STORE_DIR, exist_ok=True)

# Get all files
files = [f for f in os.listdir(DOCUMENTS_DIR)
         if f.endswith('.pdf') or f.endswith('.txt')]

if not files:
    print(f"❌ No PDF or TXT files found in {DOCUMENTS_DIR}/")
    print("Add files to documents/ folder and run again.")
    sys.exit(0)

print(f"📂 Found {len(files)} files: {', '.join(files)}")
print()

# Load dependencies
print("Loading AI components...")
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100
)

all_chunks = []
metadata_store = []
total_chunks = 0

for filename in files:
    filepath = os.path.join(DOCUMENTS_DIR, filename)
    print(f"Processing {filename}...")

    try:
        if filename.endswith('.pdf'):
            # Try PyPDF first
            loader = PyPDFLoader(filepath)
            docs = loader.load()
            full_text = "\n".join([
                d.page_content for d in docs
                if d.page_content.strip()
            ])

            # If PDF is scanned/empty try OCR
            if not full_text or len(full_text.strip()) < 50:
                print(f"  ⚠️ PDF appears to be scanned. Trying OCR...")
                try:
                    import pytesseract
                    from pdf2image import convert_from_path
                    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
                    pages = convert_from_path(filepath, dpi=200,
                        poppler_path=r'C:\poppler\Library\bin')
                    ocr_texts = []
                    for page in pages:
                        text = pytesseract.image_to_string(page, lang='eng')
                        if text.strip():
                            ocr_texts.append(text)
                    full_text = "\n".join(ocr_texts)
                except Exception as ocr_err:
                    print(f"  ⚠️ OCR failed: {ocr_err}")
                    full_text = f"Document: {filename}"

        elif filename.endswith('.txt'):
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                full_text = f.read()

        if not full_text or len(full_text.strip()) < 10:
            print(f"  ⚠️ Could not extract text from {filename}")
            continue

        # Split into chunks
        chunks = splitter.create_documents(
            [full_text],
            metadatas=[{
                "source": filename,
                "type": "global"
            }]
        )

        print(f"  ✅ {len(chunks)} chunks created")
        all_chunks.extend(chunks)

        # Store metadata
        for i, chunk in enumerate(chunks):
            metadata_store.append({
                "source": filename,
                "chunk_id": total_chunks + i,
                "text": chunk.page_content[:200],
                "type": "global"
            })

        total_chunks += len(chunks)

    except Exception as e:
        print(f"  ❌ Error processing {filename}: {e}")
        continue

print()

if not all_chunks:
    print("❌ No chunks created. Check your documents.")
    sys.exit(0)

# Build FAISS index
print(f"Building FAISS index from {total_chunks} chunks...")
db = FAISS.from_documents(all_chunks, embeddings)
db.save_local(GLOBAL_INDEX_PATH)

# Save metadata
with open(METADATA_PATH, 'w', encoding='utf-8') as f:
    json.dump(metadata_store, f, ensure_ascii=False, indent=2)

print()
print("=" * 40)
print(f"✅ Brain built successfully!")
print(f"   Files processed: {len(files)}")
print(f"   Total chunks: {total_chunks}")
print(f"   Index saved: {GLOBAL_INDEX_PATH}")
print()
print("Restart backend to load new knowledge:")
print("   python run.py")