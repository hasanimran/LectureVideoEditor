# Lecture Video Editor

A Python-based tool for shortening recorded lectures by detecting speech with **Silero VAD** and using **FFmpeg** to keep the speaking sections. Designed for lecture recordings where you want to remove long pauses without manually cutting the video.

> \*\*Current status:\*\* The current `lecture\_editor.py` uses Silero VAD to identify speech and FFmpeg to join the retained clips. \*\*Faster-Whisper is installed as an optional dependency for future transcription/filler-word detection; installing it alone does not make the current script remove “um,” “uh,” or “ah.”\*\*

## Requirements

* Windows 10/11 (instructions below; Python can also run on other systems)
* Python 3.10 or later with `pip`
* [FFmpeg](https://ffmpeg.org/download.html) available on your `PATH`
* Enough free disk space for temporary audio and video clips

## Installation (Windows PowerShell)

1. Clone or download the repository:

```powershell
   git clone https://github.com/hasanimran/LectureVideoEditor.git
   cd LectureVideoEditor
   ```

2. Optional but recommended: create a virtual environment:

```powershell
   python -m venv .venv
   .\\.venv\\Scripts\\Activate.ps1
   ```

   If PowerShell blocks activation, you can skip activation and use `.\\.venv\\Scripts\\python.exe` in place of `python` in the commands below.

3. Install Python packages:

```powershell
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

4. Install FFmpeg if necessary:

```powershell
   winget install --id Gyan.FFmpeg -e
   ```

   Restart the terminal and verify:

```powershell
   ffmpeg -version
   python -c "import torch; from silero\_vad import load\_silero\_vad; from faster\_whisper import WhisperModel; print('Dependencies imported successfully')"
   ```

## Run the editor

1. Place your lecture video in the project directory (or provide a path to it).
2. Open `lecture\_editor.py` and set the filenames near the top:

```python
   INPUT = "3\_Classes\_and\_Objects\_default.mp4"
   OUTPUT = "3\_Classes\_and\_Objects\_default\_edited.mp4"
   ```

3. Run from the repository folder:

```powershell
   python lecture\_editor.py
   ```

4. Review the exported MP4, especially around cuts. Keep the original until you confirm the edit.

## Speech-detection settings

The current script uses `get\_speech\_timestamps()` from Silero VAD. Example settings:

```python
speech = get\_speech\_timestamps(
    audio,
    model,
    sampling\_rate=16000,
    threshold=0.65,
    min\_speech\_duration\_ms=200,
    min\_silence\_duration\_ms=300,
    speech\_pad\_ms=50,
    return\_seconds=True,
)
```

|Setting|Meaning|
|-|-|
|`threshold`|Confidence required to mark a segment as speech; increasing it may miss quiet speech.|
|`min\_speech\_duration\_ms`|Minimum detected speech length to retain as a speech event.|
|`min\_silence\_duration\_ms`|Minimum gap that can separate speech segments.|
|`speech\_pad\_ms`|Extra audio/video time kept around speech to avoid clipping words.|
|`return\_seconds=True`|Returns segment boundaries in seconds for FFmpeg.|

Tune these carefully: aggressively removing pauses can cut off sentence beginnings, quiet words, or useful on-screen activity.

## How it works

1. FFmpeg extracts 16 kHz mono WAV audio from the video.
2. Silero VAD finds timestamps likely to contain speech.
3. FFmpeg exports the corresponding video intervals.
4. FFmpeg concatenates the clips into an edited MP4.

**Limitations:** VAD detects speech-like audio, not whether speech is meaningful. It can retain filler sounds and student voices, and it can occasionally miss quiet speech. The sample workflow also re-encodes segments, which can take time. Existing subtitle tracks may not be preserved by the current FFmpeg commands.

## Troubleshooting

**`ffmpeg` not recognized** — install FFmpeg, restart PowerShell/VS Code, and check `ffmpeg -version`.

**`ImportError: Audio I/O ... torchaudio or torchcodec`** — Silero's `read\_audio()` needs an audio backend. You can either install one with `python -m pip install "silero-vad\[audio]"`, or bypass it by reading FFmpeg's WAV output directly with Python's built-in `wave` module and converting the PCM samples to a 1-D `torch.float32` tensor.

**`WinError 127` / `libtorchcodec\_image.dll`** — this can be due to an incompatible TorchCodec dependency. For the FFmpeg-extracted **16 kHz mono 16-bit PCM** WAV file, reading it with `wave` avoids TorchCodec entirely:

```python
import wave
import numpy as np
import torch

with wave.open(audio\_path, "rb") as wav:
    if (wav.getframerate(), wav.getnchannels(), wav.getsampwidth()) != (16000, 1, 2):
        raise ValueError("Expected 16 kHz mono 16-bit PCM")
    frames = wav.readframes(wav.getnframes())

audio = torch.from\_numpy(
    np.frombuffer(frames, dtype=np.int16).copy()
).float() / 32768.0
```

Replace only `audio = read\_audio(...)` with the code above; keep the rest of your speech-detection pipeline.

**Output barely shorter than input** — try adjusting silence duration, threshold, and padding. Note that fillers such as “um” and “uh” are typically detected as speech and won't be removed by silence detection alone.

## Planned improvements

* \[ ] Faster-Whisper transcription and timestamp-assisted detection of isolated filler words
* \[ ] Preview and approve suggested cuts
* \[ ] Batch processing and configurable input/output paths
* \[ ] Desktop UI and progress reporting

## Privacy and files

Processing takes place on your own computer. Do not commit lecture recordings, edited MP4s, extracted WAVs, or temporary files to GitHub without permission. Add video/audio formats and `.venv/` to `.gitignore`.

## License

See the repository's `LICENSE` file.

