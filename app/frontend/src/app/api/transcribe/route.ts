import { NextResponse } from "next/server";

type ElevenLabsTranscription = {
  text?: unknown;
  transcript?: unknown;
};

export const runtime = "nodejs";

export async function POST(request: Request) {
  const apiKey = process.env.ELEVENLABS_API_KEY;
  if (!apiKey) {
    return NextResponse.json(
      {
        error: "Missing ElevenLabs API key. Set ELEVENLABS_API_KEY in frontend environment.",
      },
      { status: 500 },
    );
  }

  const inputForm = await request.formData();
  const audio = inputForm.get("audio");
  if (!(audio instanceof File)) {
    return NextResponse.json({ error: "audio file is required" }, { status: 400 });
  }

  const elevenForm = new FormData();
  elevenForm.append("file", audio, audio.name || "dictation.webm");
  elevenForm.append("model_id", "scribe_v1");
  elevenForm.append("language_code", "sl");

  const elevenResponse = await fetch("https://api.elevenlabs.io/v1/speech-to-text", {
    method: "POST",
    headers: {
      "xi-api-key": apiKey,
    },
    body: elevenForm,
  });

  if (!elevenResponse.ok) {
    const errorText = await elevenResponse.text();
    return NextResponse.json(
      { error: `ElevenLabs transcription failed: ${errorText}` },
      { status: elevenResponse.status },
    );
  }

  const data = (await elevenResponse.json()) as ElevenLabsTranscription;
  const text =
    typeof data.text === "string"
      ? data.text
      : typeof data.transcript === "string"
        ? data.transcript
        : "";

  return NextResponse.json({ text: text.trim() });
}
