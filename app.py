iimport streamlit as st
import pandas as pd
import os
from datetime import date
from openai import OpenAI

# 🔍 SUPERSNEL TESTEN – TIJDELIJK
st.write("OpenAI key gevonden:", "OPENAI_API_KEY" in st.secrets)
st.write("Google key gevonden:", "GOOGLE_API_KEY" in st.secrets)
st.write("Google CX gevonden:", "GOOGLE_CX" in st.secrets)

# =====================================================
# CONFIG
# =====================================================
st.set_page_config(page_title="🧠 BouwVraag Radar", layout="wide")
DATA_FILE = "data.csv"
client = OpenAI()

# =====================================================
# SCORE LOGICA
# =====================================================
def bereken_score(projecten, vacatures, werksoort, fase):
    score = projecten * 5
    if vacatures == "Ja":
        score += 20
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
    else:
        return "🟢 Laag"

# =====================================================
# DATA LADEN
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
# TITEL
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
werksoort = st.sidebar.selectbox("Werksoort", ["Timmerman","Beton / Ruwbouw","Prefab"])
projecten = st.sidebar.slider("Aantal projecten", 0, 10, 3)
vacatures = st.sidebar.selectbox("Vacatures actief?", ["Nee","Ja"])
fase = st.sidebar.selectbox("Projectfase", ["Start","Piek","Afronding"])
status = st.sidebar.selectbox("Status", ["Vandaag bellen","Deze week","Later","Klaar"])
laatst_contact = st.sidebar.date_input("Laatste contact", value=date.today())
volgende_actie = st.sidebar.text_input("Volgende actie")
notitie = st.sidebar.text_area("Notitie")

if st.sidebar.button("Opslaan"):
    if bedrijf.strip() == "":
        st.sidebar.error("❌ Bedrijfsnaam is verplicht")
    else:
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
        st.sidebar.success(f"✅ Opgeslagen (score {score}%)")

# =====================================================
# VANDAAG BELLEN
# =====================================================
st.subheader("📞 Vandaag bellen")
if not df.empty:
    bellen = df[df["Status"] == "Vandaag bellen"].sort_values("Score", ascending=False)
    st.dataframe(bellen, use_container_width=True)
else:
    st.info("Nog geen bedrijven ingevoerd")

# =====================================================
# AI ANALYSE OP EIGEN DATA
# =====================================================
def ai_analyse_eigen_data(df):
    if df.empty:
        return "⚠️ Nog geen data."
    csv = df.head(50).to_csv(index=False)
    prompt = f"""
Je bent een Nederlandse recruitment- en salesanalist in de bouw.
Analyseer deze data en geef:
1. Wie vandaag bellen
2. Welke werksoorten hoogste vraag
3. Kort actieadvies
DATA:
{csv}
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Analyseer bouwbedrijven."},
            {"role": "user", "content": prompt}
        ],
        timeout=30
    )
    return response.choices[0].message.content

st.divider()
st.subheader("🤖 AI-analyse (eigen data)")
if st.button("Analyseer"):
    with st.spinner("AI denkt..."):
        st.markdown(ai_analyse_eigen_data(df))

# =====================================================
# SECTOR DEFINITIES (HARD)
# =====================================================
SECTOR_CONFIG = {
    "Prefab beton producent": {
        "zoektermen": [
            "prefab beton fabriek",
            "betonelementen fabriek",
            "prefab betonelementen productie"
        ],
        "uitsluiten": [
            "aannemer", "bouwbedrijf", "infra", "projectontwikkeling"
        ]
    },
    "Modulaire woningbouw": {
        "zoektermen": [
            "modulaire woningen fabriek",
            "woningmodules productie"
        ],
        "uitsluiten": ["aannemer", "bouwbedrijf"]
    },
    "Hoofdaannemer": {
        "zoektermen": ["hoofdaannemer bouw"],
        "uitsluiten": []
    },
    "Onderaannemer": {
        "zoektermen": ["ruwbouw specialist", "betononderaannemer"],
        "uitsluiten": []
    },
    "Toelevering / Werkplaats": {
        "zoektermen": ["beton wapening productie", "bouw toeleverancier"],
        "uitsluiten": []
    },
    "Afbouw": {
        "zoektermen": ["afbouwbedrijf", "gipswanden montage"],
        "uitsluiten": []
    }
}

# =====================================================
# GOOGLE ZOEKEN
# =====================================================
def zoek_bedrijven_google(query, max_results=10):
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

    resultaten = []
    for item in data.get("items", []):
        resultaten.append({
            "naam": item.get("title"),
            "link": item.get("link"),
            "snippet": item.get("snippet", "")
        })
    return resultaten

def valideer_bedrijf(bedrijf, sector):
    tekst = (bedrijf["naam"] + " " + bedrijf["snippet"]).lower()
    for woord in SECTOR_CONFIG[sector]["uitsluiten"]:
        if woord in tekst:
            return False
    return True

# =====================================================
# AI ANALYSE OP ECHTE BEDRIJVEN
# =====================================================
def analyseer_bedrijven_met_ai(bedrijven, sector, regio):
    context = ""
    for b in bedrijven:
        context += f"""
Bedrijf: {b['naam']}
Website: {b['link']}
Info: {b['snippet']}
"""
    prompt = f"""
Je bent een zeer kritische Nederlandse recruitmentanalist.
Gebruik UITSLUITEND deze bedrijven.
Verzin NIETS.
Geef per bedrijf:
- Personeelsbehoefte score (0-100)
- Urgentie
- Functies
- Wie beslist over inleen (functie, geen naam)
- Concreet beladvies
Sector: {sector}
Regio: {regio}
DATA:
{context}
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Analyseer echte bedrijven."},
            {"role": "user", "content": prompt}
        ],
        timeout=60
    )
    return response.choices[0].message.content

# =====================================================
# MARKTVERKENNING – ECHTE BEDRIJVEN
# =====================================================
st.divider()
st.subheader("🌍 AI Marktverkenning – échte bedrijven")

sector_keuze = st.selectbox("Sector", list(SECTOR_CONFIG.keys()))
regio_keuze = st.selectbox("Regio", [
    "Nederland","Randstad","Noord-Brabant","Gelderland","Zuid-Holland"
])

if st.button("🚀 Zoek & analyseer"):
    with st.spinner("Internet wordt onderzocht..."):
        alle = []
        for term in SECTOR_CONFIG[sector_keuze]["zoektermen"]:
            gevonden = zoek_bedrijven_google(f"{term} {regio_keuze}")
            for b in gevonden:
                if valideer_bedrijf(b, sector_keuze):
                    alle.append(b)

        uniek = {b["link"]: b for b in alle}.values()

        if not uniek:
            st.error("❌ Geen valide bedrijven gevonden.")
        else:
            st.markdown(analyseer_bedrijven_met_ai(list(uniek), sector_keuze, regio_keuze))

# =====================================================
# OVERZICHT
# =====================================================
st.divider()
st.subheader("📊 Totaal overzicht")
if not df.empty:
    st.dataframe(df, use_container_width=True)
else:
    st.info("Nog geen data")

