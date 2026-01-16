import streamlit as st
import pandas as pd
import os
import requests
from datetime import date
from openai import OpenAI

# =====================================================
# FEATURE FLAGS (BELANGRIJK)
# =====================================================
USE_GOOGLE_SEARCH = False   # <-- later True zetten als je CC + Google hebt

# =====================================================
# CONFIG
# =====================================================
st.set_page_config(page_title="🧠 BouwVraag Radar", layout="wide")
DATA_FILE = "data.csv"
client = OpenAI()

# =====================================================
# SCORE LOGICA
# =====================================================
def bereken_score(projecten, vacatures, werksoort, fase, vacature_signaal=False):
    score = projecten * 5

    if vacatures == "Ja":
        score += 20

    if vacature_signaal:
        score += 25   # extra boost als er online vacatures zijn

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

# =====================================================
# DATA LADEN
# =====================================================
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
else:
    df = pd.DataFrame(columns=[
        "Bedrijf","Type","Werksoort","Projecten","Vacatures",
        "Fase","Online vacatures","Score","Prioriteit","Status",
        "Laatste contact","Volgende actie","Notitie"
    ])

# =====================================================
# UI – TITEL
# =====================================================
st.title("🧠 BouwVraag Radar")
st.caption("Radar voor échte personeelsvraag in de bouw")

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
vacatures = st.sidebar.selectbox("Vacatures bekend?", ["Nee","Ja"])
fase = st.sidebar.selectbox("Projectfase", ["Start","Piek","Afronding"])

online_vacatures = st.sidebar.checkbox(
    "Online vacatures gevonden (Indeed / Werken-bij)"
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

if st.sidebar.button("Opslaan"):
    if bedrijf.strip() == "":
        st.sidebar.error("❌ Bedrijfsnaam is verplicht")
    else:
        score = bereken_score(
            projecten,
            vacatures,
            werksoort,
            fase,
            vacature_signaal=online_vacatures
        )

        nieuw = {
            "Bedrijf": bedrijf,
            "Type": type_bedrijf,
            "Werksoort": werksoort,
            "Projecten": projecten,
            "Vacatures": vacatures,
            "Fase": fase,
            "Online vacatures": "Ja" if online_vacatures else "Nee",
            "Score": score,
            "Prioriteit": score_label(score),
            "Status": status,
            "Laatste contact": laatst_contact,
            "Volgende actie": volgende_actie,
            "Notitie": notitie
        }

        df = pd.concat([df, pd.DataFrame([nieuw])], ignore_index=True)
        df.to_csv(DATA_FILE, index=False)
        st.sidebar.success(f"✅ Opgeslagen (score {score}%)")

# =====================================================
# VANDAAG BELLEN
# =====================================================
st.subheader("📞 Vandaag bellen")

if not df.empty:
    bellen = df[df["Status"] == "Vandaag bellen"].sort_values(
        "Score", ascending=False
    )
    st.dataframe(bellen, use_container_width=True)
else:
    st.info("Nog geen bedrijven ingevoerd")

# =====================================================
# AI ANALYSE OP JE EIGEN DATA
# =====================================================
def ai_analyse_eigen_data(df):
    if df.empty:
        return "⚠️ Nog geen data beschikbaar."

    csv = df.head(50).to_csv(index=False)

    prompt = f"""
Je bent een Nederlandse recruitment- en salesanalist in de bouw.
Analyseer deze data en geef:
1. Wie vandaag gebeld moet worden
2. Welke werksoorten de hoogste vraag hebben
3. Concreet actieadvies

DATA:
{csv}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Analyseer personeelsvraag in de bouw."},
            {"role": "user", "content": prompt}
        ],
        timeout=30
    )

    return response.choices[0].message.content

st.divider()
st.subheader("🤖 AI-analyse (eigen data)")

if st.button("Analyseer met AI"):
    with st.spinner("AI denkt..."):
        st.markdown(ai_analyse_eigen_data(df))

# =====================================================
# GOOGLE PROGRAMMABLE SEARCH (LATER)
# =====================================================
def zoek_bedrijven_google(query):
    """
    WORDT PAS GEBRUIKT ALS:
    USE_GOOGLE_SEARCH = True
    én GOOGLE_API_KEY + GOOGLE_CX bestaan
    """
    if not USE_GOOGLE_SEARCH:
        return []

    if "GOOGLE_API_KEY" not in st.secrets or "GOOGLE_CX" not in st.secrets:
        st.warning("Google Search staat aan, maar keys ontbreken.")
        return []

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": st.secrets["GOOGLE_API_KEY"],
        "cx": st.secrets["GOOGLE_CX"],
        "q": query,
        "num": 10
    }

    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()

    resultaten = []
    for item in data.get("items", []):
        resultaten.append({
            "naam": item.get("title"),
            "link": item.get("link"),
            "snippet": item.get("snippet", "")
        })

    return resultaten

# =====================================================
# OVERZICHT
# =====================================================
st.divider()
st.subheader("📊 Totaal overzicht")

if not df.empty:
    st.dataframe(df, use_container_width=True)
else:
    st.info("Nog geen data")

# =====================================================
# FOOTER
# =====================================================
st.caption(
    "BouwVraag Radar — Google‑klaar | Vacature‑gedreven | Geen nepbedrijven"
)
