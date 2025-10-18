from buffering_strategy.buffering_strategies import SilenceAtEndOfChunk
from buffering_strategy.buffering_strategy_interface import BufferingStrategyInterface
from client import Client


class BufferingStrategyFactory:

    @staticmethod
    def create_buffering_strategies(type: str, client: Client, **kwargs) -> BufferingStrategyInterface:
        if type == "silence_at_the_end_of_chunk":
            return SilenceAtEndOfChunk(client, **kwargs)
        else:
            raise ValueError(f"Unsupported buffering strategy type:{type}")
