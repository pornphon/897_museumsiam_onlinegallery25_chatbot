import os
import streamlit as st
from dotenv import load_dotenv
import pymysql

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_pinecone import PineconeVectorStore
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain_core.tools import tool
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from pinecone import Pinecone
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder, HumanMessagePromptTemplate, SystemMessagePromptTemplate


# โหลด ENV
load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX")

# เชื่อมต่อ Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)

index_names = {
    "name_th": "antiquities-name-th-index",
    "material_tags": "antiquities-material-tags-index",
    "artistic_description_th": "antiquities-artistic-description-th-index",
    "place_tags": "antiquities-place-tags-index",
    "historical_description_th": "antiquities-description-th-index"
}

# โหลดแต่ละ index
index_name = pc.Index(index_names["name_th"])
index_material = pc.Index(index_names["material_tags"])
index_artistic = pc.Index(index_names["artistic_description_th"])
index_place = pc.Index(index_names["place_tags"])
index_history = pc.Index(index_names["historical_description_th"])

# เตรียม Embeddings และ LLM
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
llm = ChatOpenAI(model="gpt-4o")

# เตรียม VectorStores
#vectorstore_name = PineconeVectorStore(index=index_name, embedding=embeddings, namespace="name_namespace")
vectorstore_name = PineconeVectorStore(index=index_name, embedding=embeddings, namespace="")
vectorstore_material = PineconeVectorStore(index=index_material, embedding=embeddings, namespace="")
vectorstore_artistic = PineconeVectorStore(index=index_artistic, embedding=embeddings, namespace="")
vectorstore_place = PineconeVectorStore(index=index_place, embedding=embeddings, namespace="")
vectorstore_history = PineconeVectorStore(index=index_history, embedding=embeddings, namespace="")


