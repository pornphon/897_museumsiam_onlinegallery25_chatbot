#การใช้งาน  เปิด xampp(mysql)

import os
import streamlit as st
from dotenv import load_dotenv
import pymysql
import re

from chatbot_stt_tts import tts

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
vectorstore_name = PineconeVectorStore(index=index_name, embedding=embeddings, namespace="")
vectorstore_material = PineconeVectorStore(index=index_material, embedding=embeddings, namespace="")
vectorstore_artistic = PineconeVectorStore(index=index_artistic, embedding=embeddings, namespace="")
vectorstore_place = PineconeVectorStore(index=index_place, embedding=embeddings, namespace="")
vectorstore_history = PineconeVectorStore(index=index_history, embedding=embeddings, namespace="")


#get only 1 ids each call
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

#get array of list 
def get_antiquities_by_id_from_db(ids: list[str]) -> list[dict]:
    if not ids:
        return []
    
    with db_conn.cursor() as cursor:
        format_strings = ','.join(['%s'] * len(ids))
        query = f"SELECT * FROM antiquities WHERE id IN ({format_strings})"
        cursor.execute(query, tuple(ids))
        return cursor.fetchall()
    
    # conn = pymysql.connect(
    #     host='localhost',
    #     user='root',
    #     password='',
    #     database='vm_siam',
    #     charset='utf8mb4',
    #     cursorclass=pymysql.cursors.DictCursor
    # )
    # try:





def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='',
        database='vm_siam',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

db_conn = get_db_connection()

# สร้าง Tools
@tool
def search_by_name(query: str) -> str:
    """ค้นหาวัตถุโบราณจากชื่อ ชิ้นส่วน (name_th) ชื่อลาย และคืน ID กลับมา"""
    retriever = vectorstore_name.as_retriever(search_type="similarity", search_kwargs={"k": 2})
    docs = retriever.invoke(query)

    if not docs:
        return "ไม่พบข้อมูล"
    ids = [doc.metadata.get("id", "") for doc in docs if doc.metadata.get("id")]
       
    results = []
    textoutput =f"search_by_name พบ ID จาก Pinecone {len(ids)}: {', '.join(ids)}"
    st.write(textoutput)

    antiquities = get_antiquities_by_id_from_db(ids)

    for data in antiquities:
        summary = f"🆔 {data['id']}\n📛 ชื่อ: {data.get('name_th', '-')}\n📜 รายละเอียด: {data.get('artistic_description_th', '-')}\n📍 แหล่งที่พบ: {data.get('place_found', '-')}\n📍 thumbnail: {data.get('thumbnail', '-')}"
        print("result: "+summary)
        results.append(summary)
    return "\n\n".join(results)
    
    # for id in ids:
    #     data = get_antiquity_by_id_from_db(id)
    #     if data:
    #         # สรุปข้อความสั้น ๆ หรือดึงเฉพาะบาง field ก็ได้
    #         summary = f"🆔 {data['id']}\n📛 ชื่อ: {data.get('name_th', '-')}\n📜 รายละเอียด: {data.get('artistic_description_th', '-')}\n📍 แหล่งที่พบ: {data.get('place_found', '-')}\n📍 thumbnail: {data.get('thumbnail', '-')}"
    #         # print("result: "+summary)
    #         results.append(summary)
    # return "\n\n".join(results)

@tool
def search_by_material(query: str) -> str:
    """ค้นหาวัตถุโบราณจากวัสดุ (material_tags) และคืน ID กลับมา"""
    retriever = vectorstore_material.as_retriever(search_type="similarity", search_kwargs={"k": 3})
    docs = retriever.invoke(query)

    if not docs:
        return "ไม่พบข้อมูล"
    ids = [doc.metadata.get("id", "") for doc in docs if doc.metadata.get("id")]
       
    results = []
    textoutput =f"search_by_material พบ ID จาก Pinecone {len(ids)}: {', '.join(ids)}"
    st.write(textoutput)
    
    for id in ids:
        data = get_antiquity_by_id_from_db(id)
        if data:
            # สรุปข้อความสั้น ๆ หรือดึงเฉพาะบาง field ก็ได้
            summary = f"🆔 {data['id']}\n📛 ชื่อ: {data.get('name_th', '-')}\n📜 รายละเอียด: {data.get('artistic_description_th', '-')}\n📍 แหล่งที่พบ: {data.get('place_found', '-')}\n📍 thumbnail: {data.get('thumbnail', '-')}"
            print("result: "+summary)
            results.append(summary)
    return "\n\n".join(results)

@tool
def search_by_artistic_description(query: str) -> str:
    """ค้นหาวัตถุโบราณจากคำอธิบายศิลปะ (artistic_description_th) และคืน ID กลับมา"""
    retriever = vectorstore_artistic.as_retriever(search_type="similarity", search_kwargs={"k": 3})
    docs = retriever.invoke(query)

    if not docs:
        return "ไม่พบข้อมูล"
    ids = [doc.metadata.get("id", "") for doc in docs if doc.metadata.get("id")]
       
    results = []
    textoutput =f"search_by_artistic_description พบ ID จาก Pinecone {len(ids)}: {', '.join(ids)}"
    st.write(textoutput)
    
    for id in ids:
        data = get_antiquity_by_id_from_db(id)
        if data:
            # สรุปข้อความสั้น ๆ หรือดึงเฉพาะบาง field ก็ได้
            summary = f"🆔 {data['id']}\n📛 ชื่อ: {data.get('name_th', '-')}\n📜 รายละเอียด: {data.get('artistic_description_th', '-')}\n📍 แหล่งที่พบ: {data.get('place_found', '-')}\n📍 thumbnail: {data.get('thumbnail', '-')}"
            print("result: "+summary)
            results.append(summary)
    return "\n\n".join(results)

@tool
def search_by_place_tags(query: str) -> str:
    """ค้นหาวัตถุโบราณจากสถานที่ผลิต (place_tags) และคืน ID กลับมา"""
    retriever = vectorstore_place.as_retriever(search_type="similarity", search_kwargs={"k": 3})
    docs = retriever.invoke(query)

    if not docs:
        return "ไม่พบข้อมูล"
    ids = [doc.metadata.get("id", "") for doc in docs if doc.metadata.get("id")]
       
    results = []
    textoutput =f"search_by_artistic_description พบ ID จาก Pinecone {len(ids)}: {', '.join(ids)}"
    st.write(textoutput)
    
    for id in ids:
        data = get_antiquity_by_id_from_db(id)
        if data:
            # สรุปข้อความสั้น ๆ หรือดึงเฉพาะบาง field ก็ได้
            summary = f"🆔 {data['id']}\n📛 ชื่อ: {data.get('name_th', '-')}\n📜 รายละเอียด: {data.get('artistic_description_th', '-')}\n📍 แหล่งที่พบ: {data.get('place_found', '-')}\n📍 thumbnail: {data.get('thumbnail', '-')}"
            print("result: "+summary)
            results.append(summary)
    return "\n\n".join(results)

@tool
def search_by_description(query: str) -> str:
    """ค้นหาวัตถุโบราณจากคำอธิบาย (historical_background_description_th) และคืน ID กลับมา"""
    retriever = vectorstore_history.as_retriever(search_kwargs={"k": 3})
    docs = retriever.invoke(query)
    return ",".join(doc.metadata.get("id", "") for doc in docs)

