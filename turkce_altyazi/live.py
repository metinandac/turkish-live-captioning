"""Bellekte örtüşen pencerelerle terminal altyazısı."""

from collections import deque
from dataclasses import dataclass
import queue
import re
import threading
import time

import numpy as np

RATE = 16000


@dataclass
class Word:
    start: float
    end: float
    text: str
    first_seen: float


def normalized(text):
    return re.sub(r"[^\w]", "", text.casefold())


class Subtitles:
    """Son iki saniyeyi geçici tut; kesinleşen zaman aralığını tekrar yazma."""

    def __init__(self, emit):
        self.emit = emit
        self.pending = []
        self.history = deque(maxlen=40)
        self.committed_end = 0.0

    def update(self, words, window_start, window_end, now, final=False):
        # Pencere dışına çıkacak son hipotezi kaybetmeden kesinleştir.
        expired = [w for w in self.pending if w.end <= window_start]
        self.commit(expired, now)
        current = []
        for start, end, text in words:
            if not text.strip() or (start + end) / 2 <= self.committed_end:
                continue
            # Aynı sınır kelimesinin küçük zaman damgası kaymalarını bastır.
            if any(normalized(text) == normalized(w.text) and
                   min(end, w.end) - max(start, w.start) > 0 for w in self.history):
                continue
            seen = next((w.first_seen for w in self.pending
                         if normalized(w.text) == normalized(text) and abs(w.start - start) < 1), now)
            current.append(Word(start, end, text, seen))
        cutoff = window_end if final else window_end - 2.0
        ready = [w for w in current if w.end <= cutoff]
        self.commit(ready, now)
        self.pending = [w for w in current if w.end > cutoff]
        self.emit("temporary", self.pending, now)

    def commit(self, words, now):
        if words:
            self.emit("final", words, now)
            self.committed_end = max(self.committed_end, words[-1].end)
            self.history.extend(words)


class WindowProcessor:
    def __init__(self, model, emit, clock=time.monotonic, origin=None):
        self.model = model
        self.subtitles = Subtitles(emit)
        self.clock = clock
        self.origin = clock() if origin is None else origin
        self.audio = np.empty(0, dtype=np.float32)
        self.offset = 0
        self.next_end = 2 * RATE
        self.total = 0
        self.last_end = 0

    def feed(self, block):
        self.audio = np.concatenate((self.audio, block))
        self.total += len(block)
        while self.total >= self.next_end:
            self.process(self.next_end)
            self.next_end += 2 * RATE

    def process(self, end, final=False):
        start = max(0, end - 6 * RATE)
        audio = self.audio[start - self.offset:end - self.offset].copy()
        words = []
        if len(audio) and float(np.sqrt(np.mean(audio ** 2))) >= 0.0001:
            segments, _ = self.model.transcribe(
                audio, language="tr", task="transcribe", beam_size=5,
                word_timestamps=True, vad_filter=True,
                vad_parameters={"min_silence_duration_ms": 300},
                condition_on_previous_text=False,
            )
            for segment in segments:
                for word in segment.words or []:
                    words.append((start / RATE + word.start, start / RATE + word.end, word.word))
        self.subtitles.update(words, start / RATE, end / RATE,
                              self.clock() - self.origin, final)
        self.last_end = end
        # Son kısa pencerenin de çözülebilmesi için altı saniyeyi koru.
        discard_to = max(0, end - 6 * RATE)
        self.audio = self.audio[discard_to - self.offset:]
        self.offset = discard_to

    def finish(self):
        if self.total:
            self.process(self.total, final=True)


class Terminal:
    def __init__(self):
        self.width = 0

    def __call__(self, kind, words, now):
        print("\r" + " " * self.width + "\r", end="", flush=True)
        text = " ".join(w.text.strip() for w in words)
        if kind == "final" and words:
            first = max(w.first_seen for w in words)
            end = words[-1].end
            print(f"[{words[0].start:.2f} --> {end:.2f}] {text} "
                  f"| ilk={first:.2f}s kesin={now:.2f}s "
                  f"ilk_gecikme={max(0, first-end):.2f}s kesin_gecikme={max(0, now-end):.2f}s", flush=True)
            self.width = 0
        else:
            line = f"Geçici: {text}" if text else ""
            print(line, end="", flush=True)
            self.width = len(line)


def live(model_name="small", device=None, seconds=None):
    import sounddevice as sd
    from faster_whisper import WhisperModel

    if isinstance(device, int) and device < 0:
        raise ValueError("Cihaz numarası negatif olamaz.")
    sd.check_input_settings(device=device, channels=1, dtype="float32", samplerate=RATE)
    print(f"Model yükleniyor: {model_name} (CPU, int8). Ctrl+C ile durdur.", flush=True)
    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    blocks = queue.Queue(maxsize=300)  # 30 saniye; sessizce ses kaybetmek yerine hata ver.
    stop = threading.Event()
    errors = queue.SimpleQueue()
    origin = time.monotonic()
    terminal = Terminal()
    processor = WindowProcessor(model, terminal, origin=origin)

    def capture():
        captured = 0
        target = None if seconds is None else max(1, round(seconds * RATE))
        try:
            with sd.InputStream(device=device, samplerate=RATE, channels=1, dtype="float32") as stream:
                while not stop.is_set() and (target is None or captured < target):
                    count = 1600 if target is None else min(1600, target - captured)
                    audio, overflow = stream.read(count)
                    if overflow:
                        raise RuntimeError("Mikrofon tamponu taştı; ses kaybı nedeniyle oturum durduruldu.")
                    try:
                        blocks.put_nowait(audio[:, 0].copy())
                    except queue.Full:
                        raise RuntimeError("Transkripsiyon 30 saniyeden fazla geride kaldı. Daha küçük model kullanın.")
                    captured += len(audio)
        except Exception as exc:
            errors.put(exc)
        finally:
            stop.set()

    worker = threading.Thread(target=capture, name="microphone-capture")
    worker.start()
    try:
        while not stop.is_set() or not blocks.empty():
            if not errors.empty():
                raise errors.get()
            try:
                block = blocks.get(timeout=0.1)
            except queue.Empty:
                continue
            processor.feed(block)
        if not errors.empty():
            raise errors.get()
        processor.finish()
    except KeyboardInterrupt:
        print("\nDurduruluyor; kalan geçici metin kesinleştirilmedi.", flush=True)
    finally:
        stop.set()
        worker.join(timeout=2)
        terminal("temporary", [], time.monotonic() - origin)
        if worker.is_alive():
            raise RuntimeError("Mikrofon iş parçacığı kapanamadı.")
        print("Mikrofon serbest bırakıldı.", flush=True)
