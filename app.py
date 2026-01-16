import streamlit as st
import pandas as pd
import os
from datetime import date
from openai import OpenAI

# =====================================================
# CONFIG
# =====================================================
st.set_page_config(page_title="🧠 BouwVraag Radar", layout="wide")
DATA_FILE = "data.csv"
client = OpenAI()

# =====================================================
# VACATURE INTELLIGENTIE
# =====================================================
FUNCTIE_KEYWORDS = {
    "Timmerman": ["timmerman", "timmerlieden"],
    "Beton / Ruwbouw": ["beton", "ruwbouw", "bekisting", "vlecht"],
    "Prefab": ["prefab", "elementen", "productie"]
}

URGENTIE_WOORDEN = [
    "per direct", "dringend", "spoed", "meteen",
    "meerdere", "uitbreiding", "groei"
]

def analyseer_vacature(tekst):
    tekst = tekst.lower()
    gevonden_functies = []
    urgentie_score = 0

    for functie, woorden in FUNCTIE_KEYWORDS.items():
        if any(w in tekst for w in woorden):
            gevonden_functies.append(functie)

    for woord in URGENTIE_WOORDEN:
        if woord in tekst:
            urgentie_score += 1

    if urgentie_score >= 3:
        druk = "Hoog"
    elif urgentie_score == 2:
        druk = "Middel"
    elif urgentie_score == 1:
        druk = "Laag"
    else:
        druk = "Onbekend"

    return (
        ", ".join(gevonden_functies) if gevonden_functies else "Onbekend",
        druk,
        urgentie_score
    )

# =====================================================
# SCORE & LOGICA
# =====================================================
def bereken_score(projecten, vacatures, fase, urgentie_score):
    score = projecten * 5
    if vacatures == "Ja":
        score += 20
    score += urgentie_score * 10
    score += 15 if fase == "Piek" else 10 if fase == "Start" else 5
    return min(score, 100)

def score_label(score):
    if score >= 70:
        return "🔴 Hoog"
    if score >= 40:
        return "🟠 Middel"
    return "🟢 Laag"

def beladvies(score, vacature_druk):
    if score >= 70 or vacature_druk == "Hoog":
        return "DIRECT bellen"
    if vacature_druk == "Middel":
        return "Vandaag / morgen bellen"
    if score >= 40:
        return "Verkennend gesprek"
    return "Monitoren"

# =====================================================
# DATA
# =====================================================
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
else:
    df = pd.DataFrame(columns=[
        "Bedrijf","Type","Projecten","Fase","Vacatures",
        "Vacature functies","Vacature druk",
        "Score","Prioriteit","Beladvies",
        "Laatste contact","Notitie"
    ])

# =====================================================
# UI
# =====================================================
st.title("🧠 BouwVraag Radar")

st.sidebar.header("➕ Nieuw bedrijf")
bedrijf = st.sidebar.text_input("Bedrijfsnaam")
type_bedrijf = st.sidebar.selectbox(
    "Type bedrijf",
    [
        "Hoofdaannemer","Onderaannemer","Prefab beton producent",
        "Modulaire woningbouw","Toelevering / Werkplaats","Afbouw"
    ]
)
projecten = st.sidebar.slider("Aantal projecten", 0, 10, 3)
fase = st.sidebar.selectbox("Projectfase", ["Start","Piek","Afronding"])
vacatures = st.sidebar.selectbox("Vacatures actief?", ["Nee","Ja"])

vacature_tekst = st.sidebar.text_area(
    "Vacaturetekst (Indeed / Werken‑bij)",
    help="Plak hier 1 of meerdere vacatureteksten"
)

laatst_contact = st.sidebar.date_input("Laatste contact", value=date.today())
notitie = st.sidebar.text_area("Notitie")

if st.sidebar.button("Opslaan"):
    functies, druk, urgentie_score = analyseer_vacature(vacature_tekst)
    score = bereken_score(projecten, vacatures, fase, urgentie_score)

    nieuw = {
        "Bedrijf": bedrijf,
        "Type": type_bedrijf,
        "Projecten": projecten,
        "Fase": fase,
        "Vacatures": vacatures,
        "Vacature functies": functies,
        "Vacature druk": druk,
        "Score": score,
        "Prioriteit": score_label(score),
        "Beladvies": beladvies(score, druk),
        "Laatste contact": laatst_contact,
        "Notitie": notitie
    }

    df = pd.concat([df, pd.DataFrame([nieuw])], ignore_index=True)
    df.to_csv(DATA_FILE, index=False)
    st.success("✅ Slim opgeslagen met vacature‑analyse")

# =====================================================
# OVERZICHT
# =====================================================
st.subheader("📞 Belprioriteit")
st.dataframe(
    df.sort_values("Score", ascending=False),
    use_container_width=True
)
