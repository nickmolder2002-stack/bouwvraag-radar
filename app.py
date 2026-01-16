import streamlit as st
import os
import time
from openai import OpenAI, RateLimitError

# =====================================================
# CONFIG
# =====================================================
st.set_page_config(
    page_title="BouwVraag Radar",
    layout="centered"
)

st.title("🧠 BouwVraag Radar")
st.caption("AI ontdekt personeelsvraag vóórdat jij belt")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# =====================================================
# RATE‑LIMIT BESCHERMING
# =====================================================
if "last_call" not in st.session_state:
    st.session_state.last_call = 0

MIN_INTERVAL = 60  # seconden (belangrijk voor B‑modus)

# =====================================================
# AI FUNCTIE (VEILIG)
# =====================================================
def ai_analyse(prompt: str) -> str:
    for poging in range(3):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Je bent een zeer scherpe commerciële analist "
                            "gespecialiseerd in de Nederlandse bouwsector. "
                            "Je redeneert realistisch, maakt aannames en "
                            "denkt altijd vanuit sales-kansen."
                        )
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.15
            )
            return response.choices[0].message.content

        except RateLimitError:
            time.sleep(5)

    return "⚠️ AI is tijdelijk overbelast. Probeer het over 1 minuut opnieuw."

# =====================================================
# UI
# =====================================================
zoekterm = st.text_input(
    "🔍 Bedrijfsnaam",
    placeholder="Bijv. 'Bouwbedrijf Jansen BV'"
)

if st.button("Analyseer") and zoekterm.strip():

    nu = time.time()
    if nu - st.session_state.last_call < MIN_INTERVAL:
        st.warning("⏱️ Even wachten — maximaal 1 analyse per minuut.")
    else:
        st.session_state.last_call = nu

        with st.spinner("AI onderzoekt het bedrijf en personeelsbehoefte..."):

            prompt = f"""
Onderzoek dit Nederlandse bedrijf: "{zoekterm}"

DOE HET VOLGENDE:
1. Bepaal wat voor type bedrijf dit is
2. Beschrijf kort wat ze doen
3. Bepaal welk personeel ze waarschijnlijk zoeken
4. Schat hoe dringend dit is

DENK ALS EEN ERVAREN SALES DIRECTEUR.

GEEF OUTPUT EXACT IN DIT FORMAT:

BEDRIJF:
TYPE BEDRIJF:
WAT DOEN ZE:
- <activiteit 1>
- <activiteit 2>

WAARSCHIJNLIJKE PERSONEELSBEHOEFTE:
- <functie + korte uitleg>
- <functie + korte uitleg>

PERSONEELSDRUK SCORE: <0-100>

LABEL:
🔴 HEET (nu bellen)
🟠 WARM (deze week)
🟢 KOUD (monitoren)

REDENEN:
- <reden 1>
- <reden 2>

SALESADVIES:
<concreet actieadvies voor vandaag>
"""

            resultaat = ai_analyse(prompt)

            st.subheader("📊 Bedrijfsanalyse & Salesadvies")
            st.markdown(resultaat)

# =====================================================
# FOOTER
# =====================================================
st.markdown("---")
st.caption("Rustig testen. Slim beslissen. Bellen waar het loont.")
