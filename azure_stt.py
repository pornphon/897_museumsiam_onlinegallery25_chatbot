import os
import azure.cognitiveservices.speech as speechsdk

# ตั้งค่าคีย์และ region ของ Azure Speech
speech_key = os.getenv("AZURE_SPEECH_KEY") or "YOUR_KEY"
region = os.getenv("AZURE_REGION") or "southeastasia"

def recognize_from_microphone():
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=region)
    speech_config.speech_recognition_language = "th-TH"

    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
    speech_recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config,
        audio_config=audio_config
    )

    # ฟังก์ชัน callback เมื่อได้คำพูดแต่ละประโยค
    def recognized_callback(evt):
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            print(f"🗣 คุณพูดว่า: {evt.result.text}")
        elif evt.result.reason == speechsdk.ResultReason.NoMatch:
            print("❗ ไม่เข้าใจคำพูด")

    # เชื่อม callback
    speech_recognizer.recognized.connect(recognized_callback)

    # เริ่มการรู้จำแบบต่อเนื่อง
    print("🎙 เริ่มฟัง (กด Ctrl+C เพื่อหยุด)...")
    speech_recognizer.start_continuous_recognition()

    try:
        while True:
            pass  # ให้รันไปเรื่อย ๆ
    except KeyboardInterrupt:
        print("🛑 หยุดแล้ว")
        speech_recognizer.stop_continuous_recognition()

if __name__ == "__main__":
    recognize_from_microphone()