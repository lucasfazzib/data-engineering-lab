"""Corridas de rua em SP: lista, mapa e filtros sobre o mart do dbt (DuckDB, somente leitura)."""

from __future__ import annotations

import math
import os
from datetime import date, timedelta
from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

DB = Path(os.environ.get("CORRIDAS_DATA", Path(__file__).resolve().parents[1] / "data")) / "warehouse.duckdb"
CATEGORIES = ["5k", "10k", "21k", "42k"]
STATUS_LABEL = {
    "open": "inscrições abertas",
    "closed": "encerradas",
    "sold_out": "esgotada",
    "postponed": "adiada",
    "cancelled": "cancelada",
}

st.set_page_config(page_title="Corridas SP", page_icon="🏃", layout="wide")
st.title("🏃 Corridas de rua em SP")


@st.cache_data(ttl=300)
def load() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    with duckdb.connect(str(DB), read_only=True) as con:
        races = con.execute("select * from marts.mart_upcoming_races order by event_date").df()
        cities = con.execute("select municipality, lat, lon from marts.dim_location order by municipality").df()
        health = con.execute("select * from marts.mart_source_health").df()
    return races, cities, health


def km_between(lat1, lon1, lat2, lon2) -> float:
    """Great-circle distance (haversine), in km."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(a))


if not DB.exists():
    st.info("Sem dados ainda: rode `make run` (coleta + dbt build).")
    st.stop()

races, cities, health = load()

with st.sidebar:
    st.header("Filtros")
    chosen = st.multiselect("Distâncias", CATEGORIES, default=CATEGORIES)
    start, end = st.date_input("Período", (date.today(), date.today() + timedelta(days=120)))
    city = st.selectbox(
        "Perto de",
        ["(qualquer lugar)", *cities["municipality"]],
        index=1 + int(cities.index[cities["municipality"] == "São Paulo"][0]),
    )
    radius = st.slider("Raio (km)", 5, 300, 50, step=5, disabled=city == "(qualquer lugar)")
    max_price = st.slider("Preço até (R$)", 0, 500, 500, step=10)
    only_open = st.checkbox("Só com inscrições abertas", value=False)

df = races.copy()
df = df[(df["event_date"] >= pd.Timestamp(start)) & (df["event_date"] <= pd.Timestamp(end))]
df = df[df["distance_categories"].apply(lambda cats: any(c in chosen for c in (cats if cats is not None else [])))]
df = df[df["price_from_brl"].isna() | (df["price_from_brl"] <= max_price)]
if only_open:
    df = df[df["status"] == "open"]
if city != "(qualquer lugar)":
    ref = cities[cities["municipality"] == city].iloc[0]
    df["distancia_km"] = df.apply(lambda r: km_between(ref.lat, ref.lon, r.lat, r.lon) if pd.notna(r.lat) else None, axis=1)
    df = df[df["distancia_km"].notna() & (df["distancia_km"] <= radius)]

c1, c2, c3 = st.columns(3)
c1.metric("Corridas encontradas", len(df))
c2.metric("Cidades", df["municipality"].nunique())
median_price = df["price_from_brl"].median() if df["price_from_brl"].notna().any() else None
c3.metric("Preço mediano (a partir de)", f"R$ {median_price:.0f}" if median_price is not None else "n/d")

map_df = df.dropna(subset=["lat", "lon"])
if not map_df.empty:
    st.map(map_df, latitude="lat", longitude="lon", size=400)

table = pd.DataFrame(
    {
        "data": df["event_date"].dt.strftime("%d/%m (%a)"),
        "corrida": df["event_name"],
        "cidade": df["municipality"],
        "distâncias": df["distance_categories"].apply(
            lambda c: ", ".join(x for x in (c if c is not None else []) if x != "other")
        ),
        "a partir de (R$)": df["price_from_brl"],
        "status": df["status"].map(STATUS_LABEL),
        **({"distância (km)": df["distancia_km"].round(0)} if "distancia_km" in df else {}),
        "inscrição": df["registration_url"],
        "fontes": df["sources"].apply(lambda s: ", ".join(s) if s is not None else ""),
    }
)
st.dataframe(
    table,
    hide_index=True,
    width="stretch",
    column_config={"inscrição": st.column_config.LinkColumn("inscrição", display_text="abrir")},
)

with st.expander("Saúde das fontes"):
    st.dataframe(health, hide_index=True, width="stretch")

st.caption(
    "Fontes: Minhas Inscrições (minhasinscricoes.com.br) e CBAt (cbat.org.br) - dados factuais dos eventos, "
    "sempre com o link original; confira data, preço e regulamento no site oficial antes de se inscrever. "
    "Municípios e coordenadas: IBGE. Projeto pessoal de estudo, sem fins comerciais."
)
