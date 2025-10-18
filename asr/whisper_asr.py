from asr.asr_interface import ASRInterface
from transformers import pipeline
from audio_utils import save_audio_to_file

import os
from typing import Dict, Any


# from client import Client


class WhisperASR(ASRInterface):

    def __init__(self, **kwargs):
        model_name = kwargs.get("model_name", "openai/whisper-large-v3")
        self.asr_pipeline = pipeline("automatic-speech-recognition", model=model_name)

    async def transcribe(self, client) -> Dict[str, Any]:
        filepath = await save_audio_to_file(client.scratch_buffer, client.get_file_name())

        if client.config["language"] is not None:
            output = self.asr_pipeline(filepath, generate_kwargs={"language": client.config["language"]})["text"]
        else:
            output = self.asr_pipeline(filepath)["text"]
        os.remove(filepath)

        result = {
            "language": "UNSUPPORTED_BY_HUGGINGFACE_WHISPER",
            "language_probability": None,
            "text": output.strip(),
            "words": "UNSUPPORTED_BY_HUGGINGFACE_WHISPER",
        }
        return result
