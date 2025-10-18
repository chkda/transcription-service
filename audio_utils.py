import wave
import os


async def save_audio_to_file(audio_data: bytes, filename: str, audio_dir: str = "audio_file",
                             audio_format: str = "wave") -> str:
    os.makedirs(audio_dir, exist_ok=True)
    filepath = os.path.join(audio_dir, filename)

    with wave.open(filepath, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        wav_file.writeframes(audio_data)

    return filepath
