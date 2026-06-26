import io

import sounddevice as sd
import soundfile as sf
from openai import OpenAI

client = OpenAI(api_key = "APIKEY GOES HERE")

SAMPLE_RATE = 48000
CHANNELS = 1
DEVICE_INDEX = 25

_recording = []
_stream = None


def _callback(indata, frames, time, status):
    if status:
        print(status)
    _recording.append(indata.copy())


def start_recording(device=None):
    """Start recording."""
    global _stream, _recording

    _recording = []

    _stream = sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="float32",
        callback=_callback,
        device=device,
    )

    _stream.start()


def stop_recording_and_transcribe():
    """Stop recording and return the transcription."""
    global _stream

    if _stream is None:
        raise RuntimeError("Recording has not been started.")

    _stream.stop()
    _stream.close()
    _stream = None

    # Join all recorded chunks
    audio = __import__("numpy").concatenate(_recording, axis=0)

    # Write to an in-memory WAV
    wav_buffer = io.BytesIO()
    sf.write(wav_buffer, audio, SAMPLE_RATE, format="WAV")
    wav_buffer.seek(0)
    wav_buffer.name = "recording.wav"

    transcript = client.audio.transcriptions.create(
        model="gpt-4o-transcribe",
        file=wav_buffer,
    )

    #print(transcript.text)

    return transcript.text