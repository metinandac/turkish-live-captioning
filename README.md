# Türkçe Canlı Altyazı Sistemi

Ses ve görüntü destekli, konuşmacı ayrıştırmalı Türkçe canlı altyazı
üreten yerel bir masaüstü uygulaması geliştirmeyi amaçlayan bitirme projesi.

**Aşama 01**, faster-whisper ile WAV dosyasından Türkçe transkripsiyon ekler.
İşlem CPU üzerinde int8 ile çalışır. Mikrofon, kamera ve arayüz henüz eklenmemiştir.

PyAV bağımlılığı `av<19` ile sınırlandırılır: faster-whisper 1.2.1'in kullandığı
`metadata_errors` argümanı PyAV 19'da kaldırılmıştır. Kurulum komutu uyumlu
PyAV sürümünü de seçer.

## Windows PowerShell ile çalıştırma

Python 3.10 veya üzeri gerekir. PowerShell'i repo kökünde açın:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m turkce_altyazi --help
.\.venv\Scripts\python.exe -m turkce_altyazi transcribe "ornek.wav"
```

Bu yol sanal ortamı etkinleştirmeyi veya PowerShell yürütme politikasını
değiştirmeyi gerektirmez. Yardım metni görüntülenmeli ve komut başarıyla
sonlanmalıdır. Repo kökünde doğrudan da çalıştırabilirsiniz:

```powershell
python -m turkce_altyazi --help
```

`python` komutu bulunamıyorsa ve Windows Python başlatıcısı kuruluysa
ilk komutta `python` yerine `py -3` kullanabilirsiniz.

## WAV transkripsiyonu

Kurulumdan sonra sanal ortamı etkinleştirerek çalıştırabilirsiniz:

```powershell
.\.venv\Scripts\Activate.ps1
python -m turkce_altyazi transcribe "ornek.wav"
```

Etkinleştirme betiği engellenirse yukarıdaki doğrudan Python yolunu kullanın.
Varsayılan çok dilli model `small`dır. İlk çalıştırmada Hugging Face'den
indirilir; internet bağlantısı ve önbellek için disk alanı gerekir. Sonraki
çalıştırmalar aynı model önbelleğini kullanır. Model kullanıcı önbelleğinde
tutulur ve Git'e eklenmez. CUDA gerekmez. PyAV, FFmpeg kütüphanelerini
beraberinde getirir; ayrıca FFmpeg kurmanız gerekmez.
Kaynak: [faster-whisper belgeleri](https://github.com/SYSTRAN/faster-whisper).

Daha küçük bir çok dilli model için:

```powershell
python -m turkce_altyazi transcribe "ornek.wav" --model tiny
```

Dil `tr`, görev `transcribe` olarak sabittir. Her satır
`[başlangıç --> bitiş] metin` biçimindedir; zamanlar dosya başlangıcına göre
saniye cinsindendir. Otomatik tanıma hataları olabilir. Var olmayan dosya,
model erişimi veya ses çözümleme hatası başarısız çıkış koduyla bildirilir.
WAV dosyalarını, özel kayıtları, model ağırlıklarını ve sanal ortamı Git'e
eklemeyin; ilgili yollar `.gitignore` ile dışlanır.
