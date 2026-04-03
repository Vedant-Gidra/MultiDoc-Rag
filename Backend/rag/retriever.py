from langchain_classic.retrievers import MultiQueryRetriever
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

def get_retriever(vectorstore,file_id):

    base_retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": 4,          # total docs to return
            "fetch_k": 20,   # candidates before filtering
            "lambda_mult": 0.5,
            "filter": {"file_id": file_id}
        }
    )

    llm = ChatGroq(model="llama-3.1-8b-instant",temperature=0)

    retriever = MultiQueryRetriever.from_llm(
        retriever=base_retriever,
        llm=llm
    )

    return retriever