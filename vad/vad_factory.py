from vad.pyannote_vad import PyannoteVAD
from vad.vad_interface import VADInterface


class VADFactory:

    @staticmethod
    def create_vad_pipeline(type, **kwargs) -> VADInterface:
        if type == "pyannote":
            return PyannoteVAD(**kwargs)
        else:
            raise ValueError(f"Unknown vad type :{type}")
