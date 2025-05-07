import requests
import os
from playsound import playsound

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
        'Botnoi-Token': 'kiMZTMEAeyjHfESIJANIoOmryvUAe4CU',
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


if __name__ == "__main__":
    tts("สวัสดีครับ ผมชื่อปืนครับ")
