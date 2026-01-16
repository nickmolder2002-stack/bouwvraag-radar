import streamlit as st
import pandas as pd
import os
import requests
from datetime import date
from openai import OpenAI

# =====================================================
# BASIS CONFIG
# =====================================================
st.set_page_config(page_title="🧠 BouwVraag Radar", layout="wide")
DATA_FILE = "data.csv"
client = OpenAI()

# =====================================================
# SNELLE CHECK (MAG BLIJVEN)
# =====================================================
with st.sidebar.expander("🔑 Systeemcheck"):
    st.write("OpenAI:", "OPENAI_API_KEY" in st.secrets)
    st.write("Google API:", "GOOGLE_API_KEY" in st.secrets)
    st.write("Google CX:", "GOOGLE_CX" in st.secrets)

# =====================================================
# SCORE LOGICA
# =====================================================
def bereken_score(projecten, vacatures, fase):
    score = projecten * 6
    if vacatures:
        score += 25
    score += 15 if fase == "Piek" else 10 if fase == "Start" else 5
    return min(score, 100)

def score_label(score):
    if score >= 70:
        return "🔴 Hoog"
    if score >= 40:
        return "🟠 Middel"
    return "🟢 Laag"

# =====================================================
# DATA LADEN / INIT
# =====================================================
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
else:
    df = pd.DataFrame(columns=[
        "Bedrijf","Sector","Projecten","Vacatures",
        "Fase","Score","Prioriteit",
        "Laatste contact","Volgende actie","Notitie"
    ])

# =====================================================
# UI – TITEL
# =====================================================
st.title("🧠 BouwVraag Radar – échte bedrijven + vacatures")

# =====================================================
# SIDEBAR – HANDMATIG TOEVOEGEN
# =====================================================
st.sidebar.header("➕ Bedrijf toevoegen (handmatig)")
bedrijf = st.sidebar.text_input("Bedrijfsnaam")
sector = st.sidebar.selectbox("Sector", [
    "Hoofdaannemer",
    "Onderaannemer",
    "Prefab beton producent",
    "Modulaire woningbouw",
    "Toelevering / Werkplaats",
    "Afbouw"
])
projecten = st.sidebar.slider("Aantal projecten", 0, 10, 3)
vacatures_handmatig = st.sidebar.checkbox("Vacatures bekend?")
fase = st.sidebar.selectbox("Projectfase", ["Start","Piek","Afronding"])
laatst_contact = st.sidebar.date_input("Laatste contact", value=date.today())
volgende_actie = st.sidebar.text_input("Volgende actie")
notitie = st.sidebar.text_area("Notitie")

if st.sidebar.button("Opslaan"):
    if bedrijf.strip() == "":
        st.sidebar.error("Bedrijfsnaam verplicht")
    else:
        score = bereken_score(projecten, vacatures_handmatig, fase)
        nieuw = {
            "Bedrijf": bedrijf,
            "Sector": sector,
            "Projecten": projecten,
            "Vacatures": vacatures_handmatig,
            "Fase": fase,
            "Score": score,
            "Prioriteit": score_label(score),
            "Laatste contact": laatst_contact,
            "Volgende actie": volgende_actie,
            "Notitie": notitie
        }
        df = pd.concat([df, pd.DataFrame([nieuw])], ignore_index=True)
        df.to_csv(DATA_FILE, index=False)
        st.sidebar.success("✅ Opgeslagen")

# =====================================================
# GOOGLE SEARCH (ECHT)
# =====================================================
def google_search(query, max_results=10):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": st.secrets["GOOGLE_API_KEY"],
        "cx": st.secrets["GOOGLE_CX"],
        "q": query,
        "num": max_results
    }
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    return data.get("items", [])

# =====================================================
# VACATURE CHECK (Indeed + Werken bij)
# =====================================================
def heeft_vacatures(bedrijfsnaam):
    zoektermen = [
        f"{bedrijfsnaam} vacatures",
        f"{bedrijfsnaam} indeed",
        f"{bedrijfsnaam} werken bij"
    ]
    for term in zoektermen:
        res = google_search(term, max_results=3)
        for r in res:
            tekst = (r.get("title","") + r.get("snippet","")).lower()
            if "vacature" in tekst or "werken bij" in tekst:
                return True
    return False

# =====================================================
# MARKTVERKENNING – ÉCHTE BEDRIJVEN
# =====================================================
st.divider()
st.subheader("🌍 Marktverkenning – échte bedrijven + vacatures")

sector_keuze = st.selectbox("Sector zoeken", [
    "Prefab beton producent",
    "Modulaire woningbouw",
    "Hoofdaannemer",
    "Onderaannemer",
    "Afbouw",
    "Toelevering / Werkplaats"
])

regio = st.selectbox("Regio", [
    "Nederland","Randstad","Zuid-Holland","Noord-Brabant","Gelderland"
])

if st.button("🚀 Zoek bedrijven"):
    with st.spinner("Zoeken & valideren…"):
        zoekterm = f"{sector_keuze} {regio}"
        resultaten = google_search(zoekterm, max_results=15)

        valide_bedrijven = []
        for r in resultaten:
            naam = r.get("title","")
            if len(naam) < 4:
                continue
            vacatures = heeft_vacatures(naam)
            score = bereken_score(3, vacatures, "Start")
            valide_bedrijven.append({
                "Bedrijf": naam,
                "Sector": sector_keuze,
                "Projecten": 3,
                "Vacatures": vacatures,
                "Fase": "Start",
                "Score": score,
                "Prioriteit": score_label(score),
                "Laatste contact": "",
                "Volgende actie": "Bellen",
                "Notitie": r.get("snippet","")
            })

        if valide_bedrijven:
            df = pd.concat([df, pd.DataFrame(valide_bedrijven)], ignore_index=True)
            df.to_csv(DATA_FILE, index=False)
            st.success(f"✅ {len(valide_bedrijven)} echte bedrijven toegevoegd")
        else:
            st.error("❌ Geen valide bedrijven gevonden")

# =====================================================
# OVERZICHTEN
# =====================================================
st.divider()
st.subheader("📞 Vandaag bellen")
st.dataframe(df[df["Prioriteit"] == "🔴 Hoog"].sort_values("Score", ascending=False),
             use_container_width=True)

st.divider()
st.subheader("📊 Totaal overzicht")
st.dataframe(df.sort_values("Score", ascending=False), use_container_width=True)

# =====================================================
# AI ANALYSE (ALLEEN OP JE EIGEN DATA)
# =====================================================
def ai_analyse(df):
    csv = df.head(40).to_csv(index=False)
    prompt = f"""
Je bent een Nederlandse sales- en recruitmentstrateeg in de bouw.
Analyseer deze data:
- Wie vandaag bellen
- Waar zit de meeste vraag
- Kort actieadvies
DATA:
{csv}
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}],
        timeout=30
    )
    return response.choices[0].message.content

st.divider()
st.subheader("🤖 AI Analyse (op jouw data)")
if st.button("Analyseer"):
    with st.spinner("AI denkt…"):
        st.markdown(ai_analyse(df))
