from pathlib import Path
import os
try:
    from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
except Exception:
    from langchain.document_loaders import DirectoryLoader, PyPDFLoader
try:
    from langchain_text_splitters import CharacterTextSplitter
except Exception:
    from langchain.text_splitter import CharacterTextSplitter
try:
    from langchain_community.embeddings import HuggingFaceEmbeddings
except Exception:
    from langchain.embeddings import HuggingFaceEmbeddings
try:
    from langchain_community.vectorstores import FAISS
except Exception:
    from langchain.vectorstores import FAISS
try:
    from langchain_core.documents import Document
except Exception:
    try:
        from langchain.schema import Document
    except Exception:
        Document = None
try:
    from langchain_openai import ChatOpenAI
except Exception:
    ChatOpenAI = None
try:
    from langchain.chains import ConversationalRetrievalChain
except Exception:
    ConversationalRetrievalChain = None

class SimpleQA:
    def __init__(self, db, llm=None):
        self.db = db
        self.llm = llm
        self.chain = None
        if self.llm and ConversationalRetrievalChain:
            self.chain = ConversationalRetrievalChain.from_llm(self.llm, self.db.as_retriever())

    def invoke(self, payload):
        q = payload.get("question", "")
        hist = payload.get("chat_history", [])
        if self.chain:
            res = self.chain.invoke({"question": q, "chat_history": hist})
            return res["answer"]
        docs = self.db.similarity_search(q, k=3)
        joined = "\n\n".join(d.page_content[:800] for d in docs)
        return (
            "Doctor-Patient Conversation\n"
            "Questions: symptoms, duration, severity, red flags\n"
            "Advice: hydration, rest, monitoring\n"
            "Medicines: from guidelines if appropriate\n\n"
            f"Context:\n{joined}"
        )

def get_llm(data_path: str):
    p = Path(data_path)
    loader = DirectoryLoader(p.as_posix(), glob="**/*.pdf", loader_cls=PyPDFLoader, show_progress=True)
    try:
        docs = loader.load()
    except Exception:
        docs = []
    splitter = CharacterTextSplitter(separator="\n", chunk_size=1000, chunk_overlap=200, length_function=len)
    texts = splitter.split_documents(docs) if docs else []
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    if texts:
        db = FAISS.from_documents(texts, embeddings)
    else:
        seed_texts = ["General health guidance based on symptoms and severity."]
        db = FAISS.from_texts(seed_texts, embeddings)
    key = os.getenv("OPENAI_API_KEY", "")
    llm = ChatOpenAI(api_key=key, temperature=0) if (key and ChatOpenAI) else None
    return SimpleQA(db, llm)
