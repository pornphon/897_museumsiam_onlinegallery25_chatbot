import openai
import pyttsx3
import requests
from tts_botnoi import tts
import os
from playsound import playsound

#ใช้ open AI ในการ stt จาก mp3 (transcripe) + tts  โดยใช้ botnoi  แต่ botnoi ไม่สามารถส่งข้อมูลแบบ stream ได้

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
#client = os.getenv("OPENAI_API_KEY")
BOTNOI_TOKEN = os.getenv("BOTNOI_TOKEN")

print(f"Boinoi_Token {BOTNOI_TOKEN}")

def transcribe_audio(file_path):
    with open(file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="th",
            prompt="วัตถุโบราณ พิพิธภัณฑ์ ลายจีน ถ้วยเคลือบ"
        )
    return transcript.text

# ✅ ฟังก์ชัน: ปรับข้อความให้ลื่นไหลด้วย GPT
def rewrite_text_with_gpt(text: str, model="gpt-4") -> str:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "คุณคือผู้ช่วยที่เก่งในการปรับข้อความเสียงพูดภาษาไทยให้ลื่นไหล อ่านเข้าใจง่าย และเหมาะกับการแสดงผล"
            },
            {
                "role": "user",
                "content": f"กรุณาปรับให้ข้อความนี้อ่านเข้าใจง่าย:\n{text}"
            }
        ]
    )
    return response.choices[0].message.content


#text->speech
def tts(text):
    # สร้าง TTS ด้วย Botnoi API
    url = "https://api-voice.botnoi.ai/openapi/v1/generate_audio"
    payload = {
        "text": text,
        "speaker": "6",
        "volume": 1,
        "speed": 1,
        "type_media": "m4a",
        "save_file": "true",
        "language": "th",
    }
    headers = {
    #    'Botnoi-Token': 'kiMZTMEAeyjHfESIJANIoOmryvUAe4CU',
        'Botnoi-Token': BOTNOI_TOKEN,
        'Content-Type': 'application/json'
    }
    response = requests.post(url, headers=headers, json=payload)

    if response.ok:
        result = response.json()
        print("✅ API response:", result)
        audio_url = response.json().get("audio_url")
        print("🔊 Playing:", audio_url)

        # ดาวน์โหลดไฟล์ชั่วคราว
        audio_response = requests.get(audio_url)
        temp_path = "temp_audio.m4a"
        with open(temp_path, "wb") as f:
            f.write(audio_response.content)

        # เล่นเสียง
        playsound(temp_path)

        # ลบไฟล์ชั่วคราว
        os.remove(temp_path)
    else:
        print("❌ Error:", response.text)


# ✅ Main: รับไฟล์ mp3 และประมวลผล
if __name__ == "__main__":
    input_mp3 = "v01.mp3"  # ← แก้ชื่อไฟล์ตรงนี้

    print("📥 ถอดเสียงจาก mp3...")
    raw_text = transcribe_audio(input_mp3)
    print("📝 ข้อความดิบ:", raw_text)



    # print("✍️ กำลังปรับให้ลื่นไหล...")
    # refined = rewrite_text_with_gpt(raw_text)
    # print("✅ ข้อความหลังปรับ:", refined)

    print("🔊 กำลังพูดออกเสียง...")
    ##tts(raw_text)
    tts("จานดินเผาปากผายเขียนลายสีดำใต้เคลือบ ตรงกลางเป็นรูปปลาในวงกลม ผลิตจากกลุ่มเตาเมืองสุโขทัย")
