from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

def create_vectorstore(chunks, user_id: int = None):
    embedding = OllamaEmbeddings(model="nomic-embed-text")
    
    collection_name = f"user_{user_id}" if user_id else "default"

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embedding,
        persist_directory="chroma_db",
        collection_name=collection_name
    )

    return vectorstore

def load_vectorstore(user_id: int = None):
    embedding = OllamaEmbeddings(model="nomic-embed-text")
    
    collection_name = f"user_{user_id}" if user_id else "default"

    vectorstore = Chroma(
        persist_directory="chroma_db",
        embedding_function=embedding,
        collection_name=collection_name
    )

    return vectorstore