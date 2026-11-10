import os

import pyaudio
from assemblyai.streaming.v3 import (
    BeginEvent,
    LLMGatewayResponseEvent,
    RealTimeError,
    RealTimeEvents,
    RealTimeParameters,
    RealTimeTranscriber,
    RealTimeTranscriberOptions,
    TerminationEvent,
    TurnEvent,
)
from assemblyai.streaming.v3.models import LLMGatewayConfig, LLMGatewayMessage

API_KEY = os.environ["ASSEMBLYAI_API_KEY"]
SAMPLE_RATE = 16000
FRAMES_PER_BUFFER = 800  # 50 ms of audio at 16 kHz

# {{history_3}} and {{turn}} are filled in by the server for every final turn.
# Leave them exactly as written.
PROMPT = (
    "You are translating a live conversation from English into Spanish.\n"
    "Earlier in the conversation: {{history_3}}\n\n"
    "Translate the next turn into natural Spanish. "
    "Reply with only the Spanish translation of this turn: {{turn}}"
)

# Final transcripts, keyed by turn_order, so each translation can be
# joined back to the words it came from.
source_turns = {}


def microphone_stream():
    """Yield 16-bit PCM chunks from the default microphone."""
    audio = pyaudio.PyAudio()
    stream = audio.open(
        input=True,
        format=pyaudio.paInt16,
        channels=1,
        rate=SAMPLE_RATE,
        frames_per_buffer=FRAMES_PER_BUFFER,
    )
    try:
        while True:
            yield stream.read(FRAMES_PER_BUFFER, exception_on_overflow=False)
    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()


def on_begin(self, event: BeginEvent):
    print(f"Session started: {event.id}. Start speaking English.\n")


def on_turn(self, event: TurnEvent):
    if not event.end_of_turn:
        # Partial: show it as a live caption in the spoken language.
        print(f"\r  ... {event.transcript}", end="", flush=True)
        return
    source_turns[event.turn_order] = event.transcript
    print(f"\r[{event.turn_order}] EN: {event.transcript}")


def on_llm_response(self, event: LLMGatewayResponseEvent):
    translation = event.data["choices"][0]["message"]["content"].strip()
    print(f"[{event.turn_order}] ES: {translation}\n")


def on_terminated(self, event: TerminationEvent):
    print(f"Session ended: {event.audio_duration_seconds} s of audio processed")


def on_error(self, error: RealTimeError):
    print(f"Error: {error}")


def main():
    client = RealTimeTranscriber(
        RealTimeTranscriberOptions(api_host="streaming.assemblyai.com"),
        api_key=API_KEY,
    )

    client.on(RealTimeEvents.Begin, on_begin)
    client.on(RealTimeEvents.Turn, on_turn)
    client.on(RealTimeEvents.LLMGatewayResponse, on_llm_response)
    client.on(RealTimeEvents.Termination, on_terminated)
    client.on(RealTimeEvents.Error, on_error)

    client.connect(
        RealTimeParameters(
            sample_rate=SAMPLE_RATE,
            speech_model="universal-3-6-pro",
            llm_gateway=LLMGatewayConfig(
                model="qwen3.5-4b-32k-fast",
                messages=[LLMGatewayMessage(role="user", content=PROMPT)],
                max_tokens=400,
            ),
        )
    )

    try:
        client.stream(microphone_stream())
    except KeyboardInterrupt:
        pass
    finally:
        client.disconnect(terminate=True)


if __name__ == "__main__":
    main()
