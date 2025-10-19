"""
Simple connectivity test for the transcription service.
Tests if the WebSocket server is running and accepting connections.
"""
import asyncio
import websockets
import json


async def test_connectivity(uri="ws://localhost:8000/"):
    """Test basic WebSocket connectivity"""
    try:
        print(f"Attempting to connect to {uri}...")
        async with websockets.connect(uri) as websocket:
            print("✓ Connected successfully!")

            # Send a config message to test communication
            config_message = {
                "type": "config",
                "data": {
                    "language": "en",
                    "processing_strategy": "silence_at_the_end_of_chunk"
                }
            }

            print("Sending config message...")
            await websocket.send(json.dumps(config_message))
            print("✓ Config message sent successfully!")

            print("\n✓ Connectivity test passed!")
            print("Server is running and accepting connections.")

    except ConnectionRefusedError:
        print("✗ Connection refused. Is the server running?")
        print("Start the server with: uv run serve run serve_config.yaml")
    except Exception as e:
        print(f"✗ Connection failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_connectivity())
