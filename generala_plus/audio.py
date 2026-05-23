import math
import os
import random
import wave
from array import array
from pathlib import Path

import pygame


SAMPLE_RATE = 44100
MAX_AMPLITUDE = 32767


def project_root():
    return Path(__file__).resolve().parent.parent


def audio_dir():
    return project_root() / "assets" / "audio"


def clamp(value, low=-1.0, high=1.0):
    return max(low, min(high, value))


def env_adsr(t, duration, attack=0.006, decay=0.05, sustain=0.55, release=0.08):
    if t < attack:
        return t / max(attack, 0.001)
    if t < attack + decay:
        k = (t - attack) / max(decay, 0.001)
        return 1.0 + (sustain - 1.0) * k
    if t > duration - release:
        return max(0.0, sustain * (duration - t) / max(release, 0.001))
    return sustain


def write_wav(path, samples):
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = array("h", [int(clamp(sample) * MAX_AMPLITUDE) for sample in samples])
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(pcm.tobytes())


def tone(duration, freqs, volume=0.35, noise=0.0, attack=0.006, decay=0.06, sustain=0.45, release=0.08):
    total = int(duration * SAMPLE_RATE)
    freqs = freqs if isinstance(freqs, (list, tuple)) else [freqs]
    phases = [random.random() * math.tau for _ in freqs]
    samples = []
    for index in range(total):
        t = index / SAMPLE_RATE
        value = 0.0
        for phase, freq in zip(phases, freqs):
            value += math.sin(math.tau * freq * t + phase)
            value += 0.35 * math.sin(math.tau * freq * 2.01 * t + phase * 0.7)
        value /= max(1, len(freqs)) * 1.35
        if noise:
            value += random.uniform(-1, 1) * noise
        samples.append(value * volume * env_adsr(t, duration, attack, decay, sustain, release))
    return samples


def gliss(duration, start, end, volume=0.35, noise=0.0):
    total = int(duration * SAMPLE_RATE)
    phase = random.random() * math.tau
    samples = []
    for index in range(total):
        t = index / SAMPLE_RATE
        k = t / max(duration, 0.001)
        freq = start + (end - start) * k
        phase += math.tau * freq / SAMPLE_RATE
        value = math.sin(phase) + 0.25 * math.sin(phase * 2.03)
        if noise:
            value += random.uniform(-1, 1) * noise
        samples.append(value * volume * env_adsr(t, duration, attack=0.004, decay=0.06, sustain=0.5, release=0.08))
    return samples


def mix(*tracks):
    length = max(len(track) for track in tracks)
    output = [0.0] * length
    for track in tracks:
        for index, sample in enumerate(track):
            output[index] += sample
    peak = max(1.0, max(abs(sample) for sample in output))
    return [sample / peak * 0.92 for sample in output]


def silence(duration):
    return [0.0] * int(duration * SAMPLE_RATE)


def dice_roll_samples():
    total = int(0.72 * SAMPLE_RATE)
    samples = [0.0] * total
    for hit in range(22):
        start = int((hit / 22) ** 1.25 * total)
        length = int(random.uniform(0.025, 0.055) * SAMPLE_RATE)
        pitch = random.uniform(85, 190)
        amp = random.uniform(0.08, 0.22) * (1 - hit / 30)
        click = tone(length / SAMPLE_RATE, [pitch, pitch * 1.5], amp, noise=0.55, attack=0.001, decay=0.02, sustain=0.16, release=0.025)
        for index, sample in enumerate(click):
            pos = start + index
            if pos < total:
                samples[pos] += sample
    return samples


def ambient_loop_samples():
    duration = 8.0
    total = int(duration * SAMPLE_RATE)
    samples = []
    for index in range(total):
        t = index / SAMPLE_RATE
        low = math.sin(math.tau * 44 * t) * 0.07
        velvet = math.sin(math.tau * 88 * t + 0.4) * 0.025
        shimmer = math.sin(math.tau * 523.25 * t + math.sin(t * 0.7) * 0.8) * 0.012
        drift = math.sin(math.tau * 0.09 * t) * 0.4 + 0.6
        noise = random.uniform(-0.006, 0.006)
        samples.append((low + velvet + shimmer + noise) * drift)
    fade = int(0.4 * SAMPLE_RATE)
    for i in range(fade):
        samples[i] *= i / fade
        samples[-i - 1] *= i / fade
    return samples


