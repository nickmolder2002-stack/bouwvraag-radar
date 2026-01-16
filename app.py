import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd

# =====================================================
# CONFIG
# =====================================================
st.set_page_config(page_title="Bouw PersoneelsRadar", layout="wide")

st.title("🏗️ PersoneelsRadar – Bouw & Prefab")
st.caption("Automatisch signaleren welke bedrijven personeel nodig hebben")

# =====================================================
# INPUT (MINIMAAL)
# =====================================================
col1, col2 = st.columns(2)

with col1:
    sector = st.selectbox(
        "Sector",
        [
            "Prefab beton",
            "Modulaire woningbouw",
            "Hoofdaannemer",
            "Onderaannemer"
        ]
    )

with col2:
    regio = st.selectbox(
        "Regio",
        [
            "Nederland",
            "Randstad",
            "Noord-Brabant",
            "Gelderland",
            "Zuid-Holland"
        ]
    )

# =====================================================
# VACATURE ZOEKLOGICA (ZONDER GOOGLE)
# =====================================================
def zoek_vacatures(sector, regio):
    """
    Zoekt vacatures via Indeed-achtige openbare pagina’s
    (signaalfunctie, geen scraping op account-niveau)
    """

    zoekterm = f"{sector} {regio}"
    url = f"https://nl.indeed.com/jobs?q={zoekterm}&l={regio}"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    r = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")

    resultaten = []

    for card in soup.select("a.tapItem")[:10]:
        bedrijf = card.select_one(".companyName")
        titel = card.select_one(".jobTitle")

        if bedrijf and titel:
            resultaten.append({
                "Bedrijf": bedrijf.text.strip(),
                "Vacature": titel.text.strip(),
                "Sector": sector,
                "Regio": regio,
                "Personeelsbehoefte": "Hoog",
                "Wie bellen": "Projectleider / Bedrijfsleider",
                "Actie": "Vandaag bellen"
            })

    return resultaten

# =====================================================
# ACTIEKNOP
# =====================================================
if st.button("🔍 Zoek bedrijven met personeelsbehoefte"):
    with st.spinner("Vacature‑signalen worden geanalyseerd..."):
        data = zoek_vacatures(sector, regio)

    if not data:
        st.warning("Geen duidelijke personeels-signalen gevonden.")
    else:
        df = pd.DataFrame(data)

        st.subheader("📞 Bedrijven met directe personeelsbehoefte")
        st.dataframe(df, use_container_width=True)

        st.success(f"{len(df)} bedrijven gevonden met actieve vraag")

# =====================================================
# UITLEG (MINIMAAL)
# =====================================================
st.divider()
st.caption(
    "Deze tool toont alleen bedrijven met aantoonbare personeelsvraag "
    "(vacatures = pijn = belmoment). Geen invoer, geen CRM."
)
