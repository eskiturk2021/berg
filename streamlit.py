import streamlit as st
import os
from langchain.chains import RetrievalQA
from langchain.document_loaders import PyPDFLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI

# Установите ваш API ключ от OpenAI в безопасном месте
os.environ["OPENAI_API_KEY"] = "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"

# Загрузка PDF и обработка документов
pdf_loader = PyPDFLoader("berg.pdf")
documents = pdf_loader.load()
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
documents = text_splitter.split_documents(documents)

# Построение векторной базы данных
vector_db = Chroma.from_documents(
    documents,
    embedding=OpenAIEmbeddings(),
    persist_directory="./data"
)

vector_db.persist()

# Настройка цепочки Q&A
qa_chain = RetrievalQA.from_chain_type(
    llm=ChatOpenAI(model_name="gpt-3.5-turbo"),
    retriever=vector_db.as_retriever(search_kwargs={"k": 3}),
    return_source_documents=True
)

# Интерфейс Streamlit
st.title('Медицинская консультация')

# Поля для ввода информации пользователем
age = st.number_input("Ваш возраст", min_value=0, max_value=130, step=1)
gender = st.radio("Ваш пол", ('Мужской', 'Женский', 'Другой'))
weight = st.number_input("Ваш вес (в килограммах)", min_value=0, max_value=300, step=1)
chronic_diseases = st.text_input("Хронические заболевания (если есть, укажите их)")
symptoms = st.text_area("Что вас беспокоит? Опишите ваши симптомы")

# Кнопка для получения консультации
if st.button('Получить консультацию'):
    if not symptoms:
        st.warning('Пожалуйста, опишите ваши симптомы.')
    else:
        with st.spinner('Обрабатываем ваш запрос...'):
            # Обработка запроса
            user_query = f"Возраст: {age}, Пол: {gender}, Вес: {weight}, Хронические заболевания: {chronic_diseases}, Симптомы: {symptoms}"
            result = qa_chain({"query": user_query})
            answer = result['result']
            st.success('Ваша консультация:')
            st.write(answer)
