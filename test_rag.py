import sys
sys.path.append('.')

print("Testing imports...")

try:
    from langchain_community.document_loaders import PyPDFLoader
    print("✅ PyPDFLoader OK")
except Exception as e:
    print(f"❌ PyPDFLoader: {e}")

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    print("✅ TextSplitter OK")
except Exception as e:
    print(f"❌ TextSplitter: {e}")

try:
    from langchain_community.embeddings import HuggingFaceEmbeddings
    print("✅ HuggingFaceEmbeddings OK")
except Exception as e:
    print(f"❌ HuggingFaceEmbeddings: {e}")

try:
    from langchain_community.vectorstores import FAISS
    print("✅ FAISS OK")
except Exception as e:
    print(f"❌ FAISS: {e}")

print("\nAll tests done!")
