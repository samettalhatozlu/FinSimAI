import pandas as pd
import numpy as np
import streamlit as st
import altair as alt
import io
import re
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

try:
    from langchain_ollama import ChatOllama  # type: ignore
except Exception:
    ChatOllama = None  # type: ignore


from src.analysis_pipeline import inspect_uploaded_file, run_full_simulation_analysis


# LLM bağlantısı kontrolü
if ChatOllama is not None:
    try:
        _ = ChatOllama(model="qwen2.5:7b-instruct", temperature=0)
    except Exception:
        pass


def generate_ai_summary_text(results: dict, params: dict) -> str:
    """Türkçe finansal özet üretir. Ollama varsa LLM kullanır, yoksa deterministik özet döner."""
    def fallback() -> str:
        """Ollama yoksa kullanılacak deterministik özet"""
        start = results['start_price']
        avg = results['average_end_price']
        med = results['median_end_price']
        win = results['gain_probability_pct']
        varv = results['var_95_value']
        varp = results['var_95_return_pct']
        cvarv = results['cvar_95_value']
        cvarp = results['cvar_95_return_pct']
        vol = results.get('historical_volatility')

        parts = []
        parts.append(
            f"{params['num_scenarios']} senaryo ve {params['num_periods']} periyot ile Monte Carlo simülasyonu çalıştırıldı."
        )
        parts.append(
            f"Başlangıç fiyatı {start:.2f}; ortalama bitiş {avg:.2f}, medyan {med:.2f}."
        )
        parts.append(f"Kazanma olasılığı %{win:.2f} seviyesinde.")
        parts.append(
            f"%95 VaR {varv:.2f} ( %{varp:.2f} ) ve %95 CVaR {cvarv:.2f} ( %{cvarp:.2f} ) olarak hesaplandı."
        )
        if isinstance(vol, (int, float)):
            parts.append(f"Tarihsel volatilite {vol:.6f} seviyesinde.")
        return " ".join(parts)

    # LLM kullanılabilirse özet üret
    if ChatOllama is None:
        return fallback()
    try:
        llm = ChatOllama(model="qwen2.5:7b-instruct", temperature=0)
        prompt = (
            "Aşağıdaki Monte Carlo sonuçlarına göre, yalnızca Türkçe tek paragraf bir finansal özet yaz. "
            "Riskleri ve olası senaryoları 4-6 cümlede açıkla. Ön-ek, talimat, madde işareti, başlık, meta-yorum verme.\n\n"
            f"Parametreler: senaryo={params['num_scenarios']}, periyot={params['num_periods']}, başlangıç={results['start_price']:.2f}.\n"
            f"Ortalama bitiş={results['average_end_price']:.2f}, medyan={results['median_end_price']:.2f}, kazanma%={results['gain_probability_pct']:.2f}.\n"
            f"VaR95={results['var_95_value']:.2f} ( %{results['var_95_return_pct']:.2f} ), CVaR95={results['cvar_95_value']:.2f} ( %{results['cvar_95_return_pct']:.2f} ), "
            f"volatilite={results.get('historical_volatility', float('nan')):.6f}."
        )
        resp = llm.invoke(prompt)
        text = getattr(resp, "content", None) or (resp if isinstance(resp, str) else None)
        if isinstance(text, str) and text.strip():
            raw = text.strip()
            # Markdown formatını temizle
            lines = []
            for ln in raw.splitlines():
                s = ln.lstrip()
                if s.startswith('#'):
                    s = re.sub(r'^#+\s*', '', s)
                if s.startswith('```'):
                    continue
                lines.append(s)
            cleaned = " ".join([l for l in lines if l])
            return cleaned or fallback()
        return fallback()
    except Exception:
        return fallback()


