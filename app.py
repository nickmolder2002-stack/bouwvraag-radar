import streamlit as st
import pandas as pd
import os
import requests
from datetime import date
from openai import OpenAI

# =====================================================
# CONFIG
# =====================================================
st.set_page_config(page_title="🧠 BouwVraag Radar", layout="wide")
DATA_FILE = "data.csv"
client = OpenAI()

# =====================================================
# HULPFUNCTIES – VEILIGHEID (GEEN KEYERRORS)
# =====================================================
VERPLICHTE_KOLOMMEN = [
    "Bedrijf","Type","Werksoort","Projecten","Vacatures",
    "Fase","Score","Prioriteit","Status",
    "Laatste contact","Volgende actie","Notitie",
    "Vacature signalen","Beslisser","Beladvies"
]

def normaliseer_dataframe(df):
    for kolom in VERPLICHTE_KOLOMMEN:
        if kolom not in df.columns:
            df[kolom] = ""
    return df

# =====================================================
# SCORE LOGICA
# =====================================================
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

# =====================================================
# BESLISSER LOGICA
# =====================================================
def bepaal_beslisser(type_bedrijf):
    mapping = {
        "Hoofdaannemer": "Projectleider / Werkvoorbereider",
        "Onderaannemer": "Bedrijfsleider",
        "Prefab beton producent": "Productiemanager",
        "Modulaire woningbouw": "Operations manager",
        "Toelevering / Werkplaats": "Planner",
        "Afbouw": "Uitvoerder"
    }
    return mapping.get(type_bedrijf, "Bedrijfsleider")

# =====================================================
# DATA LADEN
# =====================================================
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
else:
    df = pd.DataFrame()

df = normaliseer_dataframe(df)

# =====================================================
# UI – TITEL
# =====================================================
st.title("🧠 BouwVraag Radar")

# =====================================================
# SIDEBAR – NIEUW BEDRIJF
# =====================================================
st.sidebar.header("➕ Nieuw bedrijf")

bedrijf = st.sidebar.text_input("Bedrijfsnaam")
type_bedrijf = st.sidebar.selectbox("Type bedrijf", [
    "Hoofdaannemer","Onderaannemer","Prefab beton producent",
    "Modulaire woningbouw","Toelevering / Werkplaats","Afbouw"
])
werksoort = st.sidebar.selectbox("Werksoort", ["Timmerman","Beton / Ruwbouw","Prefab"])
projecten = st.sidebar.slider("Aantal projecten", 0, 10, 3)
vacatures = st.sidebar.selectbox("Vacatures actief?", ["Nee","Ja"])
fase = st.sidebar.selectbox("Projectfase", ["Start","Piek","Afronding"])
status = st.sidebar.selectbox("Status", ["Vandaag bellen","Deze week","Later","Klaar"])
laatst_contact = st.sidebar.date_input("Laatste contact", value=date.today())
volgende_actie = st.sidebar.text_input("Volgende actie")
notitie = st.sidebar.text_area("Notitie")

if st.sidebar.button("Opslaan"):
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
        "Notitie": notitie,
        "Vacature signalen": vacatures,
        "Beslisser": bepaal_beslisser(type_bedrijf),
        "Beladvies": "Inventarisatie + capaciteit check"
    }
    df = pd.concat([df, pd.DataFrame([nieuw])], ignore_index=True)
    df.to_csv(DATA_FILE, index=False)
    st.success("✅ Bedrijf opgeslagen")

# =====================================================
# VANDAAG BELLEN
# =====================================================
st.subheader("📞 Vandaag bellen")
st.dataframe(
    df[df["Status"] == "Vandaag bellen"].sort_values("Score", ascending=False),
    use_container_width=True
)

# =====================================================
# AUTOMATISCHE DAGPLANNING (C)
# =====================================================
st.divider()
st.subheader("🗓️ Slimme dagplanning")

def dagprioriteit(r):
    p = r["Score"]
    if r["Vacatures"] == "Ja":
        p += 15
    if r["Fase"] == "Piek":
        p += 10
    if r["Werksoort"] in ["Beton / Ruwbouw", "Prefab"]:
        p += 10
    return p

df["Dagprioriteit"] = df.apply(dagprioriteit, axis=1)

top = df.sort_values("Dagprioriteit", ascending=False).head(5)

for i, r in top.iterrows():
    st.markdown(f"""
### {r['Bedrijf']}
- 🎯 Score: {r['Score']}
- 👤 Beslisser: {r['Beslisser']}
- ☎️ Advies: **{r['Beladvies']}**
""")

# =====================================================
# OVERZICHT
# =====================================================
st.divider()
st.subheader("📊 Totaal overzicht")
st.dataframe(df, use_container_width=True)

