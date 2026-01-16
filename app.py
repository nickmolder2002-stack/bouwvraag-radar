import streamlit as st
import os
import requests
from openai import OpenAI

# ===============================
# CONFIG
# ===============================
st.set_page_config(
    page_title="🧠 BouwVraag Radar",
    layout="centered"
)

st.title("🧠 BouwVraag Radar")
st.caption("AI‑tool voor sales: ontdek waar personeelsvraag zit in de bouw")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ===============================
# HULPFUNCTIES
# ===============================

def is_branche_zoekopdracht(query: str) -> bool:
    branche_keywords = [
        "onderaanneming",
        "onderaannemer",
        "prefab",
        "prefab beton",
        "modulaire woningbouw",
        "bouw",
        "timmer",
        "beton",
        "ruwbouw"
    ]
    return any(k in query.lower() for k in branche_keywords)


def analyseer_met_ai(prompt: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Je bent een ervaren sales-analist in de bouwsector."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )
    return response.choices[0].message.content


# ===============================
# UI – ENIGE INPUT
# ===============================

zoekterm = st.text_input(
    "🔍 Bedrijfsnaam of branche",
    placeholder="Bijv. 'Bouwbedrijf Jansen BV' of 'onderaanneming'"
)

analyse_knop = st.button("Analyseer")

# ===============================
# LOGICA
# ===============================

if analyse_knop and zoekterm.strip():

    with st.spinner("AI onderzoekt personeelsvraag..."):

        if is_branche_zoekopdracht(zoekterm):
            prompt = f"""
Je krijgt een branche of type bedrijf: "{zoekterm}"

Doe het volgende:
1. Interpreteer dit als bouw-gerelateerde bedrijven in Nederland
2. Denk aan onderaannemers, prefab, beton, modulaire woningbouw (indien relevant)
3. Ga uit van algemene marktkennis (geen exacte data nodig)
4. Selecteer 3 typische bedrijven (fictief maar realistisch)
5. Beoordeel per bedrijf of er waarschijnlijk personeelsvraag is

Geef output EXACT in dit format:

BEDRIJF: <naam>
TYPE: <type>
SIGNALEN: <korte uitleg>
KANS: 🔴 Hoog / 🟠 Middel / 🟢 Laag
ACTIE: <Vandaag bellen / Deze week / Niet bellen>

Herhaal dit 3 keer.
"""
            resultaat = analyseer_met_ai(prompt)

            st.subheader("📊 Beste sales‑kansen")
            st.markdown(resultaat)

        else:
            prompt = f"""
Analyseer dit bedrijf: "{zoekterm}"

Doe het volgende:
1. Bepaal wat voor bouwbedrijf dit waarschijnlijk is
2. Schat of er personeelsvraag is (op basis van type, groei, markt)
3. Wees kritisch: alleen hoog als het logisch is

Geef output EXACT in dit format:

BEDRIJF:
TYPE:
SIGNALEN:
KANS:
ADVIES:
"""
            resultaat = analyseer_met_ai(prompt)

            st.subheader("📋 Bedrijfsanalyse")
            st.markdown(resultaat)

# ===============================
# FOOTER
# ===============================
st.markdown("---")
st.caption("Geen CRM. Geen ruis. Alleen bellen waar het loont.")

