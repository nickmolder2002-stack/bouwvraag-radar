import streamlit as st
import pandas as pd
import os
from datetime import date
from openai import OpenAI

# =====================================================
# CONFIG
# =====================================================
st.set_page_config(page_title="BouwVraag Radar", layout="wide")
DATA_FILE = "data.csv"

# OpenAI client (leest OPENAI_API_KEY uit Streamlit Secrets)
client = OpenAI()

# =====================================================
# SCORE LOGICA
# =====================================================
def bereken_score(projecten, vacatures, werksoort, fase):
    score = projecten * 5
    if vacatures == "Ja":
        score += 20
    score += 15 if werksoort in ["Beton / Ruwbouw", "Prefab"] else 10
    score += 15 if fase == "Piek" else 10 if fase == "Start" else 5
    return min(score, 100)

def score_label(score):
    if score >= 70:
        return "🔴 Hoog"
    elif score >= 40:
        return "🟠 Middel"
    else:
        return "🟢 Laag"

# =====================================================
# DATA LADEN
# =====================================================
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
else:
    df = pd.DataFrame(columns=[
        "Bedrijf","Type","Werksoort","Projecten","Vacatures",
        "Fase","Score","Prioriteit","Status",
        "Laatste contact","Volgende actie","Notitie"
    ])

# =====================================================
# TITEL
# =====================================================
st.title("🧠 BouwVraag Radar")

# =====================================================
# SIDEBAR – INPUT
# =====================================================
st.sidebar.header("➕ Nieuw bedrijf")

bedrijf = st.sidebar.text_input("Bedrijfsnaam")
type_bedrijf = st.sidebar.selectbox(
    "Type bedrijf",
    ["Aannemer","Onderaannemer","Prefab beton","Modulaire woningbouw","Toelevering / Werkplaats","Afbouw"]
)
werksoort = st.sidebar.selectbox("Werksoort", ["Timmerman","Beton / Ruwbouw","Prefab"])
projecten = st.sidebar.slider("Aantal projecten", 0, 10, 3)
vacatures = st.sidebar.selectbox("Vacatures actief?", ["Nee","Ja"])
fase = st.sidebar.selectbox("Projectfase", ["Start","Piek","Afronding"])
status = st.sidebar.selectbox("Status", ["Vandaag bellen","Deze week","Later","Klaar"])
laatst_contact = st.sidebar.date_input("Laatste contact", value=date.today())
volgende_actie = st.sidebar.text_input("Volgende actie")
notitie = st.sidebar.text_area("Notitie")

if st.sidebar.button("Opslaan"):
    if bedrijf.strip() == "":
        st.sidebar.error("❌ Bedrijfsnaam is verplicht")
    else:
        score = bereken_score(projecten, vacatures, werksoort, fase)
        nieuw = {
            "Bedrijf": bedrijf,
            "Type": type_bedrijf,
            "Werksoort": werksoort,
            "Projecten": projecten,
            "Vacatures": vacatures,
            "Fase": fase,
            "Score": score,
            "Prioriteit": score_label(score),
            "Status": status,
            "Laatste contact": laatst_contact,
            "Volgende actie": volgende_actie,
            "Notitie": notitie
        }
        df = pd.concat([df, pd.DataFrame([nieuw])], ignore_index=True)
        df.to_csv(DATA_FILE, index=False)
        st.sidebar.success(f"✅ Opgeslagen (score: {score}%)")

# =====================================================
# VANDAAG BELLEN
# =====================================================
st.subheader("📞 Vandaag bellen")
if not df.empty:
    bellen = df[df["Status"] == "Vandaag bellen"].sort_values("Score", ascending=False)
    st.dataframe(bellen, use_container_width=True)
else:
    st.info("Nog geen bedrijven ingevoerd")

# =====================================================
# AI ANALYSE OP JE EIGEN DATA
# =====================================================
def ai_analyse_met_openai(df):
    if df.empty:
        return "⚠️ Nog geen data beschikbaar voor AI-analyse."

    samenvatting = df.head(50).to_csv(index=False)

    prompt = f"""
Je bent een ervaren Nederlandse sales- en recruitmentanalist in de bouwsector.

Analyseer deze bedrijfsdata en geef:
1. Wie vandaag gebeld moet worden
2. Welke werksoorten de hoogste vraag hebben
3. Concreet actieadvies per type bedrijf

Data:
{samenvatting}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Je analyseert bouwbedrijven voor personeelsvraag."},
                {"role": "user", "content": prompt}
            ],
            timeout=30
        )
        return response.choices[0].message.content
    except Exception:
        return "⚠️ AI tijdelijk niet beschikbaar."

st.divider()
st.subheader("🤖 AI-analyse & advies (eigen data)")

if st.button("🔍 Analyseer met AI"):
    with st.spinner("AI denkt na..."):
        advies = ai_analyse_met_openai(df)
        st.markdown(advies)

# =====================================================
# AI MARKTVERKENNING – LIVE INTELLIGENCE (SLIM & REALISTISCH)
# =====================================================
st.divider()
st.subheader("🌍 AI Marktverkenning – Personeelsbehoefte")

sector_input = st.selectbox(
    "Selecteer sector",
    [
        "Prefab beton producent",
        "Hoofdaannemer",
        "Onderaannemer",
        "Modulaire woningbouw",
        "Toelevering / Werkplaats",
        "Afbouw"
    ]
)

regio_input = st.selectbox(
    "Regio",
    ["Nederland", "Randstad", "Noord-Brabant", "Gelderland", "Zuid-Holland"]
)

if st.button("🚀 Zoek bedrijven met personeelsbehoefte"):
    with st.spinner("AI onderzoekt markt en signalen..."):
        prompt = f"""
Je bent een zeer kritische Nederlandse industrie- en recruitmentanalist.

BELANGRIJK:
- Neem ALLEEN echte bedrijven mee
- Voor 'Prefab beton producent':
  - Moet een eigen fabriek hebben
  - Produceert zelf prefab betonelementen
  - Sluit aannemers (zoals BAM, Heijmans, Dura Vermeer) UIT

Taak:
1. Selecteer maximaal 10 bedrijven binnen deze sector: {sector_input}
2. Beoordeel of zij personeel nodig hebben (vacatures, groei, projectdruk)
3. Bepaal WIE binnen het bedrijf gaat over personeels-inleen

Geef per bedrijf EXACT dit formaat:

Bedrijf:
Type:
Waarom valide:
Personeelsbehoefte-score (0–100):
Urgentie (Hoog/Middel/Laag):
Actuele signalen:
Welke functies gevraagd:

Beslisser personeels-inleen:
- Functie (geen naam gokken)
- Afdeling
- Waarschijnlijkheid (Hoog/Middel)
- Benaderstrategie

Concreet beladvies:
Regio: {regio_input}

Wees streng. Twijfel = NIET opnemen.
"""

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Je analyseert personeelsbehoefte in de Nederlandse bouwsector."},
                    {"role": "user", "content": prompt}
                ],
                timeout=60
            )
            st.markdown(response.choices[0].message.content)
        except Exception as e:
            st.error("❌ Marktverkenning mislukt")
            st.code(str(e))

# =====================================================
# OVERZICHT
# =====================================================
st.divider()
st.subheader("📊 Totaal overzicht")

if not df.empty:
    st.dataframe(df, use_container_width=True)
else:
    st.info("Nog geen data beschikbaar")