def _matplotlib_hist_image(end_prices: np.ndarray) -> bytes:
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.hist(end_prices, bins=50, color="#4C78A8")
    ax.set_title("Bitiş Fiyatları Dağılımı")
    ax.set_xlabel("Bitiş Fiyatı")
    ax.set_ylabel("Frekans")
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=180)
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def _matplotlib_paths_image(price_paths: np.ndarray, num_paths: int = 50) -> bytes:
    num_paths = min(num_paths, price_paths.shape[1])
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.plot(price_paths[:, :num_paths], alpha=0.3)
    ax.set_title(f"Örnek Fiyat Yolları ({num_paths} Senaryo)")
    ax.set_xlabel("Periyot")
    ax.set_ylabel("Fiyat")
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=180)
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def _matplotlib_bands_image(price_paths: np.ndarray) -> bytes:
    periods = np.arange(price_paths.shape[0])
    p05 = np.percentile(price_paths, 5, axis=1)
    p25 = np.percentile(price_paths, 25, axis=1)
    p50 = np.percentile(price_paths, 50, axis=1)
    p75 = np.percentile(price_paths, 75, axis=1)
    p95 = np.percentile(price_paths, 95, axis=1)

    fig, ax = plt.subplots(figsize=(6, 3))
    ax.fill_between(periods, p05, p95, color="#4C78A8", alpha=0.2, label="%5-%95")
    ax.fill_between(periods, p25, p75, color="#4C78A8", alpha=0.35, label="%25-%75")
    ax.plot(periods, p50, color="#B279A2", linewidth=2, label="Medyan")
    ax.set_xlabel("Periyot")
    ax.set_ylabel("Fiyat")
    ax.legend(loc="best")
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=180)
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def _get_pdf_styles() -> dict:
    """PDF için Türkçe karakter desteği sağlar"""
    styles = getSampleStyleSheet()
    # Türkçe karakterler için TTF font yolları
    possible_paths = [
        "./fonts/DejaVuSans.ttf",
        "./src/fonts/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/Library/Fonts/DejaVuSans.ttf",
        "/Library/Fonts/Arial Unicode.ttf",
    ]
    chosen_font = None
    for p in possible_paths:
        try:
            with open(p, "rb"):
                chosen_font = p
                break
        except Exception:
            continue
    if chosen_font:
        try:
            pdfmetrics.registerFont(TTFont("DejaVuSans", chosen_font))
            # Tüm PDF stillerine font uygula
            for name in ["Title", "Heading1", "Heading2", "Heading3", "BodyText", "Normal"]:
                if name in styles:
                    styles[name].fontName = "DejaVuSans"
        except Exception:
            pass
    return styles


