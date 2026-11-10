"""Komut satırı giriş noktası."""

import argparse
from pathlib import Path
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m turkce_altyazi",
        description="Türkçe altyazı araçları.",
    )
    commands = parser.add_subparsers(dest="command")
    transcribe = commands.add_parser("transcribe", help="WAV dosyasını Türkçe metne dönüştür")
    transcribe.add_argument("wav", type=Path, help="Türkçe konuşma içeren WAV dosyası")
    transcribe.add_argument("--model", default="small", help="Çok dilli Whisper modeli (varsayılan: small)")
    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        return
    if not args.wav.is_file():
        parser.error(f"WAV dosyası bulunamadı: {args.wav}")
    if args.wav.suffix.lower() != ".wav":
        parser.error("Lütfen .wav uzantılı bir ses dosyası seçin.")
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        parser.exit(1, "Hata: faster-whisper yüklenemedi. Kurulum için: python -m pip install -e .\n")
    try:
        print(f"Model yükleniyor: {args.model} (CPU, int8). İlk kullanımda indirilir.", file=sys.stderr)
        model = WhisperModel(args.model, device="cpu", compute_type="int8")
        segments, _ = model.transcribe(str(args.wav), language="tr", task="transcribe", beam_size=5)
        for segment in segments:
            print(f"[{segment.start:.3f} --> {segment.end:.3f}] {segment.text.strip()}", flush=True)
    except Exception as exc:
        parser.exit(1, f"Hata: Transkripsiyon tamamlanamadı: {exc}\n")


if __name__ == "__main__":
    main()
