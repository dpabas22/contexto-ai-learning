"""Tests for the jingles. Run:  pytest -q test_sounds.py"""
import io
import struct
import wave

import sounds


def read(wav_bytes):
    with wave.open(io.BytesIO(wav_bytes), "rb") as handle:
        frames = handle.readframes(handle.getnframes())
        info = (handle.getnchannels(), handle.getsampwidth(), handle.getframerate(),
                handle.getnframes() / handle.getframerate())
    samples = struct.unpack("<" + "h" * (len(frames) // 2), frames)
    return info, samples


def test_celebration_is_a_valid_short_wav():
    (channels, width, rate, seconds), _ = read(sounds.celebration_jingle())
    assert (channels, width, rate) == (1, 2, sounds.SAMPLE_RATE)
    assert 1.5 < seconds < 4.0


def test_encouragement_is_shorter_and_valid():
    (channels, width, rate, seconds), _ = read(sounds.encouragement_jingle())
    assert (channels, width, rate) == (1, 2, sounds.SAMPLE_RATE)
    assert 0.8 < seconds < 2.0


def test_sounds_are_audible_but_not_loud():
    for jingle in (sounds.celebration_jingle(), sounds.encouragement_jingle()):
        _, samples = read(jingle)
        peak = max(abs(s) for s in samples)
        assert 0.05 * 32767 < peak < 0.45 * 32767      # not silent, not harsh


def test_sounds_start_and_end_softly():
    _, samples = read(sounds.celebration_jingle())
    assert abs(samples[0]) < 500 and abs(samples[-1]) < 500    # no clicks


def test_same_input_gives_same_sound():
    assert sounds.celebration_jingle() == sounds.celebration_jingle()


def test_button_html_has_no_autoplay_and_keeps_the_label():
    html = sounds.sound_button_html("🎉 ¡Felicidades!", sounds.celebration_jingle(), b"speech")
    assert "autoplay" not in html.lower()
    assert "🎉 ¡Felicidades!" in html and "onclick" in html
    assert 'id="habla"' in html and "base64," in html


def test_button_html_works_without_speech():
    html = sounds.sound_button_html("x", sounds.encouragement_jingle(), None)
    assert 'id="habla"' not in html and 'id="musica"' in html
