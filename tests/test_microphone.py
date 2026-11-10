"""Mikrofon akışının süre ve kesinti durumunda kapanma kontrolleri."""

import io
import unittest
from unittest.mock import MagicMock, patch

import numpy as np

from turkce_altyazi.microphone import mic_check


class MicrophoneTests(unittest.TestCase):
    def make_backend(self):
        backend = MagicMock()
        backend.query_devices.return_value = {"name": "Test mikrofonu", "default_samplerate": 1000}
        context = backend.InputStream.return_value
        stream = context.__enter__.return_value
        stream.read.side_effect = lambda frames: (np.full((frames, 1), 0.5, dtype=np.float32), False)
        return backend, context, stream

    def test_duration_level_and_release(self):
        backend, context, stream = self.make_backend()
        with patch.dict("sys.modules", {"sounddevice": backend}), patch("sys.stdout", new_callable=io.StringIO) as output:
            mic_check(0.25, 2)
        self.assertEqual([call.args[0] for call in stream.read.call_args_list], [100, 100, 50])
        self.assertIn("Yakalanan: 0.25 s", output.getvalue())
        self.assertIn("RMS: 0.500000", output.getvalue())
        self.assertIn("-6.0 dBFS", output.getvalue())
        context.__exit__.assert_called_once_with(None, None, None)
        backend.query_devices.assert_called_once_with(2, kind="input")

    def test_interrupt_releases_stream(self):
        backend, context, stream = self.make_backend()
        stream.read.side_effect = KeyboardInterrupt
        with patch.dict("sys.modules", {"sounddevice": backend}), patch("sys.stdout", new_callable=io.StringIO):
            with self.assertRaises(KeyboardInterrupt):
                mic_check(5)
        self.assertIs(context.__exit__.call_args.args[0], KeyboardInterrupt)

    def test_read_error_releases_stream(self):
        backend, context, stream = self.make_backend()
        stream.read.side_effect = RuntimeError("device disconnected")
        with patch.dict("sys.modules", {"sounddevice": backend}), patch("sys.stdout", new_callable=io.StringIO):
            with self.assertRaises(RuntimeError):
                mic_check(5)
        self.assertIs(context.__exit__.call_args.args[0], RuntimeError)


if __name__ == "__main__":
    unittest.main()
