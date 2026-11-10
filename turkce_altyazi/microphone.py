"""Ses bloklarını yalnızca bellekte ölçen mikrofon kontrolü."""

import math
import sys


def mic_check(seconds: float, device: int | str | None = None) -> None:
    import numpy as np
    import sounddevice as sd

    if isinstance(device, int) and device < 0:
        raise ValueError("Cihaz numarası negatif olamaz.")
    info = sd.query_devices(device, kind="input")
    rate = int(info["default_samplerate"])
    target_frames = max(1, round(seconds * rate))
    block_frames = max(1, round(rate * 0.1))
    captured = 0
    print(f"Mikrofon: {info['name']} | {rate} Hz | Ctrl+C ile durdur", flush=True)
    with sd.InputStream(device=device, samplerate=rate, channels=1, dtype="float32") as stream:
        while captured < target_frames:
            frames = min(block_frames, target_frames - captured)
            audio, overflowed = stream.read(frames)
            captured += len(audio)
            rms = float(np.sqrt(np.mean(np.square(audio))))
            dbfs = 20 * math.log10(rms) if rms > 0 else -math.inf
            print(f"Yakalanan: {captured / rate:.2f} s | RMS: {rms:.6f} | Seviye: {dbfs:.1f} dBFS", flush=True)
            if overflowed:
                print("Uyarı: Giriş tamponu taştı; bazı ses örnekleri kayboldu.", file=sys.stderr)
    print("Süre doldu; mikrofon serbest bırakıldı.", flush=True)
