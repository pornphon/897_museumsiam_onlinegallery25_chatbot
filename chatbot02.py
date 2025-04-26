import streamlit as st
import os
import pandas as pd
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain_core.documents import Document
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

# โหลด .env
load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX")

llm = ChatOpenAI(model_name="gpt-4")


# เชื่อมต่อ Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(INDEX_NAME)

# เตรียม embeddings
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

stats = index.describe_index_stats()
if stats.total_vector_count == 0:
    df = pd.read_csv("antiquities.csv")

    df["thumbnail"] = df["thumbnail"].fillna("")
    df["id"] = df["id"].fillna("").astype(str)

    docs = [
        Document(
            page_content = (
                f"ชื่อวัตถุโบราณ: {row['name_th']} ({row['name_en']}). "
                f"ทำจากวัสดุ: {row['material_tags']}. "
                f"ยุคสมัย: {row['period_tags']}. "
                f"สถานที่พบ: {row['place_tags']}."
            )
        )
        for _, row in df.iterrows()
    ]
    print("🟡 Uploading documents to Pinecone...")
    PineconeVectorStore.from_documents(docs, embeddings, index_name=INDEX_NAME)
else:
    print(f"✅ Already have {stats.total_vector_count} vectors in Pinecone.")






# สร้าง vectorstore
vectorstore = PineconeVectorStore(index=index, embedding=embeddings, text_key="text")

# === Streamlit UI ===
st.set_page_config(page_title="Museum Chatbot", page_icon="🏺")
st.title("🗿 ถาม-ตอบเรื่องวัตถุโบราณ")

question = st.text_input("📥 พิมพ์คำถามของคุณที่นี่:")

if question:
    with st.spinner("🔍 กำลังค้นหาคำตอบจาก Pinecone..."):
        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
        results = retriever.get_relevant_documents(question)
        qa = RetrievalQA.from_chain_type(llm=llm,retriever=retriever,return_source_documents=True)       

    if results:
        for i, doc in enumerate(results, start=1):
            st.markdown(f"### ✅ คำตอบที่ {i}")
            st.write(doc.page_content)

            if doc.metadata.get("thumbnail"):
                st.image(doc.metadata["thumbnail"], width=200)

            st.caption(f"🆔 ID: {doc.metadata.get('id')}")

        st.write(f"final คำตอบ {qa}")




    else:
        st.warning("ไม่พบข้อมูลที่เกี่ยวข้อง 🕵️‍♂️")
