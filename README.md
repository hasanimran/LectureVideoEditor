# Lecture Video Editor

A Python tool that automatically shortens recorded lectures by detecting sections containing speech and removing the gaps between them. It uses **Silero VAD** for voice activity detection and **FFmpeg** to cut and join video clips.

> **Current limitation:** The program detects *speech*, not whether words are meaningful. Sounds like “um,” “uh,” and “ah” may be kept. Whisper-based filler-word removal is a possible future improvement; it is **not implemented** in the current `lecture_editor.py`.

## Requirements

- Windows 10/11
- Python 3.10 (the version used for this project)
- FFmpeg installed and available on PATH
- Internet connection for initial Python package/model downloads
- VS Code (recommended, optional)

## 1. Install Python and FFmpeg

Install Python from <https://www.python.org/downloads/windows/>. During setup, enable **Add Python to PATH**, if offered.

Open **PowerShell** and install FFmpeg:

```powershell
winget install --id Gyan.FFmpeg -e
```

Restart PowerShell/VS Code, then verify:

```powershell
python --version
ffmpeg -version
```

## 2. Open the project

Open your project folder in VS Code, then open **Terminal → New Terminal**. Or navigate there in PowerShell:

```powershell
cd "$HOME\Desktop\LectureVideoEditor"
```

Your folder should contain:

```text
LectureVideoEditor/
├── lecture_editor.py
├── 3_Classes_and_Objects_default.mp4
└── README.md
```

## 3. Install Python dependencies

In the project folder, run:

```powershell
python -m pip install silero-vad numpy torch
```

The current script also imports standard-library modules such as `subprocess`, `tempfile`, `pathlib`, and (if using the WAV workaround below) `wave`; they need no separate installation.

**Audio-loading note (important for this Windows setup):** Some combinations of `torchaudio` and `torchcodec` fail with `WinError 127` when `silero_vad.read_audio()` attempts to decode audio. Because FFmpeg already converts the source to 16 kHz mono, you can read the temporary WAV file directly with Python rather than calling `read_audio()`.

In `lecture_editor.py`, after creating `audio_path` and running FFmpeg to extract the audio, use:

```python
import wave
import numpy as np
import torch

with wave.open(audio_path, "rb") as wav:
    if (wav.getframerate(), wav.getnchannels(), wav.getsampwidth()) != (16000, 1, 2):
        raise ValueError("Expected 16 kHz mono 16-bit PCM WAV")
    frames = wav.readframes(wav.getnframes())

audio = torch.from_numpy(
    np.frombuffer(frames, dtype=np.int16).copy()
).float() / 32768.0
```

Replace the original line `audio = read_audio(audio_path, sampling_rate=16000)` with this block. Ensure FFmpeg extracts audio with `-ac 1 -ar 16000` and WAV PCM 16-bit (as in the existing script).

## 4. Choose input and output filenames

Put your lecture video in the project folder. In `lecture_editor.py`, set:

```python
INPUT = "3_Classes_and_Objects_default.mp4"
OUTPUT = "3_Classes_and_Objects_default_edited.mp4"
```

Change these names for other lectures. The input file must exist; the output file is created after successful processing.

## 5. Adjust silence detection (optional)

Look for the call to `get_speech_timestamps()` and use these **starting values**:

```python
speech = get_speech_timestamps(
    audio,
    model,
    sampling_rate=16000,
    threshold=0.65,
    min_speech_duration_ms=200,
    min_silence_duration_ms=300,
    speech_pad_ms=50,
    return_seconds=True,
)
```

- `threshold=0.65`: higher values require greater confidence before audio is labeled speech; may remove quiet words.
- `min_silence_duration_ms=300`: duration of silence that separates speech regions; it is not a guarantee that exactly 300 ms will be removed.
- `speech_pad_ms=100`: keeps approximately 0.1 seconds of audio before and after detected speech regions.
- `min_speech_duration_ms=200`: very short detected speech events may be discarded.

These values are **experimental**. Check that the editor does not cut off words or useful teaching content.

To estimate how much will be kept before rendering, add this immediately after detecting `speech`:

```python
total_duration = len(audio) / 16000
kept_duration = sum(s["end"] - s["start"] for s in speech)
print(f"Input: {total_duration / 60:.2f} min")
print(f"Estimated output: {kept_duration / 60:.2f} min")
print(f"Estimated removed: {(total_duration - kept_duration) / 60:.2f} min")
print(f"Speech segments: {len(speech)}")
```

The output length can differ slightly because of video frame boundaries and encoding.

## 6. Run the editor

From PowerShell in the project folder:

```powershell
python lecture_editor.py
```

The script will:

1. Extract the source video's audio with FFmpeg.
2. Identify likely speech segments using Silero VAD.
3. Make clips for the detected speech time ranges.
4. Join those clips and save the edited MP4.

When the script completes, look for:

```text
LectureVideoEditor/
├── lecture_editor.py
├── 3_Classes_and_Objects_default.mp4
├── 3_Classes_and_Objects_default_edited.mp4
└── README.md
```

**Keep the original video** until you have watched and checked the edited one. The current script re-encodes clips and may take a while on long lectures.

## Troubleshooting

| Problem | What to do |
|---|---|
| `python` is not recognized | Reopen PowerShell; ensure Python was installed with PATH enabled. Try `py lecture_editor.py`. |
| `ffmpeg` is not recognized | Install FFmpeg, restart the terminal, and run `ffmpeg -version`. |
| `ModuleNotFoundError: silero_vad` | Run `python -m pip install silero-vad`. |
| `Audio I/O ... requires either torchaudio or torchcodec` | Replace `read_audio()` with the `wave`-based reading code in Section 3. |
| `WinError 127` / `libtorchcodec_image.dll` | Use the same `wave` workaround; there is no need to load TorchCodec for extracted PCM WAV audio. |
| `No speech detected` | Verify the input has audible speech. Try a lower `threshold` such as `0.5`. |
| Too little silence removed | Try shorter `min_silence_duration_ms` and less `speech_pad_ms`; review for unwanted cuts. |
| Spoken words are cut off | Increase `speech_pad_ms` (for example to 200–300) or lower the threshold. |
| “Um” / “uh” remains | This is expected with VAD-only editing. Filler recognition requires transcription and more detailed editing logic. |

## Future enhancements

- Optional Whisper transcription and careful removal of isolated filler words
- Preview and approve cuts before export
- Progress indicator and batch processing
- Windows GUI with video selection and adjustable settings

## Note on subtitles

The source lecture may contain subtitle tracks. The current script works with video and audio clips; **do not assume the original subtitles are preserved** in the exported file. Subtitle handling would require additional implementation.
