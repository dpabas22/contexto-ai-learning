"""
sounds.py - short original jingles for the game, made by code.

Nothing here is copied from any song. Each jingle is a few simple notes
(sine waves with a soft start and end), so there are no licensing questions
and no files to download. Sounds only play when the child taps a button,
because browsers block sound that starts by itself.
"""
import base64
import io
import math
import struct
import wave

SAMPLE_RATE = 22050
VOLUME = 0.30            # kept moderate on purpose
FADE_IN = 0.01           # seconds
FADE_OUT = 0.08          # seconds

# note names -> frequency in hertz
C4, E4, G4 = 261.63, 329.63, 392.00
C5, E5, G5 = 523.25, 659.25, 783.99
C6, E6 = 1046.50, 1318.51


def _tone(freqs, seconds, volume):
    """One note (or chord) as a list of samples between -1 and 1."""
    count = int(SAMPLE_RATE * seconds)
    fade_in = max(1, int(SAMPLE_RATE * FADE_IN))
    fade_out = max(1, int(SAMPLE_RATE * FADE_OUT))
    samples = []
    for i in range(count):
        t = i / SAMPLE_RATE
        value = 0.0
        for freq in freqs:
            value += math.sin(2 * math.pi * freq * t)
            value += 0.25 * math.sin(2 * math.pi * 2 * freq * t)   # a little brightness
        value /= max(1, len(freqs)) * 1.25
        envelope = min(1.0, i / fade_in, (count - i) / fade_out)
        samples.append(value * envelope * volume)
    return samples


def make_wav(notes):
    """notes = [(frequencies, seconds), ...]  ->  WAV file as bytes."""
    samples = []
    for freqs, seconds in notes:
        freqs = freqs if isinstance(freqs, (list, tuple)) else [freqs]
        samples.extend(_tone(freqs, seconds, VOLUME))
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(SAMPLE_RATE)
        frames = b"".join(
            struct.pack("<h", int(max(-1.0, min(1.0, s)) * 32767)) for s in samples
        )
        handle.writeframes(frames)
    return buffer.getvalue()


def celebration_jingle():
    """A bright rising fanfare, about 2.3 seconds."""
    return make_wav([
        (C5, 0.14), (E5, 0.14), (G5, 0.14), (C6, 0.22),
        (G5, 0.12), (C6, 0.12),
        ([E5, G5, C6], 0.55),
        ([G5, C6, E6], 0.95),
    ])


def encouragement_jingle():
    """A gentle, warm rising motif, about 1.2 seconds. Soft on purpose."""
    return make_wav([(G4, 0.22), (C5, 0.22), (E5, 0.7)])


def sound_button_html(label, jingle_wav, speech_mp3=None, color="#27ae60"):
    """A big button. Tapping it plays the jingle, then the spoken phrase if there is one."""
    jingle = base64.b64encode(jingle_wav).decode("ascii")
    speech_tag = ""
    if speech_mp3:
        speech = base64.b64encode(speech_mp3).decode("ascii")
        speech_tag = f'<audio id="habla" src="data:audio/mpeg;base64,{speech}"></audio>'
    return f"""
<div style="font-family:sans-serif">
  <audio id="musica" src="data:audio/wav;base64,{jingle}"></audio>
  {speech_tag}
  <button id="boton" aria-label="{label}" onclick="go()"
    style="border:none;color:white;background:{color};font-size:20px;padding:14px 22px;
           border-radius:14px;cursor:pointer;">{label}</button>
</div>
<script>
  const musica = document.getElementById('musica');
  const habla = document.getElementById('habla');
  musica.volume = 0.6;
  if (habla) habla.volume = 0.9;
  function go() {{
    if (habla) {{ habla.pause(); habla.currentTime = 0; }}
    musica.currentTime = 0;
    if (habla) {{ musica.onended = () => habla.play(); }}
    musica.play();
  }}
</script>
"""
