from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
from dotenv import load_dotenv
load_dotenv()


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


def extract_sources(docs):
    sources = []
    seen = set()

    for doc in docs:
        # Prefer filename, fallback to persistent source/file_id
        source = doc.metadata.get("filename") or doc.metadata.get("source") or "unknown"
        page = doc.metadata.get("page", "unknown")

        key = (source, page)

        if key not in seen:
            seen.add(key)
            sources.append({
                "source": source,
                "page": page
            })

    return sources


def create_chain(retriever):
    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        temperature=0
    )

    prompt = PromptTemplate(
        template="""You are a helpful assistant.

        Answer the question ONLY using the provided context.
        If not found, say "I don't know".

        Context:
        {context}

        Question:
        {question}

        Answer:
        """,
        input_variables=['context','question'],
        validate_template=True
    )

    chain = (
        {
            "docs": retriever,
            "question": RunnablePassthrough()
        }
        | RunnableLambda(lambda x: {
            "context": format_docs(x["docs"]),
            "sources": extract_sources(x["docs"]),
            "question": x["question"]
        })
        | {
            "answer": prompt | llm | StrOutputParser(),
            "sources": lambda x: x["sources"]
        }
    )

    return chain