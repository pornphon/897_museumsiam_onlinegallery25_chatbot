import os
import pandas as pd
from dotenv import load_dotenv
#from langchain_community.vectorstores import Pinecone as LangchainPinecone
#from langchain_community.embeddings import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
import streamlit as st

from langchain_core.documents import Document
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec








# โหลด .env
load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX")


pc = Pinecone(api_key=PINECONE_API_KEY)

index = pc.Index(INDEX_NAME)

st.set_page_config(page_title="Museum Chatbot", page_icon="🏺")
st.title("🗿 ถาม-ตอบเรื่องวัตถุโบราณ")
question = st.text_input("📥 พิมพ์คำถามของคุณที่นี่:")
# เตรียม embeddings
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# เช็ค vector count
stats = index.describe_index_stats()
if stats.total_vector_count == 0:
    df = pd.read_csv("antiquities.csv")

    df["thumbnail"] = df["thumbnail"].fillna("")
    df["id"] = df["id"].fillna("").astype(str)

    docs = [
        Document(
            page_content=f"{row['name_th']} {row['name_en']} {row['material_tags']} {row['period_tags']} {row['place_tags']}",
            metadata={"thumbnail": row["thumbnail"], "id": row["id"]}
        )
        for _, row in df.iterrows()
    ]
    print("🟡 Uploading documents to Pinecone...")
    PineconeVectorStore.from_documents(docs, embeddings, index_name=INDEX_NAME)
else:
    print(f"✅ Already have {stats.total_vector_count} vectors in Pinecone.")

# === Query Section ===
def query_antique(question: str):

    vectorstore = PineconeVectorStore(index=index, embedding=embeddings,text_key="text")



    #vectorstore = LangchainPinecone(index=index, embedding=embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    results = retriever.get_relevant_documents(question)

    if results:
        #doc = results[1]
        return [
            {
                "content": doc.page_content,
                "thumbnail": doc.metadata.get("thumbnail", None),
                "id": doc.metadata.get("id", None)
            }
            for doc in results
        ]
    else:
        return {
            "content": "ไม่พบข้อมูลวัตถุโบราณที่เกี่ยวข้อง",
            "thumbnail": None,
            "id": None
        }

# ✅ ใช้งานจริง
if __name__ == "__main__":
    question = "ลายอาครา"
    response = query_antique(question)
    print("🗣️ คำตอบ:\n", response)

