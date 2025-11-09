import io
from typing import Dict, Any, List, Optional

import pandas as pd


def find_header_row(df_preview: pd.DataFrame) -> int:
    """
    DataFrame'in ilk 20 satırını analiz ederek başlık satırını bulur.
    Tarih ve fiyat anahtar kelimelerine göre skorlama yapar.
    """
    header_candidate = 0
    best_score = -1

    for i, row in df_preview.iterrows():
        row_values = [str(val).strip().lower() for val in row.values]

        # Boş satırları atla
        if all((val == "nan" or val == "") for val in row_values):
            continue

        # Tarih anahtar kelimelerini kontrol et
        has_date = any(
            any(k in val for k in ["date", "tarih", "gün", "gun"]) for val in row_values
        )
        # Fiyat anahtar kelimelerini kontrol et
        has_price = any(
            any(k in val for k in [
                "price", "fiyat", "close", "kapanış", "kapanis", "open", "high", "low",
                "bist", "kchol", "froto", "tuprs", "toaso", "ge", "intel", "microsoft"
            ]) for val in row_values
        )
        # Ayırıcı karakterler (space, /, -, _) kontrolü
        has_word_like = any(any(sep in val for sep in [" ", "/", "-", "_"]) for val in row_values)

        # Skorlama sistemi
        score = 0
        if has_date:
            score += 2
        if has_price:
            score += 2
        if has_word_like:
            score += 1
        # Uzun stringlerden kaçın
        if any(len(val) > 60 for val in row_values):
            score -= 1

        if score > best_score:
            best_score = score
            header_candidate = i

        if has_date and has_price:
            return i

    return header_candidate


def inspect_and_load_data(uploaded_file) -> Dict[str, Any]:
    """
    CSV/Excel dosyasını okur, başlık satırını tespit eder ve metadata döndürür.
    
    Returns:
        dict: DataFrame, sütunlar, önerilen başlık satırı, tarih/fiyat sütunları
    """
    try:
        uploaded_file.seek(0)
        preview_df: Optional[pd.DataFrame] = None

        # Dosya formatına göre okuma
        if uploaded_file.name.lower().endswith('.csv'):
            preview_df = pd.read_csv(uploaded_file, header=None, nrows=20, engine="python")
        elif uploaded_file.name.lower().endswith(('.xls', '.xlsx')):
            preview_df = pd.read_excel(uploaded_file, header=None, nrows=20, engine="openpyxl" if uploaded_file.name.lower().endswith('.xlsx') else None)
        else:
            return {"error": "Desteklenmeyen dosya formatı. Lütfen CSV veya Excel kullanın."}

        file_preview_str = preview_df.to_string()
        suggested_header_row = find_header_row(preview_df)

        # Tam dosyayı başlık satırıyla oku
        uploaded_file.seek(0)
        df: Optional[pd.DataFrame] = None
        if uploaded_file.name.lower().endswith('.csv'):
            df = pd.read_csv(uploaded_file, header=suggested_header_row, engine="python")
        else:
            df = pd.read_excel(uploaded_file, header=suggested_header_row, engine="openpyxl" if uploaded_file.name.lower().endswith('.xlsx') else None)

        # Boş satırları temizle
        df = df.dropna(how='all')
        cols: List[str] = list(df.columns)

        # Tarih ve fiyat sütunlarını tespit et
        suggested_date: Optional[str] = None
        suggested_prices: List[str] = []

        # Sütun analizi
        for col in cols:
            col_str = str(col).lower()
            # İsimsiz sütunları atla
            if 'unnamed' in col_str:
                continue

            # Tarih sütunu kontrolü
            if any(k in col_str for k in ["date", "tarih", "gün", "gun"]):
                if suggested_date is None:
                    suggested_date = col

            # Fiyat sütunu kontrolü
            price_keywords = [
                'price', 'fiyat', 'kapanış', 'kapanis', 'close', 'getiri',
                'open', 'high', 'low', 'bist', 'kchol', 'froto', 'tuprs', 'toaso',
                'ge', 'intel', 'microsoft'
            ]
            if any(keyword in col_str for keyword in price_keywords):
                suggested_prices.append(col)
            # Sayısal sütunları da fiyat olarak değerlendir
            elif pd.api.types.is_numeric_dtype(df[col]):
                if col != suggested_date:
                    suggested_prices.append(col)

        # Tarih sütununu fiyat listesinden çıkar
        if suggested_date in suggested_prices:
            suggested_prices = [c for c in suggested_prices if c != suggested_date]

        # Tekrarları kaldır
        suggested_prices = list(dict.fromkeys(suggested_prices))

        return {
            "dataframe": df,
            "columns": cols,
            "suggested_header_row": suggested_header_row,
            "suggested_date_col": suggested_date,
            "suggested_price_cols": suggested_prices,
            "file_preview": file_preview_str,
            "error": None
        }
    except Exception as e:
        return {"error": f"Dosya okunurken bir hata oluştu: {e}. Başlık satırı manuel olarak girilmeli."}


