import streamlit as st
import pandas as pd
import os
from datetime import date
from openai import OpenAI

# ========================
# CONFIG
# ========================
st.set_page_config(page_title="BouwVraag Radar", layout="wide")
DATA_FILE = "data.csv"

# OpenAI client (leest OPENAI_API_KEY automatisch uit Streamlit Secrets)
client = OpenAI()

# ========================
# SCORE LOGICA
# ========================
def bereken_score(projecten, vacatures, werksoort, fase):
    score = projecten * 5
    if vacatures == "Ja":
        score += 20
    score += 15 if werksoort in ["Beton / Ruwbouw", "Prefab"] else 10
    score += 15 if fase == "Piek" else 10 if fase == "Start" else 5
    return min(score, 100)

def score_label(score):
    if score >= 70:
        return "🔴 Hoog"
    elif score >= 40:
        return "🟠 Middel"
    else:
        return "🟢 Laag"

# ========================
# DATA LADEN
# ========================
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
else:
    df = pd.DataFrame(columns=[
        "Bedrijf","Type","Werksoort","Projecten","Vacatures",
        "Fase","Score","Prioriteit","Status",
        "Laatste contact","Volgende actie","Notitie"
    ])

# ========================
# TITEL
# ========================
st.title("🧠 BouwVraag Radar")

# ========================
# SIDEBAR – INPUT
# ========================
st.sidebar.header("➕ Nieuw bedrijf")

bedrijf = st.sidebar.text_input("Bedrijfsnaam")
type_bedrijf = st.sidebar.selectbox("Type bedrijf", ["Aannemer","Prefab","Onderhoud"])
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
        st.sidebar.success(f"✅ Opgeslagen (score: {score}%)")

# ========================
# VANDAAG BELLEN
# ========================
st.subheader("📞 Vandaag bellen")

if not df.empty:
    bellen = df[df["Status"] == "Vandaag bellen"].sort_values("Score", ascending=False)
    st.dataframe(bellen, use_container_width=True)
else:
    st.info("Nog geen bedrijven ingevoerd")

# ========================
# AI ANALYSE (STABIEL & VEILIG)
# ========================
def ai_analyse_met_openai(df):
    if df.empty:
        return "⚠️ Nog geen data beschikbaar voor AI-analyse."

    try:
        samenvatting = df.head(50).to_csv(index=False)
    except Exception:
        return "⚠️ Data kon niet worden gelezen."

    prompt = f"""
Je bent een ervaren sales- en recruitment-analist in de bouwsector.

Analyseer de onderstaande data en geef:
1. Wie moet vandaag gebeld worden
2. Welke werksoorten de hoogste vraag hebben
3. Concreet en kort actieadvies

Data:
{samenvatting}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Je analyseert bouwbedrijven voor personeelsvraag."},
                {"role": "user", "content": prompt}
            ],
            timeout=30
        )
        return response.choices[0].message.content

    except Exception as e:
        return "⚠️ AI tijdelijk niet beschikbaar. Controleer API-key of probeer later."

# ========================
# AI SECTIE
# ========================
st.divider()
st.subheader("🤖 AI-analyse & advies")

if st.button("🔍 Analyseer met AI"):
    with st.spinner("AI denkt na..."):
        advies = ai_analyse_met_openai(df)
        st.markdown(advies)

# ========================
# OVERZICHT
# ========================
st.subheader("📊 Totaal overzicht")

if not df.empty:
    st.dataframe(df, use_container_width=True)
else:
    st.info("Nog geen data beschikbaar")

# ========================
# AI MARKTVERKENNING – PREFAB BETON (SECTOR-ZUIVER)
# ========================
st.divider()
st.subheader("🏭 AI Marktverkenning – Prefab beton FABRIEKEN met personeelsbehoefte")

sector_input = st.selectbox(
    "Kies specialisatie",
    ["Prefab beton"]
)

regio_input = st.selectbox(
    "Regio",
    ["Nederland", "Randstad", "Noord-Brabant", "Gelderland", "Zuid-Holland"]
)

if st.button("🚀 Zoek prefab beton fabrieken"):
    with st.spinner("AI onderzoekt uitsluitend échte prefab beton producenten..."):
        try:
            prompt = f"""
Je bent een Nederlandse industrie-, productie- en recruitmentanalist.

ZEER BELANGRIJK – HARD FILTER:
- Neem UITSLUITEND bedrijven mee die ZELF prefab betonelementen PRODUCEREN
- Bedrijven MOETEN een eigen fabriek hebben
- Sluit AANNEMERS, PROJECTONTWIKKELAARS en BOUWBEDRIJVEN expliciet uit
- Bedrijven zoals Heijmans, BAM, Dura Vermeer zijn VERBODEN

Definitie prefab beton producent:
- Eigen productielocatie
- Structurele fabricage van prefab betonelementen
- Levert aan aannemers
- Geen hoofdaannemer

Taak:
1. Selecteer alleen échte prefab beton FABRIEKEN in Nederland
2. Beoordeel per bedrijf of er personeelsbehoefte is
3. Rangschik op waarschijnlijkheid van wervingsnood

Geef een TOP 10 in EXACT dit formaat:

Bedrijf:
Type: Prefab beton producent
Waarom dit GEEN aannemer is:
Personeelsbehoefte-score (0–100):
Urgentie (Hoog/Middel/Laag):
Welke functies:
Waarom personeel nodig:
Concreet beladvies:
Regio: {regio_input}

Twijfel = NIET opnemen.
"""

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Je bent een kritische Nederlandse prefab beton industrie-analist."},
                    {"role": "user", "content": prompt}
                ],
                timeout=60
            )

            st.markdown(response.choices[0].message.content)

        except Exception as e:
            st.error("❌ AI Marktverkenning mislukt.")
            st.code(str(e))

    if sector_input.strip() == "":
        st.warning("Vul een sector of specialisatie in.")
    else:
        with st.spinner("AI onderzoekt de markt..."):
            try:
                prompt = f"""
Je bent een zeer ervaren markt- en recruitmentanalist in Nederland.

Taak:
1. Zoek bestaande Nederlandse bedrijven binnen de sector: {sector_input}
2. Beoordeel per bedrijf of er waarschijnlijk personeel nodig is
3. Gebruik signalen zoals:
   - Vacatures
   - Groei of uitbreiding
   - Projectdruk
   - Moeilijk te vervullen functies
4. Geef een TOP 10 van bedrijven met de hoogste personeelsbehoefte

Per bedrijf wil ik exact dit formaat:

Bedrijf:
Sector:
Personeelsbehoefte-score (0–100):
Urgentie (Hoog/Middel/Laag):
Waarom personeel nodig:
Welke functie(s):
Concreet beladvies:

Regio-focus: {regio_input}

Wees realistisch, zakelijk en concreet.
"""

                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "Je bent een Nederlandse bouw- en recruitmentanalist."},
                        {"role": "user", "content": prompt}
                    ],
                    timeout=60
                )

                resultaat = response.choices[0].message.content
                st.markdown(resultaat)

            except Exception as e:
                st.error("❌ AI Marktverkenning mislukt.")
                st.code(str(e))
