# FinSim - AI Destekli Monte Carlo Simülasyonu

Dinamik, dosya biçimine duyarlı finansal zaman serisi simülasyon uygulaması. Tarihi fiyat verilerini kullanarak Monte Carlo simülasyonu gerçekleştirir, risk metriklerini hesaplar ve AI destekli analiz raporları oluşturur.

## ✨ Özellikler

- 🔍 **Akıllı Başlık Tespiti**: Karmaşık CSV/Excel yapıları için dayanıklı başlık satırı keşfi
- 📊 **Monte Carlo Simülasyonu**: Pandas/NumPy ile yüksek performanslı fiyat yolu simülasyonu
- 📈 **Risk Analizi**: Kazanma olasılığı, VaR (Value at Risk), CVaR (Conditional Value at Risk) ve güven aralığı hesaplamaları
- 🤖 **AI Destekli Özet**: Ollama LLM ile Türkçe finansal özet (opsiyonel, fallback mekanizması mevcut)
- 📄 **PDF Raporu**: Türkçe karakter uyumlu, histogram ve yüzde bant grafikleri içeren detaylı rapor
- 💬 **FinSim AI Chatbot**: Analiz sonuçlarına dayalı soru-cevap chatbot

## Ekranlar
<img width="1439" height="791" alt="Ekran Resmi 2025-11-07 13 43 43" src="https://github.com/user-attachments/assets/fe8b8920-21e7-419c-b7a9-d6ad801c8597" />
<img width="1439" height="791" alt="Ekran Resmi 2025-11-07 09 25 03 (1)" src="https://github.com/user-attachments/assets/030adb23-97b1-4cb6-abda-316274657e82" />
<img width="1439" height="791" alt="Ekran Resmi 2025-11-07 09 25 03" src="https://github.com/user-attachments/assets/9b643d10-4598-48ec-9e36-f1ef7685133c" />
<img width="1552" height="872" alt="Ekran Resmi 2025-11-07 09 22 26" src="https://github.com/user-attachments/assets/9acf8ce7-d4f9-49a5-8fe7-d24fe3591404" />
<img width="1552" height="872" alt="Ekran Resmi 2025-11-07 09 21 30 (1)" src="https://github.com/user-attachments/assets/077e3da7-831a-4c23-abfb-50f47de7dd28" />
<img width="1552" height="872" alt="Ekran Resmi 2025-11-07 09 21 30" src="https://github.com/user-attachments/assets/64ce5a93-7cff-4db7-b1e5-11ef21ca205e" />

## Kurulum

### Gereksinimler
- Python 3.8+
- pip

### Adımlar

1. Projeyi klonlayın:
```bash
git clone https://github.com/samettalhatozlu/simAi.git
cd simAi
```

2. Sanal ortam oluşturun ve aktifleştirin:
```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows için: .venv\Scripts\activate
```

3. Bağımlılıkları yükleyin:
```bash
pip install -U pip
pip install -r requirements.txt
```

### Gereksinimler

- `streamlit` - Web arayüzü
- `pandas` - Veri işleme
- `numpy` - Sayısal hesaplamalar
- `openpyxl` - Excel dosya desteği
- `altair` - İnteraktif grafikler
- `matplotlib` - Grafik oluşturma
- `reportlab` - PDF rapor oluşturma
- `langchain-ollama` - AI özet desteği (opsiyonel)

## Kullanım

### Uygulamayı Başlatma

```bash
source .venv/bin/activate  # Windows için: .venv\Scripts\activate
streamlit run app.py
```

Tarayıcınızda otomatik olarak açılacak arayüzde şu adımları izleyin:

