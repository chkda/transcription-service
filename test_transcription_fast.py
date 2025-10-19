"""
Faster transcription test - sends larger chunks to trigger processing sooner
"""
import asyncio
import websockets
import json
import sys
from pathlib import Path
from pydub import AudioSegment


async def test_transcription(audio_file_path: str, uri="ws://localhost:8000/", language="en"):
    """Test transcription with larger chunks"""
    audio_path = Path(audio_file_path)

    if not audio_path.exists():
        print(f"✗ File not found: {audio_file_path}")
        return

    print(f"Loading audio from: {audio_path}")

    try:
        # Load and convert audio
        audio = AudioSegment.from_file(audio_file_path)

        print(f"Original duration: {len(audio) / 1000:.2f} seconds")

        # Convert to required format
        audio = audio.set_frame_rate(16000)
        audio = audio.set_channels(1)
        audio = audio.set_sample_width(2)

        audio_data = audio.raw_data

        print(f"Converted audio: {len(audio_data)} bytes")
        print(f"Duration: {len(audio_data) / (16000 * 2):.2f} seconds")

    except Exception as e:
        print(f"✗ Failed to load audio: {e}")
        return

    try:
        print(f"\nConnecting to {uri}...")
        # Increase ping/pong timeout to prevent keepalive errors during slow processing
        async with websockets.connect(
                uri,
                ping_interval=20,  # Send ping every 20 seconds
                ping_timeout=60,  # Wait up to 60 seconds for pong
                close_timeout=10  # Wait 10 seconds when closing
        ) as websocket:
            print("✓ Connected")

            # Send config
            config_message = {
                "type": "config",
                "data": {
                    "language": language,
                    "processing_strategy": "silence_at_the_end_of_chunk",
                    "processing_args": {
                        "chunk_length_seconds": 3,
                        "chunk_offset_seconds": 0.1
                    }
                }
            }

            await websocket.send(json.dumps(config_message))
            print("Config sent")

            # Use LARGER chunks (1 second instead of 0.25 seconds)
            # This ensures we accumulate 3 seconds faster
            chunk_size = 32000  # 1 second of audio (16000 Hz * 2 bytes)

            total_chunks = (len(audio_data) + chunk_size - 1) // chunk_size

            print(f"\nSending {total_chunks} chunks (1 second each)...")

            transcriptions = []
            all_audio_sent = asyncio.Event()

            async def send_audio():
                for i in range(0, len(audio_data), chunk_size):
                    chunk = audio_data[i:i + chunk_size]
                    await websocket.send(chunk)
                    chunk_num = i // chunk_size + 1
                    print(f"  Chunk {chunk_num}/{total_chunks} sent ({len(chunk)} bytes)")
                    # Simulate real-time: 1 second of audio sent over 1 second
                    await asyncio.sleep(1.0)  # Real-time delay

                print(f"✓ All audio sent")
                all_audio_sent.set()

            async def receive_responses():
                last_response_time = asyncio.get_event_loop().time()

                while True:
                    try:
                        # Increase timeout for slow CPU processing
                        response = await asyncio.wait_for(websocket.recv(), timeout=20.0)
                        last_response_time = asyncio.get_event_loop().time()

                        result = json.loads(response)

                        print(f"\n{'=' * 60}")
                        print(f"TRANSCRIPTION RECEIVED:")
                        print(f"{'=' * 60}")

                        text = result.get('text', '')
                        print(f"\nText: {text}")
                        print(f"\nLanguage: {result.get('language', 'N/A')}")
                        print(f"Processing time: {result.get('processing_time', 0):.2f}s")
                        print(f"Word count: {len(result.get('words', []))}")

                        if text.strip() == '':
                            print("\n⚠ Empty text received!")

                        transcriptions.append(result)

                    except asyncio.TimeoutError:
                        # If all audio is sent and we haven't received anything in 20s, exit
                        if all_audio_sent.is_set():
                            print("\nNo more responses - timeout after all audio sent")
                            break
                        else:
                            # Still sending, keep waiting
                            print("\nStill waiting for responses...")
                            continue

                return transcriptions

            # Run concurrently
            send_task = asyncio.create_task(send_audio())
            recv_task = asyncio.create_task(receive_responses())

            # Wait for both tasks
            results = await recv_task
            await send_task

            print(f"\n{'=' * 60}")
            print(f"SUMMARY")
            print(f"{'=' * 60}")
            print(f"Total responses: {len(results)}")
            print(f"Non-empty: {sum(1 for r in results if r.get('text', '').strip())}")

            # Print all transcription texts combined
            if results:
                all_text = ' '.join(r.get('text', '') for r in results if r.get('text', '').strip())
                if all_text:
                    print(f"\n{'=' * 60}")
                    print(f"FULL TRANSCRIPTION:")
                    print(f"{'=' * 60}")
                    print(all_text)
                    print(f"{'=' * 60}")

            if results and any(r.get('text', '').strip() for r in results):
                print("\n✓ SUCCESS!")
            else:
                print("\n✗ No valid transcriptions")
                print("\nCheck server logs for:")
                print("  - 'Transcription: ...' messages")
                print("  - VAD detection results")
                print("  - Any errors")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_transcription_fast.py <audio_file> [language]")
        sys.exit(1)

    audio_file = sys.argv[1]
    language = sys.argv[2] if len(sys.argv) > 2 else "en"

    asyncio.run(test_transcription(audio_file, language=language))
