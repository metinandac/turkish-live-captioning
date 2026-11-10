# Türkçe Canlı Altyazı Sistemi

Ses ve görüntü destekli, konuşmacı ayrıştırmalı Türkçe canlı altyazı
üreten yerel bir masaüstü uygulaması geliştirmeyi amaçlayan bitirme projesi.

**Aşama 01**, faster-whisper ile WAV dosyasından Türkçe transkripsiyon ekler.
İşlem CPU üzerinde int8 ile çalışır. **Aşama 02**, bağımsız mikrofon kontrolü
ekler. Kamera ve arayüz henüz eklenmemiştir.

**Aşama 03**, mikrofon sesinden terminalde geçici ve kesin Türkçe altyazı üretir.

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

## Mikrofon kontrolü (Aşama 02)

Repo kökünde PowerShell ile kurulumu güncelleyin ve varsayılan mikrofonu deneyin:

```powershell
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m turkce_altyazi mic-check --seconds 5
```

Komut yaklaşık 100 ms'lik mono ses bloklarının toplam süresini, RMS seviyesini
ve dBFS değerini gösterir. Sessizlikte `-inf` görülebilir; konuşurken RMS'nin
artması ve dBFS'nin sıfıra yaklaşması beklenir. Bu değerler kalibre edilmiş
ortam ses basıncı ölçümü değildir. Ses bellekte ölçülüp bırakılır; diske
kaydedilmez ve Whisper'a gönderilmez.

Cihaz listesindeki giriş kanalı olan bir cihazın numarasını veya adını seçin:

```powershell
.\.venv\Scripts\python.exe -m sounddevice
.\.venv\Scripts\python.exe -m turkce_altyazi mic-check --seconds 5 --device 1
```

Numara örnektir; kendi listenize göre değiştirin. Windows Ayarlar > Gizlilik
ve güvenlik > Mikrofon bölümünden mikrofon erişimini ve masaüstü uygulama
erişimini açın. Geçersiz cihaz veya erişim sorunu anlaşılır hata ve başarısız
çıkış kodu üretir. Süre dolunca veya Ctrl+C ile akış kapanır. Kontrol için
komutu yeniden başlatıp mikrofonun tekrar açıldığını doğrulayın; ayrıca uzun
bir `--seconds 30` denemesini Ctrl+C ile durdurun.

Windows pip kurulumu PortAudio'yu beraberinde getirir:
[sounddevice kurulum belgeleri](https://github.com/spatialaudio/python-sounddevice/blob/master/doc/installation.rst).

## Canlı Türkçe altyazı (Aşama 03)

Repo kökünde Windows PowerShell / VS Code terminalinde:

```powershell
.\.venv\Scripts\python.exe -m turkce_altyazi live --model small
```

Varsayılan mikrofon kullanılır. `--device` ile cihaz numarası veya adı seçilebilir.
Süreli bir deneme için:

```powershell
.\.venv\Scripts\python.exe -m turkce_altyazi live --model small --seconds 20
```

İlk model yüklemesi mikrofon açılmadan yapılır. Akış 16 kHz mono ses alır;
cihaz bu biçimi desteklemiyorsa anlaşılır hata verilir. Mikrofon ayrı iş
parçacığında yaklaşık 100 ms'lik blokları okur; CPU/int8 transkripsiyonu ses
alımını bekletmez. Ses yalnızca bellekte tutulur; dosyaya yazılmaz.

İki saniyede bir, en fazla altı saniyelik pencere çözülür (tam pencerelerde
dört saniye örtüşme). `Geçici:` satırı aynı terminal satırında yenilenir.
Son iki saniyedeki kelimeler geçicidir; daha eski kelimeler kesin satıra
alınır. Kesinleşmiş zaman aralıkları ve aynı zamandaki eşleşen sınır kelimeleri
yeniden yazılmaz; daha sonra gerçekten tekrarlanan sözler korunur. Bu,
zaman tabanlı prototip bir kesinleştirme kuralıdır; tanıma hataları veya büyük
kelime zaman kaymaları olabilir. Çok düşük seviyeli pencereler atlanır;
diğerlerinde VAD sessizliği süzer. Gürültüde yanlış metin üretilebilir.

Kesin satırlar sesin oturum içindeki başlangıç/bitiş zamanını ve şu değerleri
gösterir (saniye):

- `ilk`: satırdaki bütün kelimelerin ilk hipotezlerinin görüldüğü zamanların en büyüğü.
- `kesin`: satırın kesin olarak yazıldığı zaman.
- `ilk_gecikme` ve `kesin_gecikme`: bu zamanların satırın ses bitişine farkı.

Her kelime için ilk hipotez zamanı bellekte korunur. Ses zamanları örnek
sayısıyla, görünme/kesinleşme zamanları monoton saatle aynı oturum başlangıcına
göre tutulur. Donanımın giriş gecikmesi ayrıca kalibre edilmez. Değişen bir
kelimenin ilk zamanı yeni hipotezle başlar. İlk görünüm bazen doğrudan kesin
satır olabilir. Bunlar kelime hata oranı veya doğruluk ölçümü değildir.

İşlem yetişemezse en fazla 30 saniyelik ses kuyruklanır. Kuyruk veya cihaz
tamponu taşarsa ses kaybını gizlemek yerine hata verilip oturum kapatılır;
daha küçük çok dilli `--model base` veya `--model tiny` denenebilir.
Süreli oturum sonunda kalan ses işlenir; bu yüzden son çıktı belirtilen
süreden sonra gelebilir. Ctrl+C mikrofonu kapatır; kalan geçici metin zorla
kesinleştirilmez. Modelin yürüyen CPU çağrısının kesintiyi işlemesi gecikebilir.

Yerel kabul denemesi: birkaç saniye sessiz kalın, Türkçe bir cümle söyleyin,
kısa bir aradan sonra aynı cümleyi yeniden söyleyin. Geçici metnin değişmesini,
her sözün yalnızca bir kez kesinleşmesini ve gerçek tekrarın korunmasını
kontrol edin. Ctrl+C'den sonra komutu yeniden başlatıp cihazın açıldığını doğrulayın.

Otomatik kontroller:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m pip check
```

Model API kaynağı: [faster-whisper transkripsiyon kodu](https://github.com/SYSTRAN/faster-whisper/blob/master/faster_whisper/transcribe.py).
