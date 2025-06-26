#!/usr/bin/env python3

"""
Debug script to test imports and dependencies
Run this inside the Docker container to verify all modules can be imported
"""

import sys
import traceback

def test_import(module_name, package_name=None):
    """Test importing a module and report results"""
    try:
        __import__(module_name)
        print(f"✅ {module_name}: OK")
        return True
    except ImportError as e:
        package_info = f" (from {package_name})" if package_name else ""
        print(f"❌ {module_name}{package_info}: FAILED - {e}")
        return False
    except Exception as e:
        print(f"⚠️ {module_name}: ERROR - {e}")
        return False

def main():
    print("🔍 Testing Python imports for multimodal RAG system...")
    print(f"🐍 Python version: {sys.version}")
    print(f"📁 Python path: {sys.path[:3]}...")  # Show first 3 entries
    print()
    
    # Test core dependencies
    print("📦 Core dependencies:")
    success = True
    success &= test_import("faiss", "faiss-cpu")
    success &= test_import("numpy")
    success &= test_import("sklearn", "scikit-learn")
    success &= test_import("PIL", "pillow")
    success &= test_import("pandas")
    print()
    
    # Test AI/ML dependencies
    print("🤖 AI/ML dependencies:")
    success &= test_import("cohere")
    success &= test_import("google.generativeai")
    print()
    
    # Test PDF processing
    print("📄 PDF processing:")
    success &= test_import("pdf2image")
    success &= test_import("PyPDF2")
    print()
    
    # Test web framework dependencies
    print("🌐 Web framework:")
    success &= test_import("fastapi")
    success &= test_import("uvicorn")
    success &= test_import("streamlit")
    print()
    
    # Test application modules
    print("🏗️ Application modules:")
    try:
        import core.document_utils
        print("✅ core.document_utils: OK")
    except Exception as e:
        print(f"❌ core.document_utils: FAILED - {e}")
        success = False
        
    try:
        import core.embeddings
        print("✅ core.embeddings: OK")
    except Exception as e:
        print(f"❌ core.embeddings: FAILED - {e}")
        success = False
        
    try:
        import core.search
        print("✅ core.search: OK")
    except Exception as e:
        print(f"❌ core.search: FAILED - {e}")
        success = False
    
    print()
    if success:
        print("🎉 All imports successful!")
        return 0
    else:
        print("💥 Some imports failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
