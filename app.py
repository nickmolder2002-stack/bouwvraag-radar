import streamlit as st
import pandas as pd
import os
import requests
from datetime import date
from openai import OpenAI

# =========================================
# SUPERSNELLE CHECK (MAG BLIJVEN STAAN)
# =========================================
st.write("OpenAI key:", "OPENAI_API_KEY" in st.secrets)
st.write("Google key:", "GOOGLE_API_KEY" in st.secrets)
st.write("Google CX:", "GOOGLE_CX" in st.secrets)

# =========================================
# CONFIG
# =========================================
st.set_page_config(page_title="🧠 BouwVraag Radar", layout="wide")
DATA_FILE = "data.csv"
client = OpenAI()

# =========================================
# SCORE LOGICA
# =========================================
def bereken_score(projecten, vacatures, werksoort, fase):
    score = projecten * 5
    if vacatures == "Ja":
        score += 20
    if werksoort in ["Beton / Ruwbouw", "Prefab"]:
        score += 15
    score += 15 if fase == "Piek" else 10 if fase == "Start" else 5
    return min(score, 100)

def score_label(score):
    if score >= 70:
        return "🔴 Hoog"
    elif score >= 40:
        return "🟠 Middel"
    return "🟢 Laag"

# =========================================
# DATA LADEN
# =========================================
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
else:
    df = pd.DataFrame(columns=[
        "Bedrijf","Type","Werksoort","Projecten","Vacatures",
        "Fase","Score","Prioriteit","Status",
        "Laatste contact","Volgende actie","Notitie"
    ])

# =========================================
# UI
# =========================================
st.title("🧠 BouwVraag Radar")

st.sidebar.header("➕ Nieuw bedrijf")
bedrijf = st.sidebar.text_input("Bedrijfsnaam")
type_bedrijf = st.sidebar.selectbox(
    "Type",
    [
        "Hoofdaannemer",
        "Onderaannemer",
        "Prefab beton producent",
        "Modulaire woningbouw",
        "Toelevering / Werkplaats",
        "Afbouw"
    ]
)
werksoort = st.sidebar.selectbox("Werksoort", ["Timmerman","Beton / Ruwbouw","Prefab"])
projecten = st.sidebar.slider("Projecten", 0, 10, 3)
vacatures = st.sidebar.selectbox("Vacatures", ["Nee","Ja"])
fase = st.sidebar.selectbox("Fase", ["Start","Piek","Afronding"])
status = st.sidebar.selectbox("Status", ["Vandaag bellen","Deze week","Later","Klaar"])
laatst_contact = st.sidebar.date_input("Laatste contact", value=date.today())
volgende_actie = st.sidebar.text_input("Volgende actie")
notitie = st.sidebar.text_area("Notitie")

if st.sidebar.button("Opslaan"):
    score = bereken_score(projecten, vacatures, werksoort, fase)
    df = pd.concat([df, pd.DataFrame([{
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
    }])])
    df.to_csv(DATA_FILE, index=False)
    st.success("Opgeslagen")

st.subheader("📞 Vandaag bellen")
st.dataframe(df[df["Status"] == "Vandaag bellen"].sort_values("Score", ascending=False))

