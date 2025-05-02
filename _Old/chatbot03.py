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
from langchain.chains import RetrievalQAWithSourcesChain

# โหลด .env
load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX")

llm = ChatOpenAI(model_name="gpt-4o")


# เชื่อมต่อ Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(INDEX_NAME)

# เตรียม embeddings
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

stats = index.describe_index_stats()
if stats.total_vector_count == 0:
    df = pd.read_csv("antiquities.csv")

    df = df[df["deleted_at"].isnull()]
    df["thumbnail"] = df["thumbnail"].fillna("")
    df["id"] = df["id"].fillna("").astype(str)

    docs = [
        Document(
            page_content = (
                f"ชื่อวัตถุโบราณ: {row['name_th']} ({row['name_en']}). "
                f"ทำจากวัสดุ: {row['material_tags']}. "
                f"ยุคสมัย: {row['period_tags']}. "
                f"สถานที่พบ: {row['place_tags']}."
                f"รายละเอียด: {row['artistic_description_th']}."
                f"รายละเอียด: {row['artistic_description_en']}."
                f"รายละเอียด: {row['historical_background_description_th']}."
                f"รายละเอียด: {row['historical_background_description_en']}."
                

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


custom_prompt = PromptTemplate(
    input_variables=["context", "question"],
    template="""\
คุณทำหน้าที่เป็นผู้เชี่ยวชาญวัตถุโบราณ
โดยใช้ข้อมูลที่ให้ด้านล่างนี้ กรุณาตอบคำถามอย่างกระชับ 4-5 ประโยค

ข้อมูลที่มี:
{context}

คำถาม:
{question}

คำตอบ:"""
)

if question:
    with st.spinner("🔍 กำลังค้นหาคำตอบจาก Pinecone..."):
    # mmr
        retriever = vectorstore.as_retriever(
            search_type="mmr",  # 🔥 Hybrid Search = MMR (Maximal Marginal Relevance)
            search_kwargs={
                "k": 4,             # ดึง 4 อันดับแรก
                "fetch_k":10,      # ค้นเยอะก่อน แล้วคัดให้ดี
            }
        )

        # ตั้ง RetrievalQA
        qa = RetrievalQA.from_chain_type(
            llm=llm,
            retriever=retriever,
            chain_type="stuff",
            chain_type_kwargs={"prompt": custom_prompt},
            return_source_documents=True,
        )
        result = qa.invoke({"query": question})

        st.subheader("📝 คำตอบสรุป:")
        st.success(result["result"])

        st.divider()
        st.subheader("📚 ข้อมูลที่ใช้ตอบ:")
        for i, doc in enumerate(result["source_documents"], start=1):
            st.markdown(f"**{i}.** {doc.page_content}")

            if "thumbnail" in doc.metadata and doc.metadata["thumbnail"]:
                st.image(doc.metadata["thumbnail"], width=200)

            if "id" in doc.metadata:
                st.caption(f"🆔 ID: {doc.metadata['id']}")
        # retriever = vectorstore.as_retriever(
        #     search_type="similarity_score_threshold",
        #     search_kwargs={
        #         "score_threshold": 0.5,
        #         "k": 3
        #     }
        # )

        # docs = retriever.get_relevant_documents(question)

        # if docs:
        #     # 1. แสดงทุกเอกสารก่อน
        #     st.subheader("📚 เอกสารที่ค้นเจอ:")
        #     for i, doc in enumerate(docs, start=1):
        #         st.markdown(f"### เอกสารที่ {i}")
        #         st.write(doc.page_content)

        #         if doc.metadata.get("thumbnail"):
        #             st.image(doc.metadata["thumbnail"], width=200)

        #         st.caption(f"🆔 ID: {doc.metadata.get('id', 'ไม่ระบุ')}")

        #     # 2. ส่ง context เข้า LLM เพื่อสรุป
        #     context = "\n\n".join([doc.page_content for doc in docs])

        #     chain = custom_prompt | llm
        #     result = chain.invoke({
        #         "context": context,
        #         "question": question
        #     })

        #     st.divider()
        #     st.subheader("📝 คำตอบสรุป:")
        #     st.write(result.content)

        # else:
        #     st.warning("ไม่พบข้อมูลที่ตรงกับคำถามเลยครับ 🕵️‍♂️")




##
##ขอ ข้อมูลลายดอกบัวบาน