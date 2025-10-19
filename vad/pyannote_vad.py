import os
import torch
from pyannote.audio import Model
from pyannote.audio.pipelines import VoiceActivityDetection

from audio_utils import save_audio_to_file
# from client import Client
from vad.vad_interface import VADInterface

from typing import List, Any

from ray import serve


@serve.deployment(
    ray_actor_options={"num_cpus": 1}
)
class PyannoteVAD(VADInterface):

    def __init__(self, **kwargs):
        model_name = kwargs.get("model_name", "pyannote/segmentation")
        auth_token = os.environ.get("PYANNOTE_AUTH_TOKEN")

        if not auth_token:
            auth_token = kwargs.get("auth_token")

        if auth_token is None:
            raise ValueError("Missing auth token for pyannote")

        pyannote_args = kwargs.get("pyannote_args",
                                   {"onset": 0.5, "offset": 0.5, "min_duration_on": 0.3, "min_duration_off": 0.3})

        self.model = Model.from_pretrained(model_name, use_auth_token=auth_token)
        self.model.to(torch.device("cpu"))
        self.vad_pipeline = VoiceActivityDetection(segmentation=self.model)
        self.vad_pipeline.instantiate(pyannote_args)

    async def detect_activity(self, client) -> List[Any]:
        filepath = await save_audio_to_file(client.scratch_buffer, client.get_file_name())
        vad_results = self.vad_pipeline(filepath)
        os.remove(filepath)
        vad_segments = []
        if len(vad_results) > 0:
            vad_segments = [
                {"start": segment.start, "end": segment.end, "confidence": 1.0} for segment in
                vad_results.itersegments()
            ]

        return vad_segments
