import streamlit as st
import os
from openai import OpenAI

# =====================================================
# CONFIG
# =====================================================
st.set_page_config(
    page_title="BouwVraag Radar",
    layout="centered"
)

st.title("🧠 BouwVraag Radar")
st.caption("Sales‑tool: ontdek waar NU personeelsvraag zit in de bouw")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# =====================================================
# HULPLOGICA
# =====================================================

BRANCHE_KEYWORDS = [
    "onderaanneming",
    "onderaannemer",
    "prefab",
    "prefab beton",
    "modulaire woningbouw",
    "timmer",
    "beton",
    "ruwbouw",
    "bouw"
]

def is_branche_input(query: str) -> bool:
    return any(k in query.lower() for k in BRANCHE_KEYWORDS)


def ai_analyse(prompt: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Je bent een extreem scherpe sales-analist in de Nederlandse bouwsector."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1
    )
    return response.choices[0].message.content


# =====================================================
# UI — ENIGE INPUT
# =====================================================

zoekterm = st.text_input(
    "🔍 Bedrijfsnaam of branche",
    placeholder="Bijv. 'Bouwbedrijf Jansen BV' of 'onderaanneming'"
)

if st.button("Analyseer") and zoekterm.strip():

    with st.spinner("AI analyseert personeelsvraag..."):

        # =================================================
        # BRANCHE MODE
        # =================================================
        if is_branche_input(zoekterm):
            prompt = f"""
Je krijgt deze branche-input: "{zoekterm}"

Doel:
Selecteer 3 REALISTISCHE (fictieve) Nederlandse bouwbedrijven
die waarschijnlijk personeelsvraag hebben.

Voor elk bedrijf:
- Bepaal type bedrijf
- Analyseer personeelsdruk
- Geef een score (0-100) op basis van:
  * type bedrijf
  * marktcontext
  * waarschijnlijke vacatures
  * urgentie
  * trek punten af bij twijfel

Geef OUTPUT EXACT in dit format:

BEDRIJF: <naam>
TYPE: <type>
SCORE: <0-100>
LABEL: 🔴 HEET / 🟠 WARM / 🟢 KOUD
REDENEN:
- <reden 1>
- <reden 2>
ADVIES: <Vandaag bellen / Deze week / Niet bellen>

Herhaal dit 3 keer.
"""
            resultaat = ai_analyse(prompt)

            st.subheader("📊 Beste sales‑kansen")
            st.markdown(resultaat)

        # =================================================
        # BEDRIJF MODE
        # =================================================
        else:
            prompt = f"""
Analyseer dit bedrijf: "{zoekterm}"

Doe het volgende:
1. Bepaal wat voor bouwbedrijf dit waarschijnlijk is
2. Beoordeel personeelsdruk
3. Geef een SCORE (0-100) op basis van:
   - type bedrijf
   - marktcontext
   - aannemelijke personeelsvraag
   - urgentie
4. Classificeer:
   80-100 = 🔴 HEET
   60-79  = 🟠 WARM
   <60    = 🟢 KOUD

Geef OUTPUT EXACT in dit format:

BEDRIJF:
TYPE:
SCORE:
LABEL:
REDENEN:
- <reden 1>
- <reden 2>
ADVIES:
"""
            resultaat = ai_analyse(prompt)

            st.subheader("📋 Bedrijfsanalyse")
            st.markdown(resultaat)

# =====================================================
# FOOTER
# =====================================================
st.markdown("---")
st.caption("Geen CRM. Geen ruis. Alleen bellen waar het loont.")
