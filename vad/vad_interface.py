from typing import List, Any

from client import Client


class VADInterface:

    async def detect_activity(self, client: Client) -> List[Any]:
        raise NotImplementedError("Method should be implemented by subclasses")
