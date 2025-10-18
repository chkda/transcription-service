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
        self.connected_clients = {}

    async def handle_audio(self, client: Client, websocket: WebSocket):
        while True:
            message = await websocket.receive()

            if "bytes" in message.keys():
                client.append_audio_data(message["bytes"])
            elif "text" in message.keys():
                config = json.loads(message["text"])
                if config.get("type") == "config":
                    client.update_config(config["data"])
                    continue
            elif message["type"] == "websocket.disconnect":
                raise WebSocketDisconnect
            else:
                keys_list = list(message.keys())
                logger.debug(
                    f"{type(message)} is not a valid message type. Type is {message['type']}; keys: {json.dumps(keys_list)}")
                logger.error(f"Unexpected message type from {client.client_id}")
            client.process_audio(websocket, self.vad_handle, self.asr_handle)

    @app.websocket("/")
    async def handle_websocket(self, websocket: WebSocket):
        await websocket.accept()

        client_id = str(uuid.uuid4())
        client = Client(client_id, self.sampling_rate, self.samples_width)
        self.connected_clients[client_id] = client

        logger.info(f"Client {client_id} connected")

        try:
            await self.handle_audio(client, websocket)
        except WebSocketDisconnect as e:
            logger.warning(f"Connection with {client_id} closed")
        finally:
            del self.connected_clients[client_id]


entrypoint = TranscriptionServer.bind(FasterWhisperASR.bind(), PyannoteVAD.bind())

if __name__ == "__main__":
    ray.init()
    serve.run(entrypoint, name="transcription-service", route_prefix="/")