def get_antiquity_by_id_from_db(antiquity_id: str) -> dict:
    conn = pymysql.connect(
        host='localhost',
        user='root',
        password='',
        database='vm_siam',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM antiquities WHERE id = %s", (antiquity_id,))
            return cursor.fetchone()
    finally:
        conn.close()




# สร้าง Tools
@tool
def search_by_name(query: str) -> str:
    """ค้นหาวัตถุโบราณจากชื่อ ชิ้นส่วน (name_th) ชื่อลาย และคืน ID กลับมา"""
    #retriever = vectorstore_name.as_retriever(search_type="mmr",search_kwargs={"k": 3})
    retriever = vectorstore_name.as_retriever(search_type="similarity", search_kwargs={"k": 3})

    #print("search by name ")
    docs = retriever.invoke(query)

    if not docs:
        return "ไม่พบข้อมูล"
    
    ids = [doc.metadata.get("id", "") for doc in docs if doc.metadata.get("id")]
    print(f"🔍 พบ ID จาก Pinecone: {', '.join(ids)}")
    
    results = []

    for aid in ids:
        data = get_antiquity_by_id_from_db(aid)
        if data:
            # สรุปข้อความสั้น ๆ หรือดึงเฉพาะบาง field ก็ได้
            summary = f"🆔 {data['id']}\n📛 ชื่อ: {data.get('name_th', '-')}\n📜 รายละเอียด: {data.get('artistic_description_th', '-')}\n📍 แหล่งที่พบ: {data.get('place_found', '-')}"
            print("result: "+summary)
            results.append(summary)

    return "\n\n".join(results) if results else "ไม่พบข้อมูลในฐานข้อมูล MySQL"

@tool
def search_by_material(query: str) -> str:
    """ค้นหาวัตถุโบราณจากวัสดุ (material_tags) และคืน ID กลับมา"""
    retriever = vectorstore_material.as_retriever(search_kwargs={"k": 3})
    docs = retriever.invoke(query)
    return ",".join(doc.metadata.get("id", "") for doc in docs)

@tool
def search_by_artistic_description(query: str) -> str:
    """ค้นหาวัตถุโบราณจากคำอธิบายศิลปะ (artistic_description_th) และคืน ID กลับมา"""
    retriever = vectorstore_artistic.as_retriever(search_kwargs={"k": 3})
    docs = retriever.invoke(query)
    return ",".join(doc.metadata.get("id", "") for doc in docs)

@tool
def search_by_place_tags(query: str) -> str:
    """ค้นหาวัตถุโบราณจากสถานที่ผลิต (place_tags) และคืน ID กลับมา"""
    retriever = vectorstore_place.as_retriever(search_kwargs={"k": 3})
    docs = retriever.invoke(query)

    return ",".join(doc.metadata.get("id", "") for doc in docs)

@tool
def search_by_description(query: str) -> str:
    """ค้นหาวัตถุโบราณจากคำอธิบาย (historical_background_description_th) และคืน ID กลับมา"""
    retriever = vectorstore_history.as_retriever(search_kwargs={"k": 3})
    docs = retriever.invoke(query)
    return ",".join(doc.metadata.get("id", "") for doc in docs)

@tool #อาจจะต้องไปเอาจาก DB
def general_information(query: str) -> str:
    """ตอบคำถามเกี่ยวกับ museumsiam ข้อมูลทั่วไป, สถานที่, วันเวลาเปิด"""
    retriever = vectorstore_history.as_retriever(search_kwargs={"k": 3})
    docs = retriever.invoke(query)
    return ",".join(doc.metadata.get("id", "") for doc in docs)

tools = [
    search_by_name,
    search_by_material,
    search_by_artistic_description,
    search_by_place_tags,
    search_by_description,
    general_information
]

# Prompt Template สำหรับสรุป
agent_prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(
        "คุณคือผู้ช่วยที่เก่งในการค้นหาข้อมูลวัตถุโบราณจากฐานข้อมูล"
    ),
    HumanMessagePromptTemplate.from_template("{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])


# สร้าง Agent พร้อม Prompt
agent = create_openai_functions_agent(llm=llm, tools=tools, prompt=agent_prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)







# result = search_by_name.invoke("จานลายปลา")
# print(result)

st.set_page_config(page_title="Museum Chatbot", page_icon="🏺")
st.title("Museum Siam - RAG + Agent")

question = st.text_input("📥 พิมพ์คำถาม:")
# Streamlit เริ่ม


if question:
    with st.spinner("🔍 กำลังค้นหาคำตอบ..."):
        # Step 1: ใช้ Agent หา IDs
        agent_result = agent_executor.invoke({"input": question})
        ids = agent_result.get("output", "").split(",")

        st.write("agent_result"+agent_result["output"])

        if ids and ids[0].strip():
            # Step 2: ดึง Document จาก ID ที่เจอ
            retriever = vectorstore_name.as_retriever(search_kwargs={"k": 5})
            docs = retriever.get_relevant_documents(question)

            filtered_docs = [doc for doc in docs if str(doc.metadata.get("id")) in ids]

            if not filtered_docs:
                st.warning("ไม่พบข้อมูลวัตถุโบราณที่ตรงกับ ID")
            else:
                # Step 3: ใช้ RAG เพื่อสรุป
                qa = RetrievalQA.from_chain_type(
                    llm=llm,
                    retriever=retriever,
                    chain_type="stuff",
                    chain_type_kwargs={"prompt": custom_prompt},
                    return_source_documents=True,
                )
                result = qa.invoke({"query": question})

                st.subheader("📝 คำตอบ:")
                st.write(result["result"])

                st.divider()
                st.subheader("📚 เอกสารที่นำมาตอบ:")
                for doc in filtered_docs:
                    st.write(doc.page_content)
                    if doc.metadata.get("thumbnail"):
                        st.image(doc.metadata["thumbnail"], width=150)
        else:
            st.warning("❗ ไม่พบข้อมูลที่ตรงกับคำถาม")
