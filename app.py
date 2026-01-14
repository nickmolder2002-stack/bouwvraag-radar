import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="BouwVraag Radar", layout="wide")

DATA_FILE = "data.csv"

# Score berekening
def bereken_score(projecten, vacatures, werksoort, fase):
    score = 0

    # Projecten
    score += projecten * 5  # max 50

    # Vacatures
    if vacatures == "Ja":
        score += 20

    # Werksoort
    if werksoort in ["Beton / Ruwbouw", "Prefab"]:
        score += 15
    else:
        score += 10

    # Projectfase
    if fase == "Piek":
        score += 15
    elif fase == "Start":
        score += 10
    else:
        score += 5

    return min(score, 100)

# Data laden
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
else:
    df = pd.DataFrame(columns=[
        "Bedrijf", "Type", "Werksoort", "Projecten",
        "Vacatures", "Fase", "Score", "Notitie"
    ])

st.title("🧠 BouwVraag Radar")

# Sidebar
st.sidebar.header("Nieuw bedrijf")

bedrijf = st.sidebar.text_input("Bedrijfsnaam")
type_bedrijf = st.sidebar.selectbox("Type bedrijf", ["Aannemer", "Prefab", "Onderhoud"])
werksoort = st.sidebar.selectbox("Werksoort", ["Timmerman", "Beton / Ruwbouw", "Prefab"])
projecten = st.sidebar.slider("Aantal projecten", 0, 10, 3)
vacatures = st.sidebar.selectbox("Vacatures actief?", ["Nee", "Ja"])
fase = st.sidebar.selectbox("Projectfase", ["Start", "Piek", "Afronding"])
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
        "Notitie": notitie
    }

    df = pd.concat([df, pd.DataFrame([nieuw])], ignore_index=True)
    df.to_csv(DATA_FILE, index=False)
    st.success(f"Opgeslagen ✅ Score: {score}%")

# Vandaag bellen
st.subheader("📞 Vandaag bellen")
if not df.empty:
    vandaag = df.sort_values("Score", ascending=False).head(5)
    st.dataframe(vandaag, use_container_width=True)
else:
    st.info("Nog geen bedrijven ingevoerd")

# Alles
st.subheader("📋 Alle bedrijven")
st.dataframe(df, use_container_width=True)
import pandas as pd
import streamlit as st

# Lijst om data te bewaren in de sessie
if "resultaten" not in st.session_state:
    st.session_state.resultaten = []

# VOORBEELD: na berekening score
if st.button("Opslaan"):
    st.session_state.resultaten.append({
        "Bedrijf": bedrijf,
        "Score": score,
        "Keuze": keuze,
        "Datum": pd.Timestamp.now().strftime("%d-%m-%Y")
    })

st.divider()
st.subheader("📊 Overzicht")

if st.session_state.resultaten:
    df = pd.DataFrame(st.session_state.resultaten)
    st.dataframe(df, use_container_width=True)
else:
    st.info("Nog geen data opgeslagen.")
if st.button("Optie A"):
    st.session_state.bedrijven.append({
        "Bedrijf": "preco",
        "Type": "Prefab",
        "Rol": None,
        "Score": 50,
        "Notitie": None
    })

