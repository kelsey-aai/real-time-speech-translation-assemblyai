# Real-time speech translation with AssemblyAI

Stream English from your microphone to [Universal-3.6 Pro Realtime](https://www.assemblyai.com/blog/universal-3-6-pro-realtime) (`universal-3-6-pro`) and get a Spanish translation of every final turn back on the same WebSocket. The translation runs server-side through the `llm_gateway` connection parameter: the server sends each final turn to [LLM Gateway](https://www.assemblyai.com/products/llm-gateway) with your prompt and returns the result as an `LLMGatewayResponse` message. There's no second API to call.

This is the companion repo for the tutorial: [Real-time speech translation: how it works and how to build it](https://www.assemblyai.com/blog/real-time-speech-translation). For every `llm_gateway` field and the prompt template variables, see the [real-time translation docs](https://www.assemblyai.com/docs/streaming/real-time-translation).

## What's in the repo

| File | What it does |
|------|--------------|
| `translate_live.py` | Streams the microphone, prints partials as a live English caption, and prints the Spanish translation of each final turn |
| `translate_live_tts.py` | The same script plus the optional speech step: a worker thread speaks each translation over one long-lived AssemblyAI TTS session (`aai-antonioluis`, Spanish) and writes raw PCM to `translated.pcm` |
| `translate-live.mjs` | The same build with the JavaScript SDK |
| `requirements.txt` | `assemblyai` (1.9.1) and `pyaudio` |
| `package.json` | `assemblyai` and `node-record-lpcm16` for the JavaScript version |
| `.env.example` | The one environment variable the scripts read |

## Quick start

Requires Python 3.11 or later, a microphone and an AssemblyAI API key. Translation runs on LLM Gateway, which is billed on tokens and isn't part of the free tier, so add a card to your account before you run it.

On macOS, PyAudio needs PortAudio first:

```bash
brew install portaudio
```

Then:

```bash
git clone https://github.com/kelsey-aai/real-time-speech-translation-assemblyai
cd real-time-speech-translation-assemblyai

python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env and set ASSEMBLYAI_API_KEY, then load it into your shell:
set -a; source .env; set +a
```

The scripts read `ASSEMBLYAI_API_KEY` from the environment, so `export ASSEMBLYAI_API_KEY=<your-key>` works too.

### Captions only

```bash
python translate_live.py
```

Speak a few sentences in English, then press Ctrl+C to stop. Each final turn prints its source line, and its translation lands a moment later:

```text
[0] EN: Hi, I'd like to make a reservation at a restaurant.
[0] ES: ¡Hola! Me gustaría hacer una reserva en un restaurante.
```

### Captions plus spoken translation

```bash
python translate_live_tts.py
```

Press Ctrl+C when you're done, then play the Spanish audio (raw 24 kHz 16-bit mono PCM, no header):

```bash
ffplay -f s16le -ar 24000 -ac 1 translated.pcm
```

### JavaScript

Requires Node.js 18 or later and SoX for microphone capture (`brew install sox` on macOS).

```bash
npm install
export ASSEMBLYAI_API_KEY=<your-key>
node translate-live.mjs
```

## Configuration notes

- **Prompt:** `{{turn}}` and `{{history_3}}` are filled in by the server for every final turn. Leave them exactly as written. To change the target language, change both mentions of Spanish in `PROMPT`.
- **History:** `{{history_1}}` to `{{history_10}}` carry up to the last ten final transcripts whose translation has completed. Three turns is a good start for conversations. Each turn of history adds prompt tokens.
- **Model:** `qwen3.5-4b-32k-fast` is a small, fast model so the translation keeps pace with speech. Any model from the [LLM Gateway models list](https://www.assemblyai.com/docs/llm-gateway/available-models) works.
- **Partials vs finals:** only final turns are translated. Partials stay in the spoken language. Match each translation to its source by `turn_order`, since translations for short back-to-back turns can arrive out of order.
- **Missing translations:** if the gateway call fails or times out, no `LLMGatewayResponse` is sent for that turn. Keep showing the source text.
- **TTS languages:** AssemblyAI-TTS-1 speaks English, Spanish, French, German, Italian and Portuguese. TTS takes the language as a full English name (`spanish`). The TTS session closes after two minutes with no frames in either direction.

## Learn more

- [Real-time speech translation: how it works and how to build it](https://www.assemblyai.com/blog/real-time-speech-translation)
- [Real-time translation docs](https://www.assemblyai.com/docs/streaming/real-time-translation)
- [Turn detection](https://www.assemblyai.com/docs/streaming/turn-detection)
- [AssemblyAI text-to-speech](https://www.assemblyai.com/products/text-to-speech)
