import os
import azure.cognitiveservices.speech as speechsdk
import pyaudio

#tts แบบ streaming
class AudioStreamCallback(speechsdk.audio.PushAudioOutputStreamCallback):
    def __init__(self):
        super().__init__()
        # ตั้งค่า PyAudio
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(format=pyaudio.paInt16,
                                      channels=1,
                                      rate=16000,
                                      output=True)

    def write(self, audio_buffer: memoryview) -> int:
        # แปลง memoryview เป็น bytes ก่อนส่งให้ PyAudio
        audio_data = bytes(audio_buffer)
        self.stream.write(audio_data)
        return len(audio_data)

    def close(self):
        print("Stream closed.")
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()

def text_to_speech_streaming(text):
    # ตั้งค่า Azure Speech SDK
    speech_key = os.getenv("AZURE_SPEECH_KEY")
    service_region = os.getenv("AZURE_REGION")



    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
    speech_config.speech_synthesis_voice_name = "th-TH-NiwatNeural"

    # สร้าง AudioStreamCallback
    callback = AudioStreamCallback()
    stream = speechsdk.audio.PushAudioOutputStream(callback)

    # ตั้งค่า audio output เป็น stream
    audio_output = speechsdk.audio.AudioOutputConfig(stream=stream)
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_output)

    # สร้าง event handler สำหรับการตรวจจับการเสร็จสิ้นการสังเคราะห์เสียง
    def handle_synthesis_result(evt):
        if evt.result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            print("Synthesis completed")
        elif evt.result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = evt.result.cancellation_details
            print(f"Synthesis canceled: {cancellation_details.reason}")

    speech_synthesizer.synthesis_completed.connect(handle_synthesis_result)

    # เริ่มการสร้างเสียงแบบ streaming
    print("Starting TTS streaming...")
    speech_synthesizer.speak_text_async(text).get()

if __name__ == "__main__":
    text_to_speech_streaming("ปัญหานี้เกิดจากการที่ audio_buffer ที่รับมาจาก Azure TTS เป็น memoryview object แต่ PyAudio ต้องการ bytes-like object เช่น bytes หรือ bytearray แทน memoryview")
