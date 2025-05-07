import sounddevice as sd
import wavio
import keyboard
import time
import openai

# กำหนด API Key ของคุณ
client = openai.OpenAI(api_key="sk-...")  # แก้ด้วย key จริงของคุณ

# ตั้งค่าการอัดเสียง
SAMPLE_RATE = 44100
DURATION_LIMIT = 60  # กันอัดนานเกิน

recording = []
is_recording = False

def record_audio(filename="recorded.wav"):
    print("🎙 เริ่มอัดเสียง... (กด space ค้างไว้)")
    global recording
    recording = sd.rec(int(SAMPLE_RATE * DURATION_LIMIT), samplerate=SAMPLE_RATE, channels=1)
    sd.wait()
    wavio.write(filename, recording, SAMPLE_RATE, sampwidth=2)
    print("✅ อัดเสร็จแล้ว:", filename)

def transcribe_audio(file_path):
    with open(file_path, "rb") as f:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            language="th"
        )
    print("📝 คำที่ถอดได้:", transcript.text)

# -----------------------------
print("🔁 พร้อมใช้งาน: กดค้าง Spacebar เพื่ออัดเสียง")

while True:
    keyboard.wait("space")
    start_time = time.time()
    sd.default.samplerate = SAMPLE_RATE
    sd.default.channels = 1
    duration = 0

    print("⏺ กำลังอัด...")
    recording = sd.rec(int(SAMPLE_RATE * DURATION_LIMIT), samplerate=SAMPLE_RATE, channels=1)
    while keyboard.is_pressed("space"):
        time.sleep(0.1)
        duration = time.time() - start_time
        if duration >= DURATION_LIMIT:
            print("⏹ เกินเวลาสูงสุดที่กำหนด")
            break
    sd.stop()

    wavio.write("recorded.wav", recording[:int(SAMPLE_RATE * duration)], SAMPLE_RATE, sampwidth=2)
    print("📁 บันทึกเป็น recorded.wav ความยาว", round(duration, 2), "วินาที")

    # ส่งไป STT
    transcribe_audio("recorded.wav")

    print("🔁 พร้อมอัดใหม่ (กด Spacebar)...")