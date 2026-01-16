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

GOOGLE_ENABLED = "GOOGLE_API_KEY" in st.secrets and "GOOGLE_CX" in st.secrets

# =====================================================
# SCORE & INTELLIGENTIE
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
    if score >= 40:
        return "🟠 Middel"
    return "🟢 Laag"

def bepaal_beslisser(type_bedrijf):
    mapping = {
        "Hoofdaannemer": ("Hoofd Uitvoering", "Projectleiding"),
        "Onderaannemer": ("Bedrijfsleider", "Directie"),
        "Prefab beton producent": ("Productiemanager", "Operations"),
        "Modulaire woningbouw": ("Operations manager", "Directie"),
        "Toelevering / Werkplaats": ("Werkplaatsmanager", "Productie"),
        "Afbouw": ("Projectcoördinator", "Uitvoering"),
    }
    return mapping.get(type_bedrijf, ("Onbekend", "Onbekend"))

def genereer_beladvies(score, vacatures):
    if score >= 70:
        return "Direct bellen – hoge druk"
    if vacatures == "Ja":
        return "Warm bellen – vacatures actief"
    if score >= 40:
        return "Verkennend gesprek"
    return "Monitoren"

def verklaar_interesse(rij):
    redenen = []
    if rij["Score"] >= 70:
        redenen.append("Hoge score")
    if rij["Vacatures"] == "Ja":
        redenen.append("Actieve vacatures")
    if rij["Fase"] == "Piek":
        redenen.append("Projectpiek")
    if rij["Werksoort"] in ["Beton / Ruwbouw", "Prefab"]:
        redenen.append("Knelpunt-werksoort")
    return " | ".join(redenen) if redenen else "Geen directe druk"

# =====================================================
# DATA
# =====================================================
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
else:
    df = pd.DataFrame(columns=[
        "Bedrijf","Type","Werksoort","Projecten","Vacatures","Fase",
        "Score","Prioriteit","Status",
        "Beslisser functie","Beslisser afdeling",
        "Beladvies","Waarom interessant",
        "Laatste contact","Volgende actie","Notitie"
    ])

# =====================================================
# UI — INPUT
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
werksoort = st.sidebar.selectbox("Werksoort", ["Timmerman","Beton / Ruwbouw","Prefab"])
projecten = st.sidebar.slider("Aantal projecten", 0, 10, 3)
vacatures = st.sidebar.selectbox("Vacatures actief?", ["Nee","Ja"])
fase = st.sidebar.selectbox("Projectfase", ["Start","Piek","Afronding"])
laatst_contact = st.sidebar.date_input("Laatste contact", value=date.today())
volgende_actie = st.sidebar.text_input("Volgende actie")
notitie = st.sidebar.text_area("Notitie")

if st.sidebar.button("Opslaan"):
    score = bereken_score(projecten, vacatures, werksoort, fase)
    prioriteit = score_label(score)
    beslisser_functie, beslisser_afdeling = bepaal_beslisser(type_bedrijf)
    beladvies = genereer_beladvies(score, vacatures)

    nieuw = {
        "Bedrijf": bedrijf,
        "Type": type_bedrijf,
        "Werksoort": werksoort,
        "Projecten": projecten,
        "Vacatures": vacatures,
        "Fase": fase,
        "Score": score,
        "Prioriteit": prioriteit,
        "Status": "Vandaag bellen" if score >= 70 else "Deze week",
        "Beslisser functie": beslisser_functie,
        "Beslisser afdeling": beslisser_afdeling,
        "Beladvies": beladvies,
        "Waarom interessant": "",
        "Laatste contact": laatst_contact,
        "Volgende actie": volgende_actie,
        "Notitie": notitie
    }

    df = pd.concat([df, pd.DataFrame([nieuw])], ignore_index=True)
    df["Waarom interessant"] = df.apply(verklaar_interesse, axis=1)
    df.to_csv(DATA_FILE, index=False)
    st.success("✅ Bedrijf slim opgeslagen")

# =====================================================
# DASHBOARDS
# =====================================================
st.subheader("📞 Vandaag bellen")
st.dataframe(
    df[df["Status"] == "Vandaag bellen"].sort_values("Score", ascending=False),
    use_container_width=True
)

st.divider()
st.subheader("🧠 Slim prioriteiten‑overzicht")
st.dataframe(
    df.sort_values("Score", ascending=False)[[
        "Bedrijf","Score","Prioriteit",
        "Beslisser functie","Beslisser afdeling",
        "Beladvies","Waarom interessant"
    ]],
    use_container_width=True
)

# =====================================================
# GOOGLE (OPTIONEEL – STAAT KLAAR)
# =====================================================
st.divider()
st.subheader("🌍 Marktverkenning (Google – optioneel)")

if not GOOGLE_ENABLED:
    st.info("Google is nog niet gekoppeld. App werkt volledig zonder.")
else:
    query = st.text_input("Zoekterm (bijv. prefab beton fabriek Randstad)")
    if st.button("Zoek bedrijven"):
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": st.secrets["GOOGLE_API_KEY"],
            "cx": st.secrets["GOOGLE_CX"],
            "q": query,
            "num": 10
        }
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        for item in r.json().get("items", []):
            st.markdown(f"**{item['title']}**  \n{item.get('snippet','')}")