SOUND_BUILDERS = {
    "ui_click": lambda: tone(0.09, [360, 720], 0.25, noise=0.08, release=0.035),
    "ui_back": lambda: gliss(0.12, 260, 150, 0.2, noise=0.04),
    "ui_denied": lambda: tone(0.16, [120, 92], 0.28, noise=0.04, attack=0.004, sustain=0.35),
    "pause_open": lambda: mix(gliss(0.18, 150, 82, 0.26, noise=0.05), tone(0.16, 240, 0.12)),
    "pause_close": lambda: gliss(0.14, 130, 220, 0.18, noise=0.03),
    "dice_roll": dice_roll_samples,
    "dice_land": lambda: mix(tone(0.12, [92, 148], 0.36, noise=0.4, attack=0.002), tone(0.08, 330, 0.08)),
    "die_hold": lambda: tone(0.08, [540, 810], 0.22, noise=0.05, release=0.025),
    "die_release": lambda: gliss(0.09, 440, 260, 0.2, noise=0.04),
    "release_all": lambda: mix(gliss(0.14, 520, 260, 0.25, noise=0.04), tone(0.11, 180, 0.12)),
    "score": lambda: mix(tone(0.18, [392, 588, 784], 0.28), gliss(0.22, 760, 980, 0.08)),
    "score_special": lambda: mix(tone(0.28, [330, 495, 660], 0.32), gliss(0.3, 680, 1100, 0.14)),
    "generala": lambda: mix(tone(0.62, [196, 392, 587.33], 0.36), gliss(0.58, 720, 1440, 0.18)),
    "tachada": lambda: mix(gliss(0.16, 190, 70, 0.3, noise=0.18), tone(0.08, 60, 0.2, noise=0.2)),
    "card_use": lambda: mix(tone(0.2, [220, 440, 880], 0.26, noise=0.04), gliss(0.2, 500, 860, 0.12)),
    "card_buy": lambda: mix(tone(0.16, [440, 660], 0.24), tone(0.08, 1200, 0.1)),
    "card_renew": lambda: mix(gliss(0.16, 360, 620, 0.2), gliss(0.16, 620, 360, 0.12)),
    "card_discard": lambda: gliss(0.12, 240, 120, 0.24, noise=0.1),
    "coin": lambda: mix(tone(0.14, [760, 1140], 0.22), gliss(0.12, 1200, 1600, 0.08)),
    "attack": lambda: mix(gliss(0.2, 240, 80, 0.34, noise=0.18), tone(0.09, [70, 105], 0.2)),
    "shield": lambda: mix(tone(0.22, [260, 520], 0.24), gliss(0.22, 520, 300, 0.1)),
    "event": lambda: mix(tone(0.28, [146.83, 293.66], 0.28, noise=0.03), gliss(0.32, 330, 660, 0.1)),
    "round_classic": lambda: tone(0.38, [196, 293.66, 392], 0.28, noise=0.02),
    "win": lambda: mix(tone(0.78, [196, 293.66, 392, 587.33], 0.34), gliss(0.7, 660, 1320, 0.14)),
    "ambient_loop": ambient_loop_samples,
}


def ensure_sound_assets():
    folder = audio_dir()
    folder.mkdir(parents=True, exist_ok=True)
    for name, builder in SOUND_BUILDERS.items():
        path = folder / f"{name}.wav"
        if not path.exists() or path.stat().st_size < 64:
            write_wav(path, builder())


class SoundManager:
    def __init__(self):
        self.enabled = True
        self.ready = False
        self.sfx_volume = 0.72
        self.music_volume = 0.22
        self.sounds = {}
        self._init_audio()

    def _init_audio(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1, buffer=512)
            ensure_sound_assets()
            for name in SOUND_BUILDERS:
                path = audio_dir() / f"{name}.wav"
                self.sounds[name] = pygame.mixer.Sound(str(path))
            self.ready = True
            self.apply_volumes()
        except pygame.error:
            self.enabled = False
            self.ready = False

    def apply_volumes(self):
        for name, sound in self.sounds.items():
            if name == "ambient_loop":
                sound.set_volume(self.music_volume if self.enabled else 0)
            else:
                sound.set_volume(self.sfx_volume if self.enabled else 0)

    def play(self, name):
        if not self.enabled or not self.ready:
            return
        sound = self.sounds.get(name)
        if sound:
            sound.play()

    def start_music(self):
        if not self.enabled or not self.ready:
            return
        music = self.sounds.get("ambient_loop")
        if music:
            music.play(loops=-1, fade_ms=900)

    def stop_music(self):
        music = self.sounds.get("ambient_loop")
        if music:
            music.fadeout(500)

    def set_sfx_volume(self, value):
        self.sfx_volume = max(0.0, min(1.0, value))
        self.apply_volumes()

    def set_music_volume(self, value):
        self.music_volume = max(0.0, min(1.0, value))
        self.apply_volumes()

    def toggle_enabled(self):
        self.enabled = not self.enabled
        self.apply_volumes()
        if self.enabled:
            self.start_music()
        else:
            self.stop_music()
