import asyncio
import os
import time
import json

from fastapi import WebSocket
from ray.serve.handle import DeploymentHandle

from asr.asr_interface import ASRInterface
from buffering_strategy.buffering_strategy_interface import BufferingStrategyInterface

import logging

# from client import Client
from vad.vad_interface import VADInterface

logger = logging.getLogger("ray.serve")
logger.setLevel(logging.DEBUG)


class SilenceAtEndOfChunk(BufferingStrategyInterface):

    def __init__(self, client, **kwargs):
        self.client = client

        self.chunk_length_seconds = os.environ.get("BUFFERING_CHUNK_LENGTH_SECONDS")
        if not self.chunk_length_seconds:
            self.chunk_length_seconds = kwargs.get("chunk_length_seconds")
        self.chunk_length_seconds = float(self.chunk_length_seconds)

        self.chunk_offset_seconds = os.environ.get("BUFFERING_OFFSET_SECONDS")
        if not self.chunk_offset_seconds:
            self.chunk_offset_seconds = kwargs.get("chunk_offset_seconds")
        self.chunk_offset_seconds = float(self.chunk_offset_seconds)

        self.error_if_not_realtime = os.environ.get("ERROR_IF_NOT_REALTIME")
        if not self.error_if_not_realtime:
            self.error_if_not_realtime = kwargs.get("error_if_not_realtime", False)

        self.processing_flag = False

    def process_audio(self, web_socket: WebSocket, vad_handle: DeploymentHandle, asr_handle: DeploymentHandle):
        chunk_length_in_bytes = self.chunk_length_seconds * self.client.sampling_rate * self.client.sampling_width

        if len(self.client.buffer) > chunk_length_in_bytes:
            if self.processing_flag:
                logger.warning("Tried processing a new chunk while previous one is still being processed")
            else:
                self.client.scratch_buffer += self.client.buffer
                self.client.buffer.clear()
                self.processing_flag = True
                asyncio.create_task(self.process_audio_async(web_socket, vad_handle, asr_handle))

    async def process_audio_async(self, websocket: WebSocket, vad_handle: DeploymentHandle,
                                  asr_handle: DeploymentHandle):
        start = time.time()
        vad_results = await vad_handle.detect_activity.remote(client=self.client)

        if len(vad_results) == 0:
            self.client.buffer.clear()
            self.client.scratch_buffer.clear()
            self.processing_flag = False
            return

        last_segment_should_end_before = ((len(self.client.scratch_buffer) / (
                self.client.sampling_rate * self.client.sampling_width)) - self.chunk_offset_seconds)

        logger.info(f"Last segment end: {vad_results[-1]['end']}")
        logger.info(f"Should end before: {last_segment_should_end_before}")
        logger.info(f"Condition met: {vad_results[-1]['end'] < last_segment_should_end_before}")

        # if vad_results[-1]["end"] < last_segment_should_end_before:
        transcription = await asr_handle.transcribe.remote(client=self.client)
        self.client.increment_file_counter()
        if transcription["text"] != "":
            end = time.time()
            transcription["processing_time"] = end - start
            print(transcription["text"])
            json_transcription = json.dumps(transcription)
            await websocket.send_text(json_transcription)
        self.client.scratch_buffer.clear()

        self.processing_flag = False
