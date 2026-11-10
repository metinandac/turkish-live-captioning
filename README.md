# Türkçe Canlı Altyazı Sistemi

Ses ve görüntü destekli, konuşmacı ayrıştırmalı Türkçe canlı altyazı
üreten yerel bir masaüstü uygulaması geliştirmeyi amaçlayan bitirme projesi.

Şu an yalnızca **Aşama 00: Python proje iskeleti** hazırdır. Komut satırı
yardımı Python standart kütüphanesiyle çalışır; harici çalışma zamanı
bağımlılığı yoktur. Model, mikrofon, kamera ve arayüz henüz eklenmemiştir.

## Windows PowerShell ile çalıştırma

Python 3.10 veya üzeri gerekir. PowerShell'i repo kökünde açın:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m turkce_altyazi --help
```

Bu yol sanal ortamı etkinleştirmeyi veya PowerShell yürütme politikasını
değiştirmeyi gerektirmez. Yardım metni görüntülenmeli ve komut başarıyla
sonlanmalıdır. Repo kökünde doğrudan da çalıştırabilirsiniz:

```powershell
python -m turkce_altyazi --help
```

`python` komutu bulunamıyorsa ve Windows Python başlatıcısı kuruluysa
ilk komutta `python` yerine `py -3` kullanabilirsiniz.

`pyproject.toml` paket bilgilerini içerir. Repo kökünden çalıştırmak için
paketi kurmak veya internetten bağımlılık indirmek gerekmez.
