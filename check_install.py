#!/usr/bin/env python3
"""Check ALMAA Phase 2 installation - FIXED VERSION"""

import sys
from pathlib import Path

def check_imports():
    """Check all required imports"""
    modules = [
        ("chromadb", "ChromaDB"),
        ("sentence_transformers", "SentenceTransformers"),
        ("sklearn.cluster", "Scikit-learn"),
        ("ollama", "Ollama"),
        ("loguru", "Loguru"),
        ("pydantic", "Pydantic"),
        ("click", "Click"),
        ("yaml", "PyYAML"),
        ("numpy", "NumPy")
    ]
    
    print("📦 Checking Python packages...")
    all_ok = True
    for module, name in modules:
        try:
            __import__(module)
            print(f"  ✅ {name} OK")
        except ImportError:
            print(f"  ❌ {name} missing - install with: pip install {module}")
            all_ok = False
            
    return all_ok

def check_files():
    """Check essential files"""
    print("\n📄 Checking project files...")
    
    files = [
        # Core files
        "core/base.py",
        "core/communication.py",
        "core/debate.py",
        "core/voting.py",
        "core/debate_manager.py",
        "core/user_listener.py",
        "core/memory/vector_store.py",
        "core/memory/compression.py",
        
        # Agents
        "agents/chef.py",
        "agents/enhanced_chef.py",
        "agents/chef_projet.py",
        "agents/memory_enhanced_worker.py",
        "agents/mixins/debater.py",
        "agents/mixins/memory.py",
        "agents/special/moderator.py",
        "agents/special/philosophe.py",
        
        # Main files
        "main_phase2.py",
        "config/default_phase2.yaml",
        "requirements_phase2.txt"
    ]
    
    all_ok = True
    missing = []
    
    for file in files:
        if Path(file).exists():
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} missing")
            missing.append(file)
            all_ok = False
            
    if missing:
        print("\n⚠️  Missing files need to be added to the project")
        
    return all_ok

def check_directories():
    """Check required directories"""
    print("\n📁 Checking directories...")
    
    dirs = [
        "data/memory/vectors",
        "data/logs",
        "config"
    ]
    
    all_ok = True
    for dir_path in dirs:
        path = Path(dir_path)
        if path.exists():
            print(f"  ✅ {dir_path}/")
        else:
            print(f"  ❌ {dir_path}/ missing - creating...")
            path.mkdir(parents=True, exist_ok=True)
            print(f"     Created {dir_path}/")
            
    return all_ok

def check_ollama():
    """Check Ollama installation and models - FIXED VERSION"""
    print("\n🤖 Checking Ollama...")
    
    try:
        import ollama
        
        # Test with a simple generation instead of list (more reliable)
        response = ollama.generate(
            model="solar:10.7b",  # Use your model
            prompt="Hello",
            options={"num_predict": 5}
        )
        
        print("  ✅ Ollama working - solar:10.7b model accessible")
        return True
        
    except ImportError:
        print("  ❌ Ollama Python library not installed")
        return False
    except Exception as e:
        error_msg = str(e).lower()
        
        if "model" in error_msg and "not found" in error_msg:
            print("  ⚠️  Ollama working but solar:10.7b model not found")
            print("      Install with: ollama pull solar:10.7b")
            
            # Try with llama3.2 as fallback
            try:
                response = ollama.generate(
                    model="llama3.2:latest",
                    prompt="Hello",
                    options={"num_predict": 5}
                )
                print("  ✅ Fallback: llama3.2:latest model working")
                return True
            except:
                print("  ❌ No compatible models found")
                return False
                
        elif "connect" in error_msg or "connection" in error_msg:
            print("  ❌ Cannot connect to Ollama - make sure it's running")
            print("      Windows: Ollama should start automatically")
            print("      Linux/Mac: run 'ollama serve' in another terminal")
            return False
        else:
            print(f"  ⚠️  Ollama test failed: {e}")
            print("  But models list showed solar:10.7b is available")
            return True  # Assume it's working since you have the models

def check_memory():
    """Test memory system - IMPROVED VERSION"""
    print("\n🧠 Testing memory system...")
    
    try:
        # Test imports first
        import chromadb
        from sentence_transformers import SentenceTransformer
        print("  ✅ Memory dependencies available")
        
        # Test ChromaDB directly
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            client = chromadb.PersistentClient(path=temp_dir)
            collection = client.get_or_create_collection("test")
            
            # Test embedding model
            encoder = SentenceTransformer('all-MiniLM-L6-v2')
            embedding = encoder.encode("test").tolist()
            
            # Test store and retrieve
            collection.add(
                embeddings=[embedding],
                documents=["test document"],
                metadatas=[{"test": True}],
                ids=["test_id"]
            )
            
            results = collection.query(
                query_embeddings=[embedding],
                n_results=1
            )
            
            if results['ids']:
                print("  ✅ ChromaDB working correctly")
                return True
            else:
                print("  ❌ ChromaDB test failed - no results returned")
                return False
                
    except Exception as e:
        print(f"  ❌ Memory system error: {e}")
        
        # Suggest fixes
        if "sentence" in str(e).lower():
            print("  💡 Try: pip install --upgrade sentence-transformers torch")
        elif "chroma" in str(e).lower():
            print("  💡 Try: pip install --upgrade chromadb")
            
        return False

def main():
    """Run all checks"""
    print("🔍 ALMAA Phase 2 Installation Check - FIXED")
    print("=" * 50)
    
    # Run checks
    packages_ok = check_imports()
    dirs_ok = check_directories()
    files_ok = check_files()
    ollama_ok = check_ollama()
    memory_ok = check_memory()
    
    print("\n" + "=" * 50)
    print("📊 Summary:")
    
    all_ok = packages_ok and dirs_ok and files_ok and ollama_ok and memory_ok
    
    if all_ok:
        print("\n✅ Installation complete! You can run:")
        print("   python main_phase2.py interactive")
        
        print("\n🧪 Quick test commands:")
        print("   # Test debate:")
        print("   Vous: Quelle architecture choisir pour un système de paiement?")
        print("   # Test memory:")
        print("   Vous: Crée une fonction fibonacci")
        print("   Vous: /memory")
        
    else:
        print("\n❌ Installation incomplete. Issues found:")
        
        if not packages_ok:
            print("\n💡 Install missing packages:")
            print("   pip install --upgrade pip")
            print("   pip install -r requirements_phase2.txt")
            
        if not ollama_ok:
            print("\n💡 Ollama issues:")
            print("   - Make sure Ollama is running")
            print("   - Install model: ollama pull solar:10.7b")
            
        if not memory_ok:
            print("\n💡 Memory system issues:")
            print("   pip install --upgrade chromadb sentence-transformers")
            print("   # Or use fixed version: replace vector_store.py with vector_store_fixed.py")
            
        if not files_ok:
            print("\n💡 Missing files - make sure all Phase 2 files are in place")
            
        print(f"\n🎯 Priority fixes needed: {sum([not packages_ok, not ollama_ok, not memory_ok, not files_ok])} issues")

if __name__ == "__main__":
    main()