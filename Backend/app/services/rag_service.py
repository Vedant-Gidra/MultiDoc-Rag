from rag.vectorstore import load_vectorstore
from rag.retriever import get_retriever
from rag.chain import create_chain


def query_rag(question: str, file_id: str, user_id: int, filename: str = None):
    """Query the RAG pipeline for a specific user."""
    vectorstore = load_vectorstore(user_id=user_id)

    retriever = get_retriever(vectorstore, file_id)

    chain = create_chain(retriever)

    response = chain.invoke(question)

    # Post-process sources to display file name instead of file_id when possible
    sources = response.get("sources")
    if isinstance(sources, list) and filename:
        updated_sources = []
        for src in sources:
            if isinstance(src, dict):
                source_value = src.get("source")
                if source_value == file_id or source_value == "unknown" or str(file_id) in str(source_value):
                    src["source"] = filename
                updated_sources.append(src)
            else:
                if src == file_id or src == "unknown" or str(file_id) in str(src):
                    updated_sources.append(filename)
                else:
                    updated_sources.append(src)
        response["sources"] = updated_sources

    return response