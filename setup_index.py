# setup_index.py
import os
import pandas as pd
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.documents import Document
from pinecone import Pinecone, ServerlessSpec

# โหลด .env
load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

# Connect Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)

# เตรียมฝั่ง Embedding
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# โหลด CSV
df = pd.read_csv("antiquities.csv")
df = df[df["deleted_at"].isnull()]  # เอาเฉพาะข้อมูลที่ยังไม่ลบ
df["id"] = df["id"].astype(str)
df.fillna("", inplace=True)

# สร้าง Index แต่ละตัว
fields = {
    "name_th": "antiquities-name-th-index",
    "material_tags": "antiquities-material-tags-index",
    "artistic_description_th": "antiquities-artistic-description-th-index",
    "place_tags": "antiquities-place-tags-index",
    "historical_description_th": "antiquities-description-th-index"
}

for field, index_name in fields.items():
    if index_name not in pc.list_indexes().names():
        print(f"Creating index {index_name}...")
        pc.create_index(
            name=index_name,
            dimension=1536,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )

    index = pc.Index(index_name)

    # เตรียมเอกสาร
    docs = [
        Document(
            page_content=row[field],
            metadata={"id": row["id"]}
        )
        for _, row in df.iterrows()
        if row[field].strip() != ""
    ]

    print(f"Uploading {len(docs)} documents to {index_name}...")
    PineconeVectorStore.from_documents(docs, embeddings, index_name=index_name)

print("✅ Setup indexes complete.")
