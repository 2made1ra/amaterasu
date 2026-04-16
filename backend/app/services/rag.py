import re
from app.core.config import settings
from app.services.llm import get_embeddings, get_llm

COLLECTION_NAME = settings.QDRANT_CHUNK_COLLECTION

class RagDependencyError(RuntimeError):
    """Raised when optional RAG dependencies are unavailable."""


def _get_text_splitter_class():
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        return RecursiveCharacterTextSplitter
    except ImportError:
        # Backward compatibility with older LangChain versions.
        try:
            from langchain.text_splitter import RecursiveCharacterTextSplitter
            return RecursiveCharacterTextSplitter
        except ImportError as exc:
            raise RagDependencyError(
                "Missing text splitter dependency. Install `langchain-text-splitters`."
            ) from exc


def process_pdf(file_path: str):
    try:
        from langchain_community.document_loaders import PyPDFLoader
    except ImportError as exc:
        raise RagDependencyError(
            "Missing PDF loader dependency. Install `langchain-community`."
        ) from exc

    loader = PyPDFLoader(file_path)
    documents = loader.load()

    RecursiveCharacterTextSplitter = _get_text_splitter_class()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    docs = text_splitter.split_documents(documents)
    return docs

def extract_metadata_from_text(text: str):
    # Using the LLM to extract a deadline
    llm = get_llm()
    prompt = f"Please read the following text and extract the deadline date if any. Return only the date in YYYY-MM-DD format. If not found, return 'None'. Text: {text[:2000]}"
    try:
        response = llm(prompt)
        # basic regex search for dates in YYYY-MM-DD
        date_pattern = r'\d{4}-\d{2}-\d{2}'
        matches = re.findall(date_pattern, response)
        extracted_date = matches[0] if matches else None
    except Exception as e:
        extracted_date = None

    return {"deadline": extracted_date}

def save_to_vectorstore(docs, document_id: int, owner_id: int):
    try:
        from langchain_community.vectorstores import Qdrant
    except ImportError as exc:
        raise RagDependencyError(
            "Missing vectorstore dependency. Install `langchain-community`."
        ) from exc

    # Add metadata for Tenant Isolation (filtering by owner and document)
    for doc in docs:
        doc.metadata["document_id"] = document_id
        doc.metadata["owner_id"] = owner_id

    embeddings = get_embeddings()
    Qdrant.from_documents(
        docs,
        embeddings,
        url=f"http://{settings.QDRANT_HOST}:{settings.QDRANT_PORT}",
        collection_name=COLLECTION_NAME,
        force_recreate=False
    )

def query_rag(query: str, owner_id: int, document_id: int = None):
    try:
        from langchain_community.vectorstores import Qdrant
        from langchain.chains import RetrievalQA
        from langchain.prompts import PromptTemplate
        from qdrant_client import QdrantClient
        from qdrant_client.http import models
    except ImportError as exc:
        raise RagDependencyError(
            "Missing RAG dependencies. Install LangChain and Qdrant client packages."
        ) from exc

    qdrant_client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
    embeddings = get_embeddings()
    qdrant = Qdrant(
        client=qdrant_client, collection_name=COLLECTION_NAME,
        embeddings=embeddings
    )

    # Proper Qdrant Filter
    must_conditions = [
        models.FieldCondition(
            key="metadata.owner_id",
            match=models.MatchValue(value=owner_id)
        )
    ]

    if document_id:
        must_conditions.append(
            models.FieldCondition(
                key="metadata.document_id",
                match=models.MatchValue(value=document_id)
            )
        )

    filter_obj = models.Filter(must=must_conditions)

    retriever = qdrant.as_retriever(search_kwargs={"filter": filter_obj})

    llm = get_llm()

    template = """
    You are an AI assistant for contract analysis. Use the following pieces of context to answer the question at the end.
    If searching for suppliers/contractors, provide a summary of the found suppliers based on the context.
    If you don't know the answer, just say that you don't know, don't try to make up an answer.

    Context: {context}

    Question: {question}
    Answer:"""

    QA_CHAIN_PROMPT = PromptTemplate.from_template(template)

    qa_chain = RetrievalQA.from_chain_type(
        llm,
        retriever=retriever,
        chain_type_kwargs={"prompt": QA_CHAIN_PROMPT}
    )

    result = qa_chain({"query": query})
    return result["result"]
