from typing import Dict, Any, Tuple

import numpy as np
import pandas as pd


def calculate_returns(df: pd.DataFrame, date_col: str, price_col: str) -> pd.Series:
    """DataFrame'den periyodik getirileri hesaplar"""
    if date_col not in df.columns or price_col not in df.columns:
        raise ValueError(f"Belirtilen sütunlar ({date_col}, {price_col}) DataFrame'de bulunamadı.")

    df_copy = df.copy()

    # Veri tiplerini dönüştür
    df_copy[date_col] = pd.to_datetime(df_copy[date_col], errors='coerce')
    df_copy[price_col] = pd.to_numeric(df_copy[price_col], errors='coerce')

    # Eksik değerleri temizle
    df_copy = df_copy.dropna(subset=[date_col, price_col])

    # Tarihe göre sırala ve index yap
    df_copy = df_copy.sort_values(by=date_col).set_index(date_col)

    # Yüzde değişimi hesapla
    returns = df_copy[price_col].pct_change().dropna()

    if returns.empty:
        raise ValueError("Getiri hesaplanamadı. Lütfen fiyat sütununun sayısal ve tarih sütununun kronolojik olduğundan emin olun.")

    return returns


def run_monte_carlo_simulation(
    start_price: float,
    returns: pd.Series,
    num_scenarios: int = 10000,
    num_periods: int = 252,
) -> Tuple[np.ndarray, Dict[str, float]]:
    """Tarihi getirilere dayalı Monte Carlo simülasyonu çalıştırır"""
    # Tarihi istatistikleri hesapla
    mean_return = returns.mean()
    volatility = returns.std()
    if volatility == 0 or pd.isna(volatility):
        raise ValueError("Volatilite hesaplanamadı (sıfır veya NaN). Fiyat verisi sabit mi?")

    # Rastgele getiri şokları üret
    daily_returns_shocks = np.random.normal(
        mean_return, volatility, (num_periods, num_scenarios)
    )

    # Fiyat yollarını hesapla
    price_paths = np.zeros((num_periods + 1, num_scenarios))
    price_paths[0] = start_price

    for t in range(1, num_periods + 1):
        price_paths[t] = price_paths[t - 1] * (1 + daily_returns_shocks[t - 1])
        # Negatif fiyatları önle
        price_paths[t] = np.maximum(0, price_paths[t])

    stats = {"mean_return": float(mean_return), "volatility": float(volatility)}
    return price_paths, stats


def analyze_simulation_results(price_paths: np.ndarray, start_price: float) -> Dict[str, Any]:
    """Simülasyon sonuçlarını analiz eder ve risk metriklerini hesaplar"""
    # Bitiş fiyatları
    end_prices = price_paths[-1]

    # Temel istatistikler
    average_end_price = float(np.mean(end_prices))
    median_end_price = float(np.median(end_prices))

    # Kazanma olasılığı
    gain_probability = float(np.sum(end_prices > start_price) / len(end_prices))

    # VaR (Value at Risk) %95
    var_95 = float(np.percentile(end_prices, 5))
    var_95_return = (var_95 - start_price) / start_price

    # CVaR (Conditional Value at Risk) %95
    cvar_95 = float(end_prices[end_prices <= var_95].mean())
    cvar_95_return = (cvar_95 - start_price) / start_price

    return {
        "start_price": float(start_price),
        "average_end_price": average_end_price,
        "median_end_price": median_end_price,
        "gain_probability_pct": gain_probability * 100.0,
        "var_95_value": var_95,
        "var_95_return_pct": var_95_return * 100.0,
        "cvar_95_value": cvar_95,
        "cvar_95_return_pct": cvar_95_return * 100.0,
        "confidence_interval_95": (
            float(np.percentile(end_prices, 2.5)),
            float(np.percentile(end_prices, 97.5)),
        ),
    }


