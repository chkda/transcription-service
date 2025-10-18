import uuid

from fastapi import WebSocket

from buffering_strategy.buffering_strategy_factory import BufferingStrategyFactory
from typing import Dict, Any


class Client:

    def __init__(self, client_id, sampling_rate, sampling_width):
        self.client_id = client_id
        self.buffer = bytearray()
        self.scratch_buffer = bytearray()
        self.config = {
            "language": None,
            "processing_strategy": "silence_at_the_end_of_chunk",
            "processing_args": {
                "chunk_length_seconds": 3,
                "chunk_offset_seconds": 0.1,
            }
        }
        self.file_counter = 0
        self.total_samples = 0
        self.sampling_rate = sampling_rate
        self.sampling_width = sampling_width
        self.buffering_strategy = BufferingStrategyFactory.create_buffering_strategies(
            self.config["processing_strategy"], self, **self.config["processing_args"])

    def update_config(self, config_data: Dict[str, Any]):
        self.config.update(config_data)
        self.buffering_strategy = BufferingStrategyFactory.create_buffering_strategies(
            self.config["processing_strategy"], self, **self.config["processing_args"])

    def append_audio_data(self, audio_data: bytes):
        self.buffer.extend(audio_data)
        self.total_samples += len(audio_data) / self.sampling_width

    def clear_buffer(self):
        self.buffer.clear()

    def increment_file_counter(self):
        self.file_counter += 1

    def get_file_name(self):
        new_uuid = uuid.uuid4()
        return f"{self.client_id}_{self.file_counter}.wav"

    def process_audio(self, websocket: WebSocket, vad_pipeline, asr_pipeline):
        self.buffering_strategy.process_audio(websocket, vad_pipeline, asr_pipeline)
