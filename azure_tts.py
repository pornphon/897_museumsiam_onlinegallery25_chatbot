import azure.cognitiveservices.speech as speechsdk
import os

# กำหนด key และ region ของ Azure Speech
speech_key = os.getenv("AZURE_SPEECH_KEY")
service_region = os.getenv("AZURE_REGION")

# สร้าง SpeechConfig
speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
speech_config.speech_synthesis_language = "th-TH"  # ภาษาไทย
speech_config.speech_synthesis_voice_name = "th-TH-PremwadeeNeural"  # เสียงตัวอย่าง

# สร้าง AudioOutputConfig แบบ Stream
stream = speechsdk.audio.AudioOutputStream.create_push_stream()
audio_config = speechsdk.audio.AudioConfig(stream=stream)

# สร้าง SpeechSynthesizer
synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

# ฟังก์ชันรับข้อมูลจาก stream แล้วเขียนลงไฟล์
class WavWriter:
    def __init__(self, filename):
        self.file = open(filename, 'wb')

    def write(self, buffer: memoryview):
        self.file.write(buffer)

    def close(self):
        self.file.close()

# เริ่มเขียน stream
wav_writer = WavWriter("output_stream.wav")

def stream_receiver(buffer: memoryview):
    wav_writer.write(buffer)

stream.set_on_audio_stream_received(stream_receiver)

# สั่งให้ TTS ทำงาน
text = "ยินดีต้อนรับสู่บริการแปลงข้อความเป็นเสียงของ Microsoft Azure"
result = synthesizer.speak_text_async(text).get()

# ตรวจสอบสถานะการสร้างเสียง
if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
    print("✅ สร้างเสียงสำเร็จ")
elif result.reason == speechsdk.ResultReason.Canceled:
    cancellation_details = result.cancellation_details
    print(f"❌ ยกเลิก: {cancellation_details.reason}")
    if cancellation_details.reason == speechsdk.CancellationReason.Error:
        print(f"รายละเอียด: {cancellation_details.error_details}")

wav_writer.close()
