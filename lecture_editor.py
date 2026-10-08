import subprocess
import tempfile
import wave
import numpy as np
import torch
from pathlib import Path
from silero_vad import (
    load_silero_vad,
    read_audio,
    get_speech_timestamps,
)

INPUT = "2_Review_C++_Advanced_default.mp4"
OUTPUT = "2_Review_C++_Advanced_edited.mp4"

with tempfile.TemporaryDirectory() as tmp:
    audio_path = str(Path(tmp) / "audio.wav")

    # Extract audio for speech detection
    subprocess.run([
        "ffmpeg", "-y", "-i", INPUT,
        "-vn", "-ac", "1", "-ar", "16000",
        audio_path
    ], check=True)


    model = load_silero_vad()

    with wave.open(audio_path, "rb") as wav:
        sample_rate = wav.getframerate()
        channels = wav.getnchannels()
        sample_width = wav.getsampwidth()
        frames = wav.readframes(wav.getnframes())

    if sample_rate != 16000 or channels != 1 or sample_width != 2:
        raise ValueError("Expected 16 kHz mono 16-bit PCM audio")

    audio = torch.from_numpy(
        np.frombuffer(frames, dtype=np.int16).copy()
    ).float() / 32768.0

    speech = get_speech_timestamps(
    audio,
    model,
    sampling_rate=16000,
    threshold=0.65,
    min_speech_duration_ms=200,
    min_silence_duration_ms=300,
    speech_pad_ms=50,
    return_seconds=True
    )

    if not speech:
        raise RuntimeError("No speech detected")

    # Split the original video into speech clips
    clips = []
    for i, segment in enumerate(speech):
        clip = str(Path(tmp) / f"clip_{i:04d}.mp4")
        subprocess.run([
            "ffmpeg", "-y",
            "-ss", str(segment["start"]),
            "-to", str(segment["end"]),
            "-i", INPUT,
            "-c:v", "libx264",
            "-c:a", "aac",
            clip
        ], check=True)
        clips.append(clip)

    # Join clips
    concat_file = Path(tmp) / "clips.txt"
    concat_file.write_text(
        "".join(
            f"file '{Path(c).name}'\n"
            for c in clips
        )
    )

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c", "copy", OUTPUT
    ], check=True)

print("Edited video saved:", OUTPUT)