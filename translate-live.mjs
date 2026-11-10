import { AssemblyAI } from "assemblyai";
import recorder from "node-record-lpcm16";
import { Readable } from "stream";

const PROMPT =
  "You are translating a live conversation from English into Spanish.\n" +
  "Earlier in the conversation: {{history_3}}\n\n" +
  "Translate the next turn into natural Spanish. " +
  "Reply with only the Spanish translation of this turn: {{turn}}";

const client = new AssemblyAI({ apiKey: process.env.ASSEMBLYAI_API_KEY });

const transcriber = client.streaming.transcriber({
  sampleRate: 16_000,
  speechModel: "universal-3-6-pro",
  llmGateway: {
    model: "qwen3.5-4b-32k-fast",
    messages: [{ role: "user", content: PROMPT }],
    max_tokens: 400,
  },
});

transcriber.on("turn", (turn) => {
  if (turn.end_of_turn) {
    console.log(`[${turn.turn_order}] EN: ${turn.transcript}`);
  }
});

transcriber.on("llmGatewayResponse", (response) => {
  const translation = response.data.choices[0].message.content.trim();
  console.log(`[${response.turn_order}] ES: ${translation}`);
});

transcriber.on("error", (error) => console.error(`Error: ${error}`));

await transcriber.connect();

const recording = recorder.record({ channels: 1, sampleRate: 16000, audioType: "wav" });
Readable.toWeb(recording.stream()).pipeTo(transcriber.stream());

process.on("SIGINT", async () => {
  recording.stop();
  await transcriber.close();
  process.exit();
});
