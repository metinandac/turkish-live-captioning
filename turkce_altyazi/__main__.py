"""Komut satırı giriş noktası."""

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m turkce_altyazi",
        description="Türkçe canlı altyazı sistemi — Aşama 00 proje iskeleti.",
    )
    parser.parse_args()
    parser.print_help()


if __name__ == "__main__":
    main()
