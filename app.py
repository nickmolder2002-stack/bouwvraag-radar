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
st.caption("AI ontdekt waar personeelsvraag zit — vóórdat je belt")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# =====================================================
# AI CORE
# =====================================================

def ai_analyse(prompt: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    "Je bent een extreem scherpe commerciële analist gespecialiseerd "
                    "in de Nederlandse bouwsector. Je redeneert realistisch, "
                    "werkt met aannames en denkt altijd vanuit sales-kansen."
                )
            },
            {"role": "user", "content": prompt}
        ],
        temperature=0.15
    )
    return response.choices[0].message.content


# =====================================================
# UI
# =====================================================

zoekterm = st.text_input(
    "🔍 Bedrijfsnaam",
    placeholder="Bijv. 'Bouwbedrijf Jansen BV'"
)

if st.button("Analyseer") and zoekterm.strip():

    with st.spinner("AI onderzoekt het bedrijf en personeelsbehoefte..."):

        prompt = f"""
Onderzoek dit Nederlandse bedrijf: "{zoekterm}"

DOEL:
Bepaal of dit bedrijf waarschijnlijk NU personeel nodig heeft.

STAPPEN:
1. Analyseer wat voor bedrijf dit is
2. Wat doen ze concreet (activiteiten / projecten)
3. Welke functies zoeken ze waarschijnlijk
4. Hoe dringend is die behoefte

DENK ALS EEN SALES DIRECTEUR.

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
st.caption("AI denkt vooruit. Jij belt alleen waar het loont.")

