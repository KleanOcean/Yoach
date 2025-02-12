## pip install --upgrade google-genai==0.2.2 ##
import asyncio
import json
import os
import websockets
from google import genai
import base64

# Load API key from environment
os.environ['GOOGLE_API_KEY'] = 'AIzaSyDhqIOtKs_aOYFhWbYLpamiJolpzHudyig'
MODEL = "gemini-2.0-flash-exp"  # use your model ID

client = genai.Client(
  http_options={
    'api_version': 'v1alpha',
  }
)

async def gemini_session_handler(client_websocket: websockets.WebSocketServerProtocol):
    """Handles the interaction with Gemini API within a websocket session.

    Args:
        client_websocket: The websocket connection to the client.
    """
    try:
        config_message = await client_websocket.recv()
        print(f"Received config message: {config_message}")
        config_data = json.loads(config_message)
        config = config_data.get("setup", {})
        print(f"Using config: {config}")

        async with client.aio.live.connect(model=MODEL, config=config) as session:
            print("Connected to Gemini API")

            async def send_to_gemini():
                """Sends messages from the client websocket to the Gemini API."""
                try:
                    async for message in client_websocket:
                        try:
                            data = json.loads(message)
                            print(f"Received message from client: {data.keys()}")
                            
                            if "realtime_input" in data:
                                for chunk in data["realtime_input"]["media_chunks"]:
                                    try:
                                        print(f"Processing chunk type: {chunk['mime_type']}")
                                        payload = {
                                            "mime_type": chunk["mime_type"],
                                            "data": chunk["data"]
                                        }
                                        print(f"Attempting to send payload to Gemini: {payload['mime_type']}")
                                        try:
                                            # Use named argument 'input' as required by the API
                                            await session.send(input=payload)
                                            print(f"Successfully sent {chunk['mime_type']} chunk to Gemini")
                                        except TypeError as te:
                                            print(f"TypeError when sending to Gemini: {te}")
                                            print(f"Payload type: {type(payload)}")
                                        except Exception as e:
                                            print(f"Failed to send to Gemini: {type(e).__name__}: {str(e)}")
                                    except Exception as chunk_error:
                                        print(f"Error processing chunk: {chunk_error}")
                                        
                        except json.JSONDecodeError as je:
                            print(f"JSON decode error: {je}")
                        except Exception as e:
                            print(f"Error processing message: {type(e).__name__}: {str(e)}")
                            print(f"Message that caused error: {message}")
                except Exception as e:
                    print(f"Error in send_to_gemini outer loop: {type(e).__name__}: {str(e)}")
                finally:
                    print("send_to_gemini closed")

            async def receive_from_gemini():
                """Receives responses from the Gemini API and forwards them to the client, looping until turn is complete."""
                try:
                    while True:
                        try:
                            print("receiving from gemini")
                            async for response in session.receive():
                                #first_response = True
                                print(f"response: {response}")
                                if response.server_content is None:
                                    print(f'Unhandled server message! - {response}')
                                    continue

                                model_turn = response.server_content.model_turn
                                if model_turn:
                                    for part in model_turn.parts:
                                        print(f"part: {part}")
                                        if hasattr(part, 'text') and part.text is not None:
                                            #print(f"text: {part.text}")
                                            await client_websocket.send(json.dumps({"text": part.text}))
                                        elif hasattr(part, 'inline_data') and part.inline_data is not None:
                                            # if first_response:
                                            print("audio mime_type:", part.inline_data.mime_type)
                                                #first_response = False
                                            base64_audio = base64.b64encode(part.inline_data.data).decode('utf-8')
                                            await client_websocket.send(json.dumps({
                                                "audio": base64_audio,
                                            }))
                                            print("audio received")

                                if response.server_content.turn_complete:
                                    print('\n<Turn complete>')
                        except websockets.exceptions.ConnectionClosedOK:
                            print("Client connection closed normally (receive)")
                            break  # Exit the loop if the connection is closed
                        except Exception as e:
                            print(f"Error receiving from Gemini: {e}")
                            break # exit the lo

                except Exception as e:
                      print(f"Error receiving from Gemini: {e}")
                finally:
                      print("Gemini connection closed (receive)")


            # Start send loop
            send_task = asyncio.create_task(send_to_gemini())
            # Launch receive loop as a background task
            receive_task = asyncio.create_task(receive_from_gemini())
            await asyncio.gather(send_task, receive_task)


    except Exception as e:
        print(f"Error in Gemini session: {e}")
    finally:
        print("Gemini session closed.")


async def main() -> None:
    async with websockets.serve(gemini_session_handler, "localhost", 9082):
        print("Running websocket server localhost:9082...")
        await asyncio.Future()  # Keep the server running indefinitely


if __name__ == "__main__":
    asyncio.run(main())