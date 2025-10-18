from typing import Dict, Any

from client import Client


class ASRInterface:
    async def transcribe(self, client: Client) -> Dict[str, Any]:
        raise NotImplementedError("This method should be implemented by sub classes")
