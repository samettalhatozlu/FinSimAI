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
<img width="1552" height="872" alt="Ekran Resmi 2025-11-09 15 21 54" src="https://github.com/user-attachments/assets/99ce9481-4d17-4e0f-b9e1-5a93fe041b18" />
<img width="1552" height="872" alt="Ekran Resmi 2025-11-09 15 22 31" src="https://github.com/user-attachments/assets/a5f44634-abf6-4aae-9b8b-f33126f3fa69" />
<img width="1552" height="872" alt="Ekran Resmi 2025-11-09 15 22 38" src="https://github.com/user-attachments/assets/f0011b5b-2003-4772-ba34-3c526a666412" />
<img width="1552" height="872" alt="Ekran Resmi 2025-11-09 15 23 05" src="https://github.com/user-attachments/assets/cb9ed0ac-02a9-4685-afb2-390575f5bad7" />
<img width="1552" height="872" alt="Ekran Resmi 2025-11-09 15 23 27" src="https://github.com/user-attachments/assets/3757b9f3-d9b1-43ef-b157-abaff679cb82" />
<img width="1552" height="872" alt="Ekran Resmi 2025-11-09 15 23 47" src="https://github.com/user-attachments/assets/79cfb77e-3a82-433d-9262-3dd7dbc7f3a3" />
<img width="1552" height="872" alt="Ekran Resmi 2025-11-09 15 25 50" src="https://github.com/user-attachments/assets/15c46ba2-4d19-434e-b42d-4c914a8aa699" />

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
