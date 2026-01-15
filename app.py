import streamlit as st
import pandas as pd
import os
from datetime import date
from openai import OpenAI

# ========================
# CONFIG
# ========================
st.set_page_config(page_title="BouwVraag Radar", layout="wide")
DATA_FILE = "data.csv"

client = OpenAI()  # leest OPENAI_API_KEY automatisch

# ========================
# SCORE LOGICA
# ========================
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

# ========================
# DATA LADEN
# ========================
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
else:
    df = pd.DataFrame(columns=[
        "Bedrijf","Type","Werksoort","Projecten","Vacatures",
        "Fase","Score","Prioriteit","Status",
        "Laatste contact","Volgende actie","Notitie"
    ])

# ========================
# TITEL
# ========================
st.title("🧠 BouwVraag Radar")

# ========================
# SIDEBAR – INPUT
# ========================
st.sidebar.header("➕ Nieuw bedrijf")
bedrijf = st.sidebar.text_input("Bedrijfsnaam")
type_bedrijf = st.sidebar.selectbox("Type bedrijf", ["Aannemer","Prefab","Onderhoud"])
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
        st.sidebar.error("Bedrijfsnaam is verplicht")
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
        st.sidebar.success(f"Opgeslagen ✅ Score: {score}%")

# ========================
# VANDAAG BELLEN
# ========================
st.subheader("📞 Vandaag bellen")
if not df.empty:
    bellen = df[df["Status"] == "Vandaag bellen"].sort_values("Score", ascending=False)
    st.dataframe(bellen, use_container_width=True)
else:
    st.info("Nog geen bedrijven")

# ========================
# AI ANALYSE (STABIEL & FOUTBESTENDIG)
# ========================
def ai_analyse_met_openai(df):
    if df.empty or len(df) == 0:
        return "⚠️ Nog geen data beschikbaar voor AI-analyse."

    try:
        samenvatting = df.head(50).to_csv(index=False)
    except Exception:
        return "⚠️ Data kon niet correct worden gelezen."

    prompt = f"""
Je bent een ervaren sales- en recruitment-analist in de bouwsector.
Analyseer de data en geef:
1. Wie vandaag bellen
2. Welke werksoorten hoogste vraag hebben
3. Concreet actieadvies
Data:
{samenvatting}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "Analyseer bouwbedrijven voor personeelsvraag."},
                {"role": "user", "content": prompt}
            ],
            timeout=30
        )
        return response.choices[0].message.content
    except Exception:
        return "⚠️ AI tijdelijk niet beschikbaar."


# ========================
# AI SECTIE
# ========================
st.divider()
st.subheader("🤖 AI-analyse & advies")

if st.button("🔍 Analyseer met AI"):
    with st.spinner("AI denkt na..."):
        try:
            advies = ai_analyse_met_openai(df)
            st.markdown(advies)
        except Exception as e:
            st.error("AI-analyse mislukt. Controleer je API-key.")
            st.code(str(e))

# ========================
# OVERZICHT
# ========================
st.subheader("📊 Overzicht")
if not df.empty:
    st.dataframe(df, use_container_width=True)
else:
    st.info("Nog geen data")
