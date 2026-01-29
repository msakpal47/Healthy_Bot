from pathlib import Path
from src.config import DATA_DIR, INDEX_DIR, ensure_dirs, get_openai_api_key

try:
    from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
except Exception:
    from langchain.document_loaders import DirectoryLoader, PyPDFLoader

try:
    from langchain_text_splitters import CharacterTextSplitter
except ImportError:
    try:
        from langchain.text_splitter import CharacterTextSplitter
    except ImportError:
        CharacterTextSplitter = None
        print("Warning: Could not import CharacterTextSplitter")

try:
    from langchain_community.embeddings import HuggingFaceEmbeddings
except Exception:
    from langchain.embeddings import HuggingFaceEmbeddings

try:
    from langchain_community.vectorstores import FAISS
except Exception:
    from langchain.vectorstores import FAISS

def ingest_pdfs() -> None:
    ensure_dirs()
    print(f"Loading PDFs from {DATA_DIR.as_posix()}...")
    # Explicitly check for the requested file to confirm it exists
    target_file = DATA_DIR / "Disease_Medicine_500_Clean_Readable.pdf"
    if target_file.exists():
        print(f"Found target file: {target_file.name}")
    
    loader = DirectoryLoader(DATA_DIR.as_posix(), glob="**/*.pdf", loader_cls=PyPDFLoader, show_progress=True)
    documents = loader.load()
    print(f"Loaded {len(documents)} documents")
    if not documents:
        print("No documents found!")
        return
    splitter = CharacterTextSplitter(separator="\n", chunk_size=1000, chunk_overlap=200, length_function=len)
    texts = splitter.split_documents(documents)
    print(f"Split into {len(texts)} chunks")
    
    print("Using HuggingFaceEmbeddings (local) to avoid OpenAI quota limits...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    print("Creating vector store...")
    vectordb = FAISS.from_documents(texts, embeddings)
    vectordb.save_local(INDEX_DIR.as_posix())
    print(f"Index saved to {INDEX_DIR.as_posix()}")

def main() -> int:
    ingest_pdfs()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
