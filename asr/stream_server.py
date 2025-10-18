import ray
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from ray import serve
from ray.serve.handle import DeploymentHandle

import websockets
import uuid
import json
import asyncio
import logging

from audio_utils import save_audio_to_file
from client import Client
from asr.faster_whisper_asr import FasterWhisperASR
from vad.pyannote_vad import PyannoteVAD

logger = logging.getLogger("ray.serve")
logger.setLevel(logging.DEBUG)
app = FastAPI()


@serve.deployment
@serve.ingress(app)
class TranscriptionServer:

    def __init__(self, asr_handle: DeploymentHandle, vad_handle: DeploymentHandle, sampling_rate=16000,
                 samples_width=2):
        self.sampling_rate = sampling_rate
        self.samples_width = samples_width
        self.asr_handle = asr_handle
        self.vad_handle = vad_handle
