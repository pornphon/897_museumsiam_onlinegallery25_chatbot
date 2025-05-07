import openai
import pyttsx3

def transcribe_audio(file_path):
    with open(file_path, "rb") as audio_file:
        transcript = openai.Audio.transcribe(
            model="whisper-1",
            file=audio_file,
            language="th",
            prompt="วัตถุโบราณ พิพิธภัณฑ์ ลายจีน ถ้วยเคลือบ"
        )
    return transcript["text"]

# ✅ ฟังก์ชัน: ปรับข้อความให้ลื่นไหลด้วย GPT
def rewrite_text_with_gpt(text: str, model="gpt-4") -> str:
    response = openai.ChatCompletion.create(
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
    return response["choices"][0]["message"]["content"]

# ✅ ฟังก์ชัน: พูดออกเสียงด้วย TTS
def speak(text):
    engine = pyttsx3.init()
    engine.setProperty("rate", 170)
    engine.say(text)
    engine.runAndWait()

# ✅ Main: รับไฟล์ mp3 และประมวลผล
if __name__ == "__main__":
    input_mp3 = "v03.mp3"  # ← แก้ชื่อไฟล์ตรงนี้

    print("📥 ถอดเสียงจาก mp3...")
    raw_text = transcribe_audio(input_mp3)
    print("📝 ข้อความดิบ:", raw_text)

    print("✍️ กำลังปรับให้ลื่นไหล...")
    refined = rewrite_text_with_gpt(raw_text)
    print("✅ ข้อความหลังปรับ:", refined)

    prdint("🔊 กำลังพูดออกเสียง...")
    speak(refined)