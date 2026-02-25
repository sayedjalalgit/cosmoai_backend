import sys
sys.path.append('.')

from app.services.rag_service import process_pdf, search_documents
import os

UPLOADS_DIR = r"E:\project_management\COSMOAI\project_management_web\cosmoai-backend\uploads"

print("Testing RAG pipeline...")
print(f"Looking in: {UPLOADS_DIR}")

files = os.listdir(UPLOADS_DIR)
print(f"Files found: {files}")

if not files:
    print("❌ No files in uploads folder")
else:
    full_path = os.path.join(UPLOADS_DIR, files[0])
    print(f"Testing with: {full_path}")

    try:
        print("Processing PDF...")
        chunks = process_pdf(full_path, "test_user_123")
        print(f"✅ Processed! {chunks} chunks created")

        print("Testing search...")
        result = search_documents("test_user_123", "skills")
        if result:
            print(f"✅ Search working!")
            print(result[:300])
        else:
            print("❌ Search returned nothing")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
