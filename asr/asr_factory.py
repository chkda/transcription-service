from asr.asr_interface import ASRInterface
from asr.faster_whisper_asr import FasterWhisperASR
from asr.whisper_asr import WhisperASR


class ASRFactory:

    @staticmethod
    def create_asr_pipeline(type: str, **kwargs) -> ASRInterface:
        if type == "whisper":
            return WhisperASR(**kwargs)
        elif type == "faster_whisper":
            return FasterWhisperASR(**kwargs)
        else:
            raise ValueError(f"Unknown ASR pipeline type: {type}")
