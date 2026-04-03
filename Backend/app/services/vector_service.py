from rag.loader import load_pdf
from rag.splitter import split_documents
from rag.vectorstore import load_vectorstore, create_vectorstore


def process_and_store(file_path: str, file_id: str, user_id: int, filename: str = None):
    """Process and store documents in user-specific vectorstore."""
    documents = load_pdf(file_path)

    for doc in documents:
        doc.metadata["file_id"] = file_id
        doc.metadata["user_id"] = user_id
        if filename:
            doc.metadata["filename"] = filename
        # keep existing source/page metadata in sync if available
        doc.metadata["source"] = filename or doc.metadata.get("source", file_id)

    chunks = split_documents(documents)

    try:
        vectorstore = load_vectorstore(user_id=user_id)
        vectorstore.add_documents(chunks)
    except:
        vectorstore = create_vectorstore(chunks, user_id=user_id)

    return True