import pymysql
import pandas as pd
import streamlit as st

# ตั้งค่าการเชื่อมต่อฐานข้อมูล
conn = pymysql.connect(
    host='localhost',
    user='root',
    password='',
    database='vm_siam',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)

# Streamlit UI
st.set_page_config(page_title="SQL Viewer", page_icon="📊")
st.title("📊 ข้อมูลวัตถุโบราณจากฐานข้อมูล")

query = st.text_input("🔍 พิมพ์คำสั่ง SQL (SELECT):", "SELECT * FROM artifacts LIMIT 10")

if st.button("ดึงข้อมูล"):
    try:
        with conn.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
            df = pd.DataFrame(result)
            st.dataframe(df)
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาด: {e}")
