"""Canlı altyazıda örtüşme, gecikme ve pencere kontrolleri."""

import unittest
import io
import threading
import time
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

from turkce_altyazi.live import RATE, Subtitles, WindowProcessor, live


class LiveTests(unittest.TestCase):
    def test_capture_continues_during_inference_and_closes(self):
        state = {"reads": 0, "closed": False, "advanced": False}
        class Stream:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                state["closed"] = True
            def read(self, count):
                time.sleep(0.002)
                state["reads"] += 1
                return np.full((count, 1), 0.1, dtype=np.float32), False
        class Model:
            def transcribe(self, *args, **kwargs):
                before = state["reads"]
                time.sleep(0.04)
                state["advanced"] |= state["reads"] > before
                return iter([]), None
        backend = SimpleNamespace(check_input_settings=lambda **kw: None, InputStream=lambda **kw: Stream())
        whisper = SimpleNamespace(WhisperModel=lambda *args, **kw: Model())
        with patch.dict("sys.modules", {"sounddevice": backend, "faster_whisper": whisper}), patch("sys.stdout", new_callable=io.StringIO):
            live(seconds=3)
        self.assertTrue(state["advanced"])
        self.assertTrue(state["closed"])
        self.assertEqual(state["reads"], 30)
        self.assertFalse(any(t.name == "microphone-capture" for t in threading.enumerate()))

    def test_overlap_is_finalized_once_and_times_are_separate(self):
        events = []
        subtitles = Subtitles(lambda *event: events.append(event))
        phrase = [(0.2, 0.7, "Merhaba"), (1.1, 1.7, "dünya")]
        subtitles.update(phrase, 0, 2, 2.3)
        self.assertEqual(events[-1][0], "temporary")
        subtitles.update(phrase, 0, 4, 4.2)
        subtitles.update(phrase, 0, 6, 6.1)
        finalized = [w for kind, words, _ in events if kind == "final" for w in words]
        self.assertEqual([w.text for w in finalized], ["Merhaba", "dünya"])
        self.assertEqual(finalized[0].first_seen, 2.3)
        self.assertEqual([now for kind, _, now in events if kind == "final"], [4.2])

    def test_boundary_timestamp_jitter_and_later_genuine_repeat(self):
        final = []
        subtitles = Subtitles(lambda kind, words, now: final.extend(words) if kind == "final" else None)
        subtitles.update([(1, 2, "Merhaba")], 0, 4, 4)
        subtitles.update([(1.1, 2.2, "Merhaba"), (3, 3.6, "Merhaba")], 0, 6, 6)
        self.assertEqual([w.start for w in final], [1, 3])

    def test_revised_word_inside_committed_time_is_not_finalized_again(self):
        final = []
        subtitles = Subtitles(lambda kind, words, now: final.extend(words) if kind == "final" else None)
        subtitles.update([(1, 2, "Türkçe")], 0, 4, 4)
        subtitles.update([(1.1, 2.2, "sütçü"), (2.2, 2.8, "altyazı")], 0, 6, 6)
        self.assertEqual([w.text for w in final], ["Türkçe", "altyazı"])

    def test_silence_does_not_invoke_model_or_emit_words(self):
        class Model:
            def transcribe(self, *args, **kwargs):
                raise AssertionError("Sessiz pencere modele gitmemeli")
        events = []
        processor = WindowProcessor(Model(), lambda *event: events.append(event))
        for _ in range(100):
            processor.feed(np.zeros(1600, dtype=np.float32))
        processor.finish()
        self.assertFalse(any(words for _, words, _ in events))
        self.assertLessEqual(len(processor.audio), 6 * RATE)

    def test_overlapping_windows_and_final_partial_window(self):
        lengths = []
        class Model:
            def transcribe(self, audio, **kwargs):
                lengths.append(len(audio))
                self.options = kwargs
                return iter([]), SimpleNamespace()
        model = Model()
        processor = WindowProcessor(model, lambda *args: None)
        for _ in range(85):
            processor.feed(np.full(1600, 0.1, dtype=np.float32))
        processor.finish()
        self.assertEqual(lengths, [2*RATE, 4*RATE, 6*RATE, 6*RATE, 6*RATE])
        self.assertEqual(model.options["language"], "tr")
        self.assertTrue(model.options["word_timestamps"])


if __name__ == "__main__":
    unittest.main()
