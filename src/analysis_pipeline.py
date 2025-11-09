from typing import Any, Dict, Optional

import pandas as pd
import streamlit as st

from src.data_inspector import inspect_and_load_data
from src.simulation_engine import (
    analyze_simulation_results,
    calculate_returns,
    run_monte_carlo_simulation,
)


def inspect_uploaded_file(uploaded_file_name: str) -> Dict[str, Any]:
    """Yüklenen dosyayı analiz eder ve metadata döndürür"""
    if "uploaded_file" not in st.session_state or st.session_state.uploaded_file is None:
        return {"error": "Kullanıcı henüz bir dosya yüklemedi."}

    uploaded_file = st.session_state.uploaded_file
    uploaded_file.seek(0)

    inspection_result = inspect_and_load_data(uploaded_file)

    if inspection_result.get("dataframe") is not None:
        st.session_state.dataframe = inspection_result.pop("dataframe")

    return inspection_result


def run_full_simulation_analysis(
    date_col: str,
    price_col: str,
    start_price: float,
    num_periods: int,
    num_scenarios: int,
    header_row_index: Optional[int] = None,
) -> Dict[str, Any]:
    """Monte Carlo simülasyonunu çalıştırır ve analiz sonuçlarını döndürür"""
    try:
        if header_row_index is not None and "uploaded_file" in st.session_state:
            uploaded_file = st.session_state.uploaded_file
            uploaded_file.seek(0)

            if uploaded_file.name.lower().endswith('.csv'):
                df = pd.read_csv(uploaded_file, header=header_row_index, engine="python")
            else:
                df = pd.read_excel(
                    uploaded_file,
                    header=header_row_index,
                    engine="openpyxl" if uploaded_file.name.lower().endswith('.xlsx') else None,
                )

            df = df.dropna(how='all')
            st.session_state.dataframe = df

        if "dataframe" not in st.session_state or st.session_state.dataframe is None:
            return {"error": "Analiz için veri bulunamadı. Lütfen önce bir dosya yükleyin."}

        df = st.session_state.dataframe

        returns = calculate_returns(df, date_col, price_col)

        price_paths, stats = run_monte_carlo_simulation(
            start_price, returns, num_scenarios, num_periods
        )

        analysis_results = analyze_simulation_results(price_paths, start_price)

        analysis_results["historical_mean_return"] = stats["mean_return"]
        analysis_results["historical_volatility"] = stats["volatility"]
        analysis_results["num_scenarios"] = int(num_scenarios)
        analysis_results["num_periods"] = int(num_periods)

        st.session_state.price_paths = price_paths

        return analysis_results
    except Exception as e:
        return {"error": f"Simülasyon sırasında bir hata oluştu: {e}"}


