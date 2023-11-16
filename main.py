import os
from langchain.chains import RetrievalQA
from langchain.document_loaders import PyPDFLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI

# Установите ваш API ключ от OpenAI здесь
os.environ["OPENAI_API_KEY"] = "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"

pdf_loader = PyPDFLoader("berg.pdf")
documents = pdf_loader.load()

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
documents = text_splitter.split_documents(documents)

vector_db = Chroma.from_documents(
    documents,
    embedding=OpenAIEmbeddings(),
    persist_directory="./data"
)

vector_db.persist()

qa_chain = RetrievalQA.from_chain_type(
    llm=ChatOpenAI(model_name="gpt-3.5-turbo"),
    retriever=vector_db.as_retriever(search_kwargs={"k": 3}),
    return_source_documents=True
)

queries = [
    "Что можно есть при кето диете?",

]

for query in queries:
    result = qa_chain({"query": query})
    print(f"question: {query}")
    print(f"response: {result['result']}")
