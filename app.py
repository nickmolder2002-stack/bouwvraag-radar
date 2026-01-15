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

# 🔑 ZET HIER JE API KEY
client = OpenAI(api_key="PLAK_HIER_JE_API_SLEUTEL")

# ========================
# SCORE LOGICA
# ========================
def bereken_score(projecten, vacatures, werksoort, fase):
    score = 0
    score += projecten * 5
    if vacatures == "Ja":
        score += 20
    if werksoort in ["Beton / Ruwbouw", "Prefab"]:
        score += 15
    else:
        score += 10
    if fase == "Piek":
        score += 15
    elif fase == "Start":
        score += 10
    else:
        score += 5
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
# SIDEBAR – NIEUW BEDRIJF
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
    if bedrijf.strip():
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
        st.sidebar.success("Opgeslagen ✅")

# ========================
# OVERZICHT
# ========================
st.subheader("📊 Overzicht")
if not df.empty:
    st.dataframe(df, use_container_width=True)
else:
    st.info("Nog geen data")

# ========================
# 🤖 ECHTE AI ANALYSE
# ========================
def ai_analyse(df):
    samenvatting = df[[
        "Werksoort","Fase","Score","Prioriteit","Status"
    ]].to_csv(index=False)

    prompt = f"""
Je bent een ervaren recruiter in de bouwsector.

Analyseer onderstaande data en geef:
1. Waar zit de hoogste kans op vraag naar vakkrachten?
2. Welke werksoorten moet vandaag gebeld worden?
3. Concreet beladvies in duidelijke taal.

Data:
{samenvatting}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}]
    )

    return response.choices[0].message.content

st.divider()
st.subheader("🤖 AI‑advies")

if st.button("🔍 Analyseer met AI"):
    with st.spinner("AI analyseert je data..."):
        advies = ai_analyse(df)
        st.markdown(advies)
