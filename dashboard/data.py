from dataclasses import dataclass

import pandas as pd
import streamlit as st

from dashboard.config import DATA_FILE, DAY_NAME_MAP


@dataclass(frozen=True)
class FilterState:
    start_date: object
    end_date: object
    selected_days: list[str]
    start_hour: int
    end_hour: int


@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_FILE)
    df["Fecha"] = pd.to_datetime(df["Fecha"])
    df["Hora"] = df["Fecha"].dt.hour
    df["Dia_Semana"] = df["Fecha"].dt.day_name().map(DAY_NAME_MAP)
    return df


def apply_filters(df: pd.DataFrame, filters: FilterState) -> pd.DataFrame:
    mask = (
        (df["Fecha"].dt.date >= filters.start_date)
        & (df["Fecha"].dt.date <= filters.end_date)
        & (df["Dia_Semana"].isin(filters.selected_days))
        & (df["Hora"] >= filters.start_hour)
        & (df["Hora"] <= filters.end_hour)
    )
    return df.loc[mask]
