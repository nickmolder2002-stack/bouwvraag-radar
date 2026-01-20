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
# RATE LIMIT (B‑MODUS)
# =====================================================
if "last_call" not in st.session_state:
    st.session_state.last_call = 0

MIN_INTERVAL = 60  # seconden

# =====================================================
# AI FUNCTIE
# =====================================================
def ai_analyse(prompt: str) -> str:
    for _ in range(3):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Je bent een extreem scherpe commerciële analist "
                            "in de Nederlandse bouw- en maakindustrie. "
                            "Je redeneert realistisch en denkt altijd vanuit sales-kansen."
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
bedrijf = st.text_input(
    "🔍 Bedrijfsnaam",
    placeholder="Bijv. 'Rollecate'"
)

context = st.text_input(
    "🏗️ Wat doet dit bedrijf? (optioneel maar sterk aanbevolen)",
    placeholder="Bijv. producent van aluminium kozijnen en gevelsystemen"
)

if st.button("Analyseer") and bedrijf.strip():

    nu = time.time()
    if nu - st.session_state.last_call < MIN_INTERVAL:
        st.warning("⏱️ Even wachten — maximaal 1 analyse per minuut.")
    else:
        st.session_state.last_call = nu

        with st.spinner("AI onderzoekt bedrijf en personeelsbehoefte..."):

            prompt = f"""
Analyseer dit Nederlandse bedrijf:

BEDRIJFSNAAM:
{bedrijf}

EXTRA CONTEXT (indien gegeven door gebruiker):
{context if context.strip() else "Geen extra context opgegeven"}

DOEL:
Bepaal zo realistisch mogelijk:
- wat dit bedrijf doet
- welk type bedrijf het is
- welk personeel ze waarschijnlijk zoeken
- hoe dringend dit is voor sales

Gebruik de context expliciet als die er is.
Maak aannames alleen als dat logisch is en benoem ze.

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
<concreet en direct actieadvies>
"""

            resultaat = ai_analyse(prompt)

            st.subheader("📊 Bedrijfsanalyse & Salesadvies")
            st.markdown(resultaat)

# =====================================================
# FOOTER
# =====================================================
st.markdown("---")
st.caption("Geef 1 zin context → krijg 10× betere salesbeslissing.")

