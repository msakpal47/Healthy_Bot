from pathlib import Path
from typing import List, Tuple
from src.config import INDEX_DIR, get_openai_api_key

try:
    from langchain.chains import ConversationalRetrievalChain
except Exception:
    ConversationalRetrievalChain = None

try:
    from langchain_community.embeddings import HuggingFaceEmbeddings
except Exception:
    from langchain.embeddings import HuggingFaceEmbeddings

try:
    from langchain_openai import ChatOpenAI, OpenAI
except Exception:
    ChatOpenAI = None
    OpenAI = None

try:
    from langchain_community.vectorstores import FAISS
except Exception:
    from langchain.vectorstores import FAISS

_embeddings = None
_db = None
def load_db():
    global _embeddings, _db
    index_file = INDEX_DIR / "index.faiss"
    if not INDEX_DIR.exists() or not index_file.exists():
        raise ValueError(f"Vector index not found at {INDEX_DIR}. The ingestion step failed or hasn't been run yet. Please check your API key and run 'python main.py ingest'.")
    if _embeddings is None:
        # Use the same local embeddings as ingestion
        _embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    if _db is None:
        try:
            _db = FAISS.load_local(INDEX_DIR.as_posix(), _embeddings, allow_dangerous_deserialization=True)
        except Exception as e:
            raise ValueError(f"Failed to load vector store: {e}")
    return _db

_llm = None
def ask(question: str, chat_history: List[Tuple[str, str]] | None = None) -> str:
    db = load_db()
    global _llm
    try:
        if _llm is None and ChatOpenAI is not None and get_openai_api_key():
            _llm = ChatOpenAI(api_key=get_openai_api_key(), temperature=0)
        elif _llm is None and OpenAI is not None and get_openai_api_key():
            _llm = OpenAI(api_key=get_openai_api_key(), temperature=0)
        if _llm is not None and ConversationalRetrievalChain is not None:
            chain = ConversationalRetrievalChain.from_llm(_llm, db.as_retriever())
            res = chain.invoke({"question": question, "chat_history": chat_history or []})
            return res["answer"]
    except Exception:
        pass
    docs = db.similarity_search(question, k=3)
    return "\n\n".join(d.page_content[:500] for d in docs)
