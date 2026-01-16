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
# SUPERSNELLE CHECK (MAG JE LATER VERWIJDEREN)
# =====================================================
st.write("✅ OpenAI key:", "OPENAI_API_KEY" in st.secrets)
st.write("✅ Google key:", "GOOGLE_API_KEY" in st.secrets)
st.write("✅ Google CX:", "GOOGLE_CX" in st.secrets)

# =====================================================
# SCORE LOGICA
# =====================================================
def bereken_score(projecten, vacatures, werksoort, fase):
    score = projecten * 5
    if vacatures == "Ja":
        score += 25
    if werksoort in ["Prefab", "Beton / Ruwbouw"]:
        score += 20
    if fase == "Piek":
        score += 20
    elif fase == "Start":
        score += 10
    return min(score, 100)

def score_label(score):
    if score >= 70:
        return "🔴 Hoog"
    elif score >= 40:
        return "🟠 Middel"
    return "🟢 Laag"

# =====================================================
# DATA
# =====================================================
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
else:
    df = pd.DataFrame(columns=[
        "Bedrijf","Type","Werksoort","Projecten","Vacatures",
        "Fase","Score","Prioriteit","Status",
        "Laatste contact","Volgende actie","Notitie"
    ])

# =====================================================
# UI
# =====================================================
st.title("🧠 BouwVraag Radar")

# =====================================================
# SIDEBAR INPUT
# =====================================================
st.sidebar.header("➕ Nieuw bedrijf")

bedrijf = st.sidebar.text_input("Bedrijfsnaam")
type_bedrijf = st.sidebar.selectbox(
    "Type",
    [
        "Prefab beton producent",
        "Modulaire woningbouw",
        "Hoofdaannemer",
        "Onderaannemer",
        "Toelevering / Werkplaats",
        "Afbouw"
    ]
)

werksoort = st.sidebar.selectbox("Werksoort", ["Prefab","Beton / Ruwbouw","Timmerman"])
projecten = st.sidebar.slider("Projecten", 0, 10, 3)
vacatures = st.sidebar.selectbox("Vacatures", ["Nee","Ja"])
fase = st.sidebar.selectbox("Fase", ["Start","Piek","Afronding"])
status = st.sidebar.selectbox("Status", ["Vandaag bellen","Deze week","Later","Klaar"])
laatst_contact = st.sidebar.date_input("Laatste contact", value=date.today())
volgende_actie = st.sidebar.text_input("Volgende actie")
notitie = st.sidebar.text_area("Notitie")

if st.sidebar.button("Opslaan"):
    if not bedrijf.strip():
        st.sidebar.error("Bedrijfsnaam verplicht")
    else:
        score = bereken_score(projecten, vacatures, werksoort, fase)
        df.loc[len(df)] = [
            bedrijf, type_bedrijf, werksoort, projecten, vacatures,
            fase, score, score_label(score), status,
            laatst_contact, volgende_actie, notitie
        ]
        df.to_csv(DATA_FILE, index=False)
        st.sidebar.success("Opgeslagen")

# =====================================================
# VANDAAG BELLEN
# =====================================================
st.subheader("📞 Vandaag bellen")
st.dataframe(df[df["Status"]=="Vandaag bellen"].sort_values("Score", ascending=False))

# =====================================================
# SECTOR DEFINITIES (KEIHARD)
# =====================================================
SECTOR_CONFIG = {
    "Prefab beton producent": {
        "zoektermen": [
            "prefab beton fabriek",
            "betonelementen fabriek",
            "prefab betonelementen productie"
        ],
        "vereist": ["fabriek", "productie", "beton"],
        "uitsluiten": ["aannemer", "bouwbedrijf", "infra"]
    }
}

# =====================================================
# GOOGLE SEARCH
# =====================================================
def google_zoek(query):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": st.secrets["GOOGLE_API_KEY"],
        "cx": st.secrets["GOOGLE_CX"],
        "q": query,
        "num": 10
    }
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    return r.json().get("items", [])

def valideer_bedrijf(item, sector):
    text = (item["title"] + " " + item.get("snippet","")).lower()

    for woord in SECTOR_CONFIG[sector]["uitsluiten"]:
        if woord in text:
            return False

    positief = any(w in text for w in SECTOR_CONFIG[sector]["vereist"])
    return positief and (".nl" in item["link"] or ".com" in item["link"])

# =====================================================
# MARKTVERKENNING (ALLEEN ECHT)
# =====================================================
st.divider()
st.subheader("🌍 Marktverkenning – 100% echte bedrijven")

sector = st.selectbox("Sector", list(SECTOR_CONFIG.keys()))
regio = st.selectbox("Regio", ["Nederland","Randstad","Noord-Brabant"])

if st.button("Zoek bedrijven"):
    met_data = []

    for term in SECTOR_CONFIG[sector]["zoektermen"]:
        results = google_zoek(f"{term} {regio}")
        for r in results:
            if valideer_bedrijf(r, sector):
                met_data.append({
                    "naam": r["title"],
                    "site": r["link"],
                    "info": r.get("snippet","")
                })

    uniek = {b["site"]: b for b in met_data}.values()

    if not uniek:
        st.error("❌ Geen echte bedrijven gevonden")
    else:
        context = ""
        for b in uniek:
            context += f"""
Bedrijf: {b['naam']}
Website: {b['site']}
Info: {b['info']}
"""

        prompt = f"""
Gebruik UITSLUITEND onderstaande bedrijven.
Verzin GEEN namen.
Analyseer personeelsbehoefte en geef:
- Score 0–100
- Urgentie
- Functies
- Beslisser (functie)
- Concreet beladvies

DATA:
{context}
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"user","content":prompt}],
            timeout=60
        )

        st.markdown(response.choices[0].message.content)

# =====================================================
# OVERZICHT
# =====================================================
st.divider()
st.subheader("📊 Overzicht")
st.dataframe(df, use_container_width=True)
