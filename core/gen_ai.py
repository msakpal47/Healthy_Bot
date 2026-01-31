from pathlib import Path
import os
print("Importing pypdf...")
import pypdf

print("Importing langchain components...")
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
        class Document:
            def __init__(self, page_content, metadata=None):
                self.page_content = page_content
                self.metadata = metadata or {}

try:
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
except Exception:
    ChatOpenAI = None
    OpenAIEmbeddings = None
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
            try:
                res = self.chain.invoke({"question": q, "chat_history": hist})
                return res["answer"]
            except Exception as e:
                print(f"LLM chain failed: {e}")
        
        docs = self.db.similarity_search(q, k=3)
        joined = "\n\n".join(d.page_content[:800] for d in docs)
        return (
            "Doctor-Patient Conversation\n"
            "Questions: symptoms, duration, severity, red flags\n"
            "Advice: hydration, rest, monitoring\n"
            "Medicines: from guidelines if appropriate\n\n"
            f"Context:\n{joined}"
        )

def load_pdfs(path: Path):
    docs = []
    if not path.exists():
        return docs
    for f in path.glob("**/*.pdf"):
        try:
            reader = pypdf.PdfReader(str(f))
            text = ""
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
            if text.strip():
                docs.append(Document(page_content=text, metadata={"source": str(f)}))
        except Exception as e:
            print(f"Error reading {f}: {e}")
    return docs

def get_llm(data_path: str):
    p = Path(data_path)
    
    key = os.getenv("OPENAI_API_KEY", "")
    
    embeddings = None
    if key and OpenAIEmbeddings:
        try:
            print("Initializing OpenAI Embeddings...")
            temp_embeddings = OpenAIEmbeddings(api_key=key)
            # Test call to verify key
            temp_embeddings.embed_query("test")
            embeddings = temp_embeddings
            print("OpenAI Embeddings initialized successfully.")
        except Exception as e:
            print(f"OpenAI Embeddings failed: {e}. Falling back to HuggingFace.")
            embeddings = None

    if not embeddings:
        print("Using HuggingFace Embeddings (may download model)...")
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    vector_path = os.path.join(data_path, "..", "vectorstore")
    if os.path.exists(vector_path) and os.path.exists(os.path.join(vector_path, "index.faiss")):
        print("Loading existing vector store...")
        try:
            db = FAISS.load_local(vector_path, embeddings, allow_dangerous_deserialization=True)
            return SimpleQA(db, None)
        except Exception as e:
            print(f"Failed to load vector store: {e}")

    docs = load_pdfs(p)
    
    splitter = CharacterTextSplitter(separator="\n", chunk_size=1000, chunk_overlap=200, length_function=len)
    texts = splitter.split_documents(docs) if docs else []
    
    if texts:
        db = FAISS.from_documents(texts, embeddings)
        try:
            db.save_local(vector_path)
        except:
            pass
    else:
        seed_texts = ["General health guidance based on symptoms and severity."]
        db = FAISS.from_texts(seed_texts, embeddings)
    
    llm = None
    if key and ChatOpenAI:
        try:
            llm = ChatOpenAI(api_key=key, temperature=0)
        except Exception:
            llm = None

    return SimpleQA(db, llm)
