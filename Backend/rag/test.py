from vectorstore import load_vectorstore
from retriever import get_retriever
from chain import create_chain
import time

def main():
    vectorstore = load_vectorstore()

    start_time = time.time()

    retriever = get_retriever(vectorstore,"f154f194-b941-4cfc-8cda-01e7a05d9faf")
    chain = create_chain(retriever)
    print(chain.invoke('what is transformer?'))
    
    end_time = time.time()
    print('/n/n',end_time - start_time)


if __name__ == "__main__":
    main()