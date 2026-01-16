import streamlit as st
import pandas as pd
import os
import requests
from datetime import date
from openai import OpenAI

# ==============================
# CONFIG
# ==============================
st.set_page_config(page_title="🧠 BouwVraag Radar", layout="wide")
DATA_FILE = "data.csv"
client = OpenAI()

# ==============================
# HULPFUNCTIES
# ==============================
def website_bestaat(url):
    try:
        r = requests.get(url, timeout=5)
        return r.status_code == 200
    except:
        return False

def detecteer_vacature_signalen(bedrijfsnaam):
    """
    Legitieme vacature-detectie:
    - check werken-bij pagina
    - check vacature keywords
    """
    signalen = []
    basis_urls = [
        f"https://www.{bedrijfsnaam.replace(' ', '').lower()}.nl/werken-bij",
        f"https://www.{bedrijfsnaam.replace(' ', '').lower()}.nl/vacatures"
    ]

    for url in basis_urls:
        if website_bestaat(url):
            signalen.append("Werken-bij pagina")

    return signalen

# ==============================
# SCORE LOGICA
# ==============================
def bereken_score(projecten, vacatures_gevonden, werksoort, fase):
    score = 0

    # Vacatures (hard bewijs)
    score += min(len(vacatures_gevonden) * 20, 40)

    # Projectdruk
    score += projecten * 3
    score += 15 if fase == "Piek" else 10 if fase == "Start" else 5

    # Werksoort match
    if werksoort in ["Beton / Ruwbouw", "Prefab"]:
        score += 20
    else:
        score += 10

    return min(score, 100)

def score_label(score):
    if score >= 70:
        return "🔴 Hoog"
    elif score >= 40:
        return "🟠 Middel"
    return "🟢 Laag"

# =========================================
# BESLISSER & BELADVIES LOGICA
# =========================================
def bepaal_beslisser(type_bedrijf):
    mapping = {
        "Hoofdaannemer": ("Hoofd Uitvoering", "Projectleiding"),
        "Onderaannemer": ("Bedrijfsleider", "Directie"),
        "Prefab beton producent": ("Productiemanager", "Operations"),
        "Modulaire woningbouw": ("Operations manager", "Directie"),
        "Toelevering / Werkplaats": ("Werkplaatsmanager", "Productie"),
        "Afbouw": ("Projectcoördinator", "Uitvoering")
    }
    return mapping.get(type_bedrijf, ("Onbekend", "Onbekend"))

def genereer_beladvies(score, vacature_signalen):
    if score >= 70:
        return "Direct bellen: hoge projectdruk en personeelsbehoefte"
    if vacature_signalen and vacature_signalen != "Geen":
        return "Warm bellen: actieve vacature-signalen gevonden"
    if score >= 40:
        return "Verkennend gesprek plannen"
    return "Lage prioriteit – monitoren"


# ==============================
# DATA LADEN
# ==============================
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
else:
  df = pd.DataFrame(columns=[
    "Bedrijf","Type","Werksoort","Projecten","Vacatures",
    "Fase","Vacature_signalen",
    "Score","Prioriteit","Status",
    "Beslisser","Beladvies",
    "Laatste contact","Volgende actie","Notitie"
])


# ==============================
# UI
# ==============================
st.title("🧠 BouwVraag Radar")

st.sidebar.header("➕ Nieuw bedrijf")
bedrijf = st.sidebar.text_input("Bedrijfsnaam (exact)")
type_bedrijf = st.sidebar.selectbox("Type", [
    "Hoofdaannemer","Onderaannemer","Prefab beton producent",
    "Modulaire woningbouw","Toelevering / Werkplaats","Afbouw"
])
werksoort = st.sidebar.selectbox("Werksoort", ["Timmerman","Beton / Ruwbouw","Prefab"])
projecten = st.sidebar.slider("Aantal projecten", 0, 10, 3)
fase = st.sidebar.selectbox("Fase", ["Start","Piek","Afronding"])
status = st.sidebar.selectbox("Status", ["Vandaag bellen","Deze week","Later","Klaar"])
laatst_contact = st.sidebar.date_input("Laatste contact", value=date.today())
notitie = st.sidebar.text_area("Notitie")

if st.sidebar.button("Opslaan"):
    score = bereken_score(projecten, vacatures, werksoort, fase)

    beslisser_functie, beslisser_afdeling = bepaal_beslisser(type_bedrijf)

    beladvies = genereer_beladvies(
        score=score,
        vacature_signalen=vacatures
    )

    auto_status = "Vandaag bellen" if score >= 70 else status

    df = pd.concat([df, pd.DataFrame([{
        "Bedrijf": bedrijf,
        "Type": type_bedrijf,
        "Werksoort": werksoort,
        "Projecten": projecten,
        "Vacatures": vacatures,
        "Fase": fase,
        "Score": score,
        "Prioriteit": score_label(score),
        "Status": auto_status,
        "Laatste contact": laatst_contact,
        "Volgende actie": volgende_actie,
        "Notitie": notitie,
        "Beslisser functie": beslisser_functie,
        "Beslisser afdeling": beslisser_afdeling,
        "Beladvies": beladvies
    }])], ignore_index=True)

    df.to_csv(DATA_FILE, index=False)
    st.sidebar.success(f"✅ Opgeslagen — advies: {beladvies}")


    df = pd.concat([df, pd.DataFrame([nieuw])], ignore_index=True)
    df.to_csv(DATA_FILE, index=False)
    st.sidebar.success(f"✅ Opgeslagen — score {score}%")

# ==============================
# OVERZICHT
# ==============================
st.subheader("📞 Vandaag bellen")
st.dataframe(
    df[df["Status"] == "Vandaag bellen"].sort_values("Score", ascending=False),
    use_container_width=True
)

st.subheader("📊 Alle bedrijven")
st.dataframe(df.sort_values("Score", ascending=False), use_container_width=True)