1. **Dosya Yükleme**: CSV/XLS/XLSX formatında tarihsel fiyat verisi içeren dosyanızı yükleyin
2. **Parametre Onayı**: AI önerilerini doğrulayın (başlık satırı indeksi, tarih ve fiyat sütunları)
3. **Simülasyon Ayarları**: Simülasyon periyodu ve senaryo sayısını seçin
4. **Analiz**: Analizi başlatın ve sonuçları görüntüleyin
5. **AI Yorumu**: Opsiyonel olarak Ollama ile AI destekli özet oluşturun
6. **PDF Raporu**: Detaylı PDF raporunu oluşturup indirin
7. **Chatbot**: FinSim AI Chatbot ile analiz sonuçları hakkında sorular sorun

## Yapılandırma

### Türkçe PDF Desteği

PDF raporlarında Türkçe karakterlerin düzgün görüntülenmesi için TTF font dosyası gerekir. Uygulama aşağıdaki konumlardan otomatik olarak font arayacaktır:

- `./fonts/DejaVuSans.ttf`
- `./src/fonts/DejaVuSans.ttf`
- `/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf` (Linux)
- `/Library/Fonts/DejaVuSans.ttf` (macOS)
- `/Library/Fonts/Arial Unicode.ttf` (macOS)

**Öneri**: Proje kök dizinine `fonts/DejaVuSans.ttf` dosyasını yerleştirin.

### Ollama AI Desteği (Opsiyonel)

AI özet ve chatbot özelliklerini kullanmak için Ollama kurulumu gereklidir:

1. [Ollama](https://ollama.ai/) kurulumunu yapın
2. Modeli indirin:
```bash
ollama pull qwen2.5:7b-instruct
```

Ollama kurulu değilse uygulama deterministik özet ve kural tabanlı chatbot yanıtları kullanacaktır.

## Görselleştirmeler

- **Dağılım Grafiği (Histogram)**: Senaryoların bitiş fiyatı dağılımını gösterir
- **Fiyat Yolu Bant Grafiği**: Medyan, %25/%75 ve %5/%95 bantlarını gösteren okunabilir grafik

## Mimari

- `app.py`: Streamlit arayüzü, durum yönetimi, grafikler, PDF çıktısı
- `src/data_inspector.py`: Başlık satırı keşfi, tarih/fiyat sütun önerileri
- `src/simulation_engine.py`: Getiri hesabı, Monte Carlo simülasyonu, sonuç analizleri
- `src/analysis_pipeline.py`: Veri inceleme ve simülasyon başlatma fonksiyonları

## Notlar

- Uygulama "agentsiz" çalışır. LLM zorunlu değildir.
- "AI Yorumunu Oluştur" özelliği Ollama varsa LLM kullanır, yoksa deterministik özet üretir.
- Chatbot da aynı stratejiyi izler: LLM varsa kullanır, yoksa metrik tabanlı yanıtlar verir.

## Sorun Giderme

### PDF'de Türkçe karakterler bozuksa
`fonts/DejaVuSans.ttf` dosyasını proje kök dizinine ekleyin ve tekrar deneyin.

### Tarih/fiyat sütunları görünmüyorsa
Parametre onay ekranında manuel seçim yapın ve başlık satırı indeksini düzeltin.

### Grafikler boş çıkıyorsa
Seçili fiyat sütununda sayısal veri olduğundan emin olun.

### Ollama bağlantı hatası
Ollama servisinin çalıştığından emin olun veya AI özelliklerini kullanmadan devam edin.

## Lisans

Bu proje [MIT License](LICENSE) altında lisanslanmıştır.

## Yazar

**Samet Talha Tozlu**

- GitHub: [@samettalhatozlu](https://github.com/samettalhatozlu)
- LinkedIn: [samettalhatozlu](https://www.linkedin.com/in/samettalhatozlu)

## Dipnot

- [Streamlit](https://streamlit.io/) - Web arayüzü framework'ü
- [Pandas](https://pandas.pydata.org/) - Veri analizi kütüphanesi
- [NumPy](https://numpy.org/) - Sayısal hesaplama kütüphanesi
- [Ollama](https://ollama.ai/) - Yerel LLM desteği
