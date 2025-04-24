import os
import pandas as pd
from dotenv import load_dotenv

from langchain_community.vectorstores import Pinecone as LangchainPinecone
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_core.documents import Document
##from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
#from pinecone import CreateIndexRequest

# โหลด .env
load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX")



index = PineconeVectorStore.Index(INDEX_NAME)

# Load CSV
df = pd.read_csv("antiquities.csv")

# เตรียม embeddings
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# ตรวจว่ามีข้อมูลใน Pinecone แล้วหรือยัง
existing = index.describe_index_stats().get('total_vector_count', 0)
if existing == 0:
    print("Pinecone index is empty. Uploading...")

    docs = [
        Document(
            page_content=f"{row['name_th']} {row['name_en']} {row['material_tags']} {row['period_tags']} {row['place_tags']}",
            metadata={"thumbnail": row["thumbnail"]}
        )
        for _, row in df.iterrows()
    ]

    PineconeVectorStore.from_documents(
        docs, embeddings, index_name=INDEX_NAME, namespace="", index=index
    )
else:
    print(f"Pinecone index already has {existing} vectors.")

# === Query section ===
def query_artifact(text_query: str):
    vectorstore = LangchainPinecone(index=index, embedding=embeddings, text_key="text")
    retriever = vectorstore.as_retriever(search_kwargs={"k": 1})
    results = retriever.get_relevant_documents(text_query)

    if results:
        top = results[0]
        return {
            "content": top.page_content,
            "thumbnail": top.metadata.get("thumbnail", "No thumbnail")
        }
    else:
        return {"content": "ไม่พบข้อมูลที่เกี่ยวข้อง", "thumbnail": None}

# ตัวอย่างการใช้งาน
if __name__ == "__main__":
    query = "จานลายบิม่า"
    result = query_artifact(query)
    print("🔍 คำตอบ:", result["content"])
    print("🖼️ URL รูป:", result["thumbnail"])