def build_pdf_report(results: dict, params: dict, ai_summary: str, price_paths: np.ndarray) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = _get_pdf_styles()
    story = []

    story.append(Paragraph("FinSim - AI Destekli Monte Carlo Simülasyonu Raporu", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph("Özet (AI)", styles["Heading2"]))
    story.append(Paragraph(ai_summary.replace("\n", "<br/>"), styles["BodyText"]))
    story.append(Spacer(1, 12))

    stats_html = (
        f"Başlangıç: {results['start_price']:.2f}<br/>"
        f"Ortalama Bitiş: {results['average_end_price']:.2f}<br/>"
        f"Medyan Bitiş: {results['median_end_price']:.2f}<br/>"
        f"Kazanma Olasılığı: %{results['gain_probability_pct']:.2f}<br/>"
        f"VaR 95%: {results['var_95_value']:.2f} ( %{results['var_95_return_pct']:.2f} )<br/>"
        f"CVaR 95%: {results['cvar_95_value']:.2f} ( %{results['cvar_95_return_pct']:.2f} )<br/>"
        f"Volatilite: {results.get('historical_volatility', float('nan')):.6f}<br/>"
        f"Senaryo/Periyot: {params['num_scenarios']} / {params['num_periods']}<br/>"
    )
    story.append(Paragraph("Ana İstatistikler", styles["Heading2"]))
    story.append(Paragraph(stats_html, styles["BodyText"]))
    story.append(Spacer(1, 12))

    # Grafikler ekle
    end_prices = price_paths[-1]
    hist_bytes = _matplotlib_hist_image(end_prices)
    bands_bytes = _matplotlib_bands_image(price_paths)
    story.append(Paragraph("Dağılım Grafiği", styles["Heading2"]))
    story.append(RLImage(io.BytesIO(hist_bytes), width=480, height=240))
    story.append(Spacer(1, 12))
    story.append(Paragraph("Fiyat Yolu Bant Grafiği (Medyan + %25/%75 + %5/%95)", styles["Heading2"]))
    story.append(RLImage(io.BytesIO(bands_bytes), width=480, height=240))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()


# Streamlit arayüzü ve durum yönetimi
st.set_page_config(layout="wide")
st.title("FinSim - AI Destekli Monte Carlo Simülasyonu")

if "current_state" not in st.session_state:
    st.session_state.current_state = "INIT"
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
if "inspection_results" not in st.session_state:
    st.session_state.inspection_results = None
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None
if "dataframe" not in st.session_state:
    st.session_state.dataframe = None
if "price_paths" not in st.session_state:
    st.session_state.price_paths = None


def set_state(state: str) -> None:
    """Uygulama durumunu günceller"""
    st.session_state.current_state = state


# Ana arayüz bileşenleri
if st.session_state.current_state == "INIT":
    st.header("1. Adım: Veri Yükleyin")
    st.markdown(
        "Lütfen analiz etmek istediğiniz Tarihsel Fiyat Verilerini içeren bir CSV veya Excel dosyası yükleyin."
    )

    uploaded_file = st.file_uploader("Finansal Veri Dosyası", type=["csv", "xls", "xlsx"])

    if uploaded_file:
        st.session_state.uploaded_file = uploaded_file
        set_state("INSPECTING")
        st.rerun()

elif st.session_state.current_state == "INSPECTING":
    st.header("1. Adım: Veri Yükleyin")
    st.success(f"Dosya Yüklendi: `{st.session_state.uploaded_file.name}`")

    with st.spinner("Uygulama dosyanızı inceliyor..."):
        # Dosya analizini başlat
        st.session_state.inspection_results = inspect_uploaded_file(
            st.session_state.uploaded_file.name
        )

        if st.session_state.inspection_results.get("error"):
            st.error(st.session_state.inspection_results["error"])
            set_state("INIT")
        else:
            set_state("CONFIRM")
            st.rerun()

elif st.session_state.current_state == "CONFIRM":
    st.header("2. Adım: Simülasyon Parametrelerini Onaylayın")
    st.markdown("Uygulama dosyanızı analiz etti. Lütfen parametreleri doğrulayın.")

    results = st.session_state.inspection_results
    all_cols = results["columns"]

    st.subheader("Veri Önizleme (Dosyanın ilk 20 satırı):")
    st.text(results["file_preview"])

    with st.form("simulation_form"):
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Veri Ayarları (AI Önerileri)")

            header_row_index = st.number_input(
                "Gerçek Başlık Satırı İndeksi:",
                min_value=0,
                value=int(results["suggested_header_row"]),
                help="AI, başlığın bu satırda (0'dan başlayarak) olduğunu tahmin etti. Gerekirse düzeltin.",
            )

            date_col_index = (
                all_cols.index(results["suggested_date_col"]) if results["suggested_date_col"] in all_cols else 0
            )
            date_col = st.selectbox("Tarih Sütunu:", all_cols, index=date_col_index)

            price_col_options = results["suggested_price_cols"] if results["suggested_price_cols"] else all_cols
            price_col = st.selectbox("Fiyat/Getiri Sütunu:", price_col_options)

            try:
                last_price = (
                    pd.to_numeric(st.session_state.dataframe[price_col], errors='coerce').dropna().iloc[-1]
                )
            except Exception:
                last_price = 100.0

            start_price = st.number_input(
                "Simülasyon Başlangıç Fiyatı:", value=float(last_price), format="%.2f"
            )

        with col2:
            st.subheader("Simülasyon Ayarları")
            user_type = st.radio(
                "Kullanıcı Tipi:", ["Bireysel (Basit)", "Kurumsal (Gelişmiş)"], horizontal=True
            )

            if user_type == "Bireysel (Basit)":
                num_periods = st.selectbox(
                    "Simülasyon Süresi:", [21, 63, 126, 252], format_func=lambda x: f"{x} Periyot (Gün/Ay)"
                )
                num_scenarios = 10000
                st.info("Bireysel modda senaryo sayısı 10.000 olarak sabitlenmiştir.")
            else:
                num_periods = st.number_input("Simülasyon Periyodu (Gün/Ay):", value=252)
                num_scenarios = st.number_input(
                    "Senaryo Sayısı:", value=20000, min_value=1000, max_value=100000, step=1000
                )

        submitted = st.form_submit_button("ANALİZİ BAŞLAT")

        if submitted:
            st.session_state.run_params = {
                "header_row_index": int(header_row_index),
                "date_col": date_col,
                "price_col": price_col,
                "start_price": float(start_price),
                "num_periods": int(num_periods),
                "num_scenarios": int(num_scenarios),
            }
            set_state("ANALYZING")
            st.rerun()

elif st.session_state.current_state == "ANALYZING":
    st.header("3. Adım: Analiz Sonuçları")

    with st.spinner("Simülasyon çalışıyor..."):
        params = st.session_state.run_params

        # Monte Carlo simülasyonunu çalıştır
        response = run_full_simulation_analysis(
            date_col=params["date_col"],
            price_col=params["price_col"],
            start_price=params["start_price"],
            num_periods=params["num_periods"],
            num_scenarios=params["num_scenarios"],
            header_row_index=params["header_row_index"],
        )

        st.session_state.analysis_results = response if isinstance(response, dict) else {"error": "Beklenmedik hata oluştu."}

        if st.session_state.analysis_results.get("error"):
            st.error(st.session_state.analysis_results["error"])
            set_state("CONFIRM")
        else:
            set_state("DONE")
            st.rerun()

elif st.session_state.current_state == "DONE":
    st.header("3. Adım: Analiz Sonuçları")
    st.balloons()

    results = st.session_state.analysis_results

    st.subheader(
        f"'{st.session_state.run_params['price_col']}' için {st.session_state.run_params['num_scenarios']} Senaryolu Analiz"
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Kazanma Olasılığı", f"{results['gain_probability_pct']:.2f}%")
    col2.metric("Ortalama Bitiş Fiyatı", f"{results['average_end_price']:.2f}")
    col3.metric("Medyan Bitiş Fiyatı", f"{results['median_end_price']:.2f}")
    col4.metric("Başlangıç Fiyatı", f"{results['start_price']:.2f}")

    st.divider()

    st.subheader("Risk Analizi (En Kötü Senaryolar)")
    col1, col2 = st.columns(2)
    with col1:
        st.error("VaR 95% (En Kötü %5'lik Durum)")
        st.metric("Minimum Değer", f"{results['var_95_value']:.2f}", f"{results['var_95_return_pct']:.2f}% Getiri/Kayıp")
    with col2:
        st.error("CVaR 95% (En Kötü %5'in Ortalaması)")
        st.metric(
            "Beklenen Minimum Değer",
            f"{results['cvar_95_value']:.2f}",
            f"{results['cvar_95_return_pct']:.2f}% Getiri/Kayıp",
        )

    st.subheader("Simülasyon Dağılım Grafiği (Bitiş Fiyatları)")
    price_paths = st.session_state.price_paths
    end_prices = price_paths[-1]
    chart_data = pd.DataFrame({"Bitiş Fiyatları": end_prices})
    hist_chart = (
        alt.Chart(chart_data)
        .mark_bar()
        .encode(
            x=alt.X("Bitiş Fiyatları", bin=alt.Bin(maxbins=100), title="Bitiş Fiyatı"),
            y=alt.Y("count()", title="Senaryo Sayısı"),
            tooltip=[alt.X("Bitiş Fiyatları", bin=alt.Bin(maxbins=100)), "count()"],
        )
        .properties(title=f"{st.session_state.run_params['num_scenarios']} Senaryonun Dağılımı")
        .interactive()
    )
    st.altair_chart(hist_chart, use_container_width=True)

    st.subheader("Fiyat Yolu Bant Grafiği (Median + %25/%75 + %5/%95)")
    periods = np.arange(price_paths.shape[0])
    p05 = np.percentile(price_paths, 5, axis=1)
    p25 = np.percentile(price_paths, 25, axis=1)
    p50 = np.percentile(price_paths, 50, axis=1)
    p75 = np.percentile(price_paths, 75, axis=1)
    p95 = np.percentile(price_paths, 95, axis=1)
    band_df = pd.DataFrame({
        "Periyot": periods,
        "p05": p05,
        "p25": p25,
        "p50": p50,
        "p75": p75,
        "p95": p95,
    })

    base = alt.Chart(band_df).encode(x="Periyot")
    band_95 = base.mark_area(opacity=0.2, color="#4C78A8").encode(y="p05", y2="p95")
    band_50 = base.mark_area(opacity=0.35, color="#4C78A8").encode(y="p25", y2="p75")
    median_line = base.mark_line(color="#B279A2", strokeWidth=2).encode(y="p50")
    band_chart = (band_95 + band_50 + median_line).properties(title="Senaryo Bantları ve Medyan")
    st.altair_chart(band_chart.interactive(), use_container_width=True)

    # AI yorum ve PDF raporu
    st.subheader("AI Yorum ve PDF Raporu")
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("AI Yorumunu Oluştur (Ollama)"):
            params = st.session_state.run_params
            ai_summary = generate_ai_summary_text(results, params)
            st.session_state.ai_summary = ai_summary
            st.success("AI yorumu hazırlandı.")
            st.text_area("AI Özeti", value=ai_summary, height=160)
        elif "ai_summary" in st.session_state and st.session_state.ai_summary:
            st.text_area("AI Özeti", value=st.session_state.ai_summary, height=160)

    with col_b:
        if st.button("PDF Raporu Oluştur"):
            params = st.session_state.run_params
            ai_text = st.session_state.get("ai_summary") or generate_ai_summary_text(results, params)
            pdf_bytes = build_pdf_report(results, params, ai_text, price_paths)
            st.session_state.report_pdf = pdf_bytes
            st.success("PDF raporu hazırlandı.")

        if st.session_state.get("report_pdf"):
            st.download_button(
                label="PDF'yi İndir",
                data=st.session_state.report_pdf,
                file_name="FinSim_AI_Destekli_Monte_Carlo_Simulasyonu.pdf",
                mime="application/pdf",
            )

    # FinSim AI Chatbot
    st.subheader("FinSim AI Chatbot")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Sohbet geçmişini göster
    if st.session_state.chat_history:
        for msg in st.session_state.chat_history[-8:]:
            speaker = "Kullanıcı" if msg["role"] == "user" else "FinSim"
            st.markdown(f"**{speaker}:** {msg['content']}")

    with st.form("chat_form"):
        user_q = st.text_input("Sorunuz", placeholder="Örn: Kazanma olasılığı nedir? 1 ay için beklenen aralık?")
        send = st.form_submit_button("Gönder")

    if send and user_q.strip():
        st.session_state.chat_history.append({"role": "user", "content": user_q.strip()})

        def _fallback_answer(r: dict, p: dict, q: str) -> str:
            """Ollama yoksa kullanılacak kural tabanlı yanıtlar"""
            ql = q.lower()
            if "kazanma" in ql or "olasılık" in ql:
                return f"Kazanma olasılığı yaklaşık %{r['gain_probability_pct']:.2f}."
            if "var" in ql:
                return f"%95 VaR {r['var_95_value']:.2f} ( %{r['var_95_return_pct']:.2f} )."
            if "cvar" in ql or "koşullu" in ql:
                return f"%95 CVaR {r['cvar_95_value']:.2f} ( %{r['cvar_95_return_pct']:.2f} )."
            if "volatilite" in ql or "oynak" in ql:
                vol = r.get('historical_volatility')
                return f"Tarihsel volatilite {vol:.6f}." if isinstance(vol, (int, float)) else "Volatilite bilgisi mevcut değil."
            if "ortalama" in ql or "medyan" in ql:
                return f"Ortalama bitiş {r['average_end_price']:.2f}, medyan {r['median_end_price']:.2f}."
            return "Bu metrik sorunuz için belirgin eşleşme bulamadım; lütfen daha spesifik sorar mısınız?"

        # LLM kullanılabilirse kullan, yoksa kural tabanlı yanıt
        if ChatOllama is not None:
            try:
                llm = ChatOllama(model="qwen2.5:7b-instruct", temperature=0)
                sys_ctx = (
                    "Türkçe konuşan finans analisti asistanısın. Aşağıdaki simülasyon sonuçlarını referans alarak "
                    "kısa ve teknik, yanıltıcı olmayan yanıtlar ver. Sayıları yuvarlama: 2 ondalık.")
                facts = (
                    f"Başlangıç={results['start_price']:.2f}; Ortalama={results['average_end_price']:.2f}; "
                    f"Medyan={results['median_end_price']:.2f}; Kazanma%={results['gain_probability_pct']:.2f}; "
                    f"VaR95={results['var_95_value']:.2f} ( %{results['var_95_return_pct']:.2f} ); "
                    f"CVaR95={results['cvar_95_value']:.2f} ( %{results['cvar_95_return_pct']:.2f} ); "
                    f"Volatilite={results.get('historical_volatility', float('nan')):.6f}."
                )
                prompt = f"{sys_ctx}\n\nGerçekler: {facts}\n\nSoru: {user_q}\nCevap:"
                resp = llm.invoke(prompt)
                ans = getattr(resp, "content", None) or (resp if isinstance(resp, str) else None)
                answer = ans.strip() if isinstance(ans, str) and ans.strip() else _fallback_answer(results, st.session_state.run_params, user_q)
            except Exception:
                answer = _fallback_answer(results, st.session_state.run_params, user_q)
        else:
            answer = _fallback_answer(results, st.session_state.run_params, user_q)

        st.session_state.chat_history.append({"role": "assistant", "content": answer})
        st.rerun()

    if st.button("Yeni Analiz Yap"):
        for key in list(st.session_state.keys()):
            if key != 'current_state':
                del st.session_state[key]
        set_state("INIT")
        st.rerun()


