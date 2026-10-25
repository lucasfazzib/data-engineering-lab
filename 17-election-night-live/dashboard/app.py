"""Election night live dashboard (TSE official feed, 2026 presidential runoff).

Reads the silver Parquet files written by the poller; refreshes itself every 30 s.
"""

from __future__ import annotations

import os

import altair as alt
import pandas as pd
import streamlit as st

from election.metrics import connect, has_data

DATA = os.environ.get("ELECTION_DATA", "data")
REFRESH = int(os.environ.get("ELECTION_REFRESH_SECONDS", "30"))
COLORS = {"LULA": "#d62728", "FLAVIO BOLSONARO": "#1f77b4"}

st.set_page_config(page_title="Apuração ao vivo", page_icon="🗳️", layout="wide")
st.title("🗳️ Apuração ao vivo: 2º turno presidencial 2026")
st.caption("Dados oficiais do TSE (resultados.tse.jus.br), coletados a cada minuto. Não é um site oficial.")


def color_scale(names):
    names = list(names)
    return alt.Scale(domain=names, range=[COLORS.get(n, "#7f7f7f") for n in names])


@st.fragment(run_every=REFRESH)
def live() -> None:
    if not has_data(DATA):
        st.info("Ainda sem dados: rode `make poll` (ou `make backfill`).")
        return
    con = connect(DATA)
    br = con.execute("select * from latest_totals where scope = 'br'").df()
    cands = con.execute("select * from latest_candidates where scope = 'br' order by votes desc").df()
    if br.empty or cands.empty:
        st.info("Aguardando o arquivo nacional.")
        return
    t = br.iloc[0]
    lead, second = cands.iloc[0], cands.iloc[1] if len(cands) > 1 else None

    st.markdown(
        f"**{t.pct_sections_counted:.2f}% das seções apuradas** · totais gerados pelo TSE às "
        f"**{pd.Timestamp(t.totals_at):%H:%M:%S}** de {pd.Timestamp(t.totals_at):%d/%m}"
        + (" · **RESULTADO FINAL**" if t.is_final else "")
    )
    st.progress(min(float(t.pct_sections_counted) / 100, 1.0))

    cols = st.columns(len(cands) + 2)
    for col, (_, c) in zip(cols, cands.iterrows(), strict=False):
        col.metric(c["name"], f"{c.pct_valid:.2f}%", f"{c.votes:,.0f} votos".replace(",", "."), delta_color="off")
    if second is not None:
        gap = int(lead.votes - second.votes)
        cols[-2].metric(
            "Diferença", f"{gap:,.0f}".replace(",", "."), f"{lead.pct_valid - second.pct_valid:.2f} p.p.", delta_color="off"
        )
    cols[-1].metric(
        "Comparecimento",
        f"{100 * t.turnout / t.voters:.1f}%" if t.voters else "n/a",
        f"abstenção {100 * t.abstention / t.voters:.1f}%" if t.voters else None,
        delta_color="off",
    )

    left, right = st.columns(2)
    with left:
        st.subheader("Como a disputa evoluiu durante a apuração")
        tl = con.execute("select * from national_timeline order by totals_at").df()
        st.altair_chart(
            alt.Chart(tl)
            .mark_line(point=True)
            .encode(
                x=alt.X("pct_sections_counted:Q", title="% das seções apuradas"),
                y=alt.Y("pct_valid:Q", title="% dos votos válidos", scale=alt.Scale(zero=False)),
                color=alt.Color("name:N", title=None, scale=color_scale(tl["name"].unique())),
                tooltip=["totals_at:T", "pct_sections_counted:Q", "name:N", "votes:Q", "pct_valid:Q"],
            ),
            width="stretch",
        )
    with right:
        st.subheader("Projeção ingênua por estado")
        proj = con.execute("select * from projection order by projected_votes desc").df()
        st.caption(
            "Votos que faltam em cada estado divididos como os já apurados naquele estado. "
            "Corrige a ordem de chegada dos estados, não a diferença capital/interior. É um cenário, não uma previsão."
        )
        st.dataframe(
            proj.rename(
                columns={
                    "name": "candidato",
                    "counted_votes": "apurados",
                    "projected_votes": "projetados",
                    "projected_pct_valid": "% projetado",
                    "states_reporting": "UFs",
                }
            ),
            hide_index=True,
            width="stretch",
        )

    st.subheader("Por estado")
    states = con.execute("""
        select uf, any_value(pct_sections_counted) as pct_apurado, any_value(sections_remaining) as secoes_faltando,
               arg_max(name, votes) as lider,
               max(pct_valid) - min(pct_valid) as margem_pp,
               sum(votes) as votos_validos_apurados
        from state_race group by uf order by votos_validos_apurados desc
    """).df()
    states["uf"] = states["uf"].str.upper()
    chart = (
        alt.Chart(states)
        .mark_bar()
        .encode(
            x=alt.X("margem_pp:Q", title="margem do líder (p.p.)"),
            y=alt.Y("uf:N", sort="-x", title=None),
            color=alt.Color("lider:N", title="líder", scale=color_scale(states["lider"].unique())),
            tooltip=["uf", "lider", "margem_pp", "pct_apurado", "secoes_faltando", "votos_validos_apurados"],
        )
    )
    c1, c2 = st.columns([1, 1])
    c1.altair_chart(chart, width="stretch")
    c2.dataframe(states, hide_index=True, width="stretch", height=720)

    n_versions = con.execute("select count(*) from totals").fetchone()[0]
    st.caption(f"{n_versions:,} versões do arquivo do TSE armazenadas · atualiza a cada {REFRESH}s")


live()