@tool #อาจจะต้องไปเอาจาก DB
def general_information(query: str) -> str:
    """ตอบคำถามเกี่ยวกับ museumsiam ข้อมูลทั่วไป, สถานที่, วันเวลาเปิด"""
    result ="""มิวเซียมสยาม หรือ พิพิธภัณฑ์การเรียนรู้ (อังกฤษ: Museum Siam, Discovery Museum) เป็นพิพิธภัณฑ์ตั้งอยู่บนถนนสนามไชย แขวงพระบรมมหาราชวัง เขตพระนคร กรุงเทพมหานคร เปิดให้บริการเมื่อ 2 เมษายน พ.ศ. 2551 มิวเซียมสยามดูแลโดยสถาบันพิพิธภัณฑ์การเรียนรู้แห่งชาติ
มิวเซียมสยาม พิพิธภัณฑ์การเรียนรู้นี้ ถือเป็นแหล่งการเรียนรู้หนึ่งที่เน้นจุดมุ่งหมายในการแสดงตัวตนของชนในชาติ ซึ่งจะทำให้ผู้เข้าชม โดยเฉพาะอย่างยิ่งผู้เข้าชมที่อยู่ในวัยเด็กและเยาวชน ได้เรียนรู้รากเหง้าของชาวไทย โดยเน้นไปที่กลุ่มชนในเขตเมืองบางกอก หรือที่เรียกในปัจจุบันว่า กรุงเทพมหานคร เป็นสำคัญ เนื่องจากตัวมิวเซียมสยามแห่งนี้ได้ตั้งอยู่ในเขตกรุงเทพมหานคร แต่มิได้หมายความว่าถ้าเป็นคนไทยต่างจังหวัด จะไม่สามารถมาเรียนรู้จากพิพิธภัณฑ์นี้ได้ ด้วยเพราะสิ่งที่จัดแสดงในตู้ เน้นการนำเสนอความเป็นไทย ในมิติที่ร่วมสมัยมากขึ้น ตั้งแต่อดีตถึงปัจจุบัน ผ่านการนำเสนอด้วยสื่อผสมหลายรูปแบบ ทำให้มีความน่าสนใจ และดึงดูดใจผู้เข้าชมได้เป็นอย่างยิ่ง ทั้งยังตั้งอยู่ในสถานที่สวยงาม
ปัจจุบัน ได้ทำการปรับปรุงนิทรรศการชุด เรียงความประเทศไทย เมื่อวันที่ 18 เมษายน 2559 ต่อมาได้มีการจัดทำนิทรรศการชุดใหม่โดยมีจุดประสงค์ให้มีเนื้อหาเท่าทันสมัย และตอบโจทย์ความต้องการของผู้เข้าชม มีชื่อชุดว่า นิทรรศการ "ถอดรหัสไทย" นำเสนอภายใน 14 ห้องนิทรรศการ ที่จะพาไปเรียนรู้ทุกมุมมองความเป็นไทย และพัฒนาการความเป็นไทย ตั้งแต่อดีตจนถึงปัจจุบัน อาทิ เรื่องราวด้านประวัติศาสตร์ สถาปัตยกรรม วัฒนธรรมประเพณี อาหารการกิน การแต่งกาย
สำหรับ นิทรรศการ "เรียงความประเทศไทย" ได้ทำการจัดแสดงกับ Muse Mobile มิวเซียมติดล้อ เป็นการจัดนิทรรศการในตู้คอนเทนเนอร์เคลื่อนที่ไปจัดแสดง ในสถานที่ต่างๆ โดยเล่าถึงประวัติศาสตร์ของประเทศและคนไทย ผ่านรูปแบบนิทรรศการที่ทันสมัยในตู้คอนเทนเนอร์ขนาดใหญ่
เปิดให้บริการ 10.00 - 18.00 น.
เปิดให้บริการวันอังคาร-วันอาทิตย์
"""
    return result

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
    """
คุณคือตัวช่วยตอบคำถามเกี่ยวกับวัตถุโบราณจากฐานข้อมูล นิสัยร่าเริง 

หากคุณพบข้อมูลวัตถุโบราณที่เกี่ยวข้อง ให้สรุปในรูปแบบดังนี้ มาแค่ 1 ชิ้น:

id: [รหัสวัตถุ]  
thumbnail: [URL รูปภาพ ถ้ามี]  
คำอธิบาย: [คำอธิบายโดยย่อที่เข้าใจง่าย เป็นกันเอง มีการทวนคำถามก่อนตอบ]
URL: [https://collection360.museumsiam.org/antiquities/detail/?id=[รหัสวัตถุ]]

ถ้าไม่พบข้อมูลให้ตอบว่า "ไม่พบข้อมูลที่เกี่ยวข้อง"
"""
    ),
    HumanMessagePromptTemplate.from_template("{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])


# สร้าง Agent พร้อม Prompt
agent = create_openai_functions_agent(llm=llm, tools=tools, prompt=agent_prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools)


st.set_page_config(page_title="Museum Chatbot", page_icon="🏺")
st.title("Museum Siam - RAG + Agent")

question = st.text_input("📥 พิมพ์คำถาม:")
# Streamlit เริ่ม


def extract_description(text):
    match = re.search(r"คำอธิบาย:\s*(.+)", text)
    if match:
        print(f"Extract Des: {match.group(1).strip()}")
        return match.group(1).strip()
    return "ไม่พบคำอธิบาย"


if question:
    with st.spinner("🔍 กำลังค้นหาคำตอบ..."):
        # Step 1: ใช้ Agent หา IDs
        agent_result = agent_executor.invoke({"input": question})
        ids = agent_result.get("output", "").split(",")
        st.write("agent_executor result: \n"+agent_result["output"])
        description_only=extract_description(agent_result["output"])
        #audio_url=tts(description_only)
        #if audio_url:
        #    st.audio(audio_url,format='audio/m4a')
