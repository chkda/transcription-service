from fastapi import WebSocket


class BufferingStrategyInterface:

    def process_audio(self, web_socket: WebSocket, vad_pipeline, asr_pipeline):
        raise NotImplementedError("This method should be implemented by sub class")
