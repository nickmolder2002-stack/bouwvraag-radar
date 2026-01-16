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

GOOGLE_ENABLED = (
    "GOOGLE_API_KEY" in st.secrets and
    "GOOGLE_CX" in st.secrets
)

# =====================================================
# SCORE + BESLISSER LOGICA
# =====================================================
def bereken_score(projecten, vacatures, werksoort, fase, vacature_signalen):
    score = projecten * 5

    if vacatures == "Ja":
        score += 20

    if vacature_signalen > 0:
        score += min(vacature_signalen * 10, 30)

    if werksoort in ["Beton / Ruwbouw", "Prefab"]:
        score += 15

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
    return "🟢 Laag"


def bepaal_beslisser(type_bedrijf):
    mapping = {
        "Hoofdaannemer": "Projectleider / Hoofd uitvoering",
        "Onderaannemer": "Directeur / Bedrijfsleider",
        "Prefab beton producent": "Productiemanager",
        "Modulaire woningbouw": "Operationeel manager",
        "Toelevering / Werkplaats": "Werkplaatschef",
        "Afbouw": "Uitvoerder"
    }
    return mapping.get(type_bedrijf, "Directie")

# =====================================================
# DATA LADEN
# =====================================================
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
else:
    df = pd.DataFrame(columns=[
        "Bedrijf","Type","Werksoort","Projecten",
        "Vacatures","Vacature signalen",
        "Fase","Score","Prioriteit",
        "Beslisser","Status",
        "Laatste contact","Volgende actie","Notitie"
    ])

# =====================================================
# UI – TITEL
# =====================================================
st.title("🧠 BouwVraag Radar")

# =====================================================
# SIDEBAR – BEDRIJF TOEVOEGEN
# =====================================================
st.sidebar.header("➕ Nieuw bedrijf")

bedrijf = st.sidebar.text_input("Bedrijfsnaam")
type_bedrijf = st.sidebar.selectbox(
    "Type bedrijf",
    [
        "Hoofdaannemer",
        "Onderaannemer",
        "Prefab beton producent",
        "Modulaire woningbouw",
        "Toelevering / Werkplaats",
        "Afbouw"
    ]
)

werksoort = st.sidebar.selectbox(
    "Werksoort",
    ["Timmerman","Beton / Ruwbouw","Prefab"]
)

projecten = st.sidebar.slider("Aantal projecten", 0, 10, 3)
vacatures = st.sidebar.selectbox("Vacatures actief?", ["Nee","Ja"])
vacature_signalen = st.sidebar.number_input(
    "Online vacature signalen (Indeed / Werkenbij)",
    0, 10, 0
)

fase = st.sidebar.selectbox(
    "Projectfase",
    ["Start","Piek","Afronding"]
)

status = st.sidebar.selectbox(
    "Status",
    ["Vandaag bellen","Deze week","Later","Klaar"]
)

laatst_contact = st.sidebar.date_input(
    "Laatste contact",
    value=date.today()
)

volgende_actie = st.sidebar.text_input("Volgende actie")
notitie = st.sidebar.text_area("Notitie")

if st.sidebar.button("💾 Opslaan"):
    if bedrijf.strip() == "":
        st.sidebar.error("Bedrijfsnaam is verplicht")
    else:
        score = bereken_score(
            projecten, vacatures, werksoort,
            fase, vacature_signalen
        )

        nieuw = {
            "Bedrijf": bedrijf,
            "Type": type_bedrijf,
            "Werksoort": werksoort,
            "Projecten": projecten,
            "Vacatures": vacatures,
            "Vacature signalen": vacature_signalen,
            "Fase": fase,
            "Score": score,
            "Prioriteit": score_label(score),
            "Beslisser": bepaal_beslisser(type_bedrijf),
            "Status": status,
            "Laatste contact": laatst_contact,
            "Volgende actie": volgende_actie,
            "Notitie": notitie
        }

        df = pd.concat([df, pd.DataFrame([nieuw])], ignore_index=True)
        df.to_csv(DATA_FILE, index=False)
        st.sidebar.success(f"Opgeslagen – score {score}%")

# =====================================================
# VANDAAG BELLEN
# =====================================================
st.subheader("📞 Vandaag bellen")

if df.empty:
    st.info("Nog geen bedrijven ingevoerd")
else:
    bellen = df[df["Status"] == "Vandaag bellen"] \
        .sort_values("Score", ascending=False)

    st.dataframe(bellen, use_container_width=True)

# =====================================================
# GOOGLE ZOEKEN (OPTIONEEL)
# =====================================================
def google_zoek(query, max_results=5):
    if not GOOGLE_ENABLED:
        return []

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": st.secrets["GOOGLE_API_KEY"],
        "cx": st.secrets["GOOGLE_CX"],
        "q": query,
        "num": max_results
    }

    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()

    return [
        {
            "naam": item.get("title"),
            "link": item.get("link"),
            "snippet": item.get("snippet", "")
        }
        for item in data.get("items", [])
    ]

# =====================================================
# MARKTVERKENNING
# =====================================================
st.divider()
st.subheader("🌍 Marktverkenning (echte bedrijven)")

zoekterm = st.text_input("Zoekterm (bv. prefab beton fabriek)")
regio = st.text_input("Regio", "Nederland")

if st.button("🔍 Zoek bedrijven"):
    if not GOOGLE_ENABLED:
        st.warning("Google is nog niet geactiveerd")
    else:
        with st.spinner("Zoeken..."):
            resultaten = google_zoek(f"{zoekterm} {regio}")

        if not resultaten:
            st.error("Geen resultaten")
        else:
            for r in resultaten:
                st.markdown(f"""
**{r['naam']}**  
{r['snippet']}  
🔗 {r['link']}
""")

# =====================================================
# OVERZICHT
# =====================================================
st.divider()
st.subheader("📊 Volledig overzicht")

if not df.empty:
    st.dataframe(df, use_container_width=True)
else:
    st.info("Nog geen data")
