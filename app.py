import streamlit as st
import pandas as pd
from datetime import date
import os

st.set_page_config(page_title="Bouwvraag Radar", layout="wide")

DATA_FILE = "bedrijven.csv"

# =========================
# HULPFUNCTIES
# =========================

def bereken_score(projecten, vacatures, werksoort, fase):
    score = 0
    score += projecten * 10
    score += vacatures * 15

    if fase == "Start":
        score += 20
    elif fase == "Uitvoering":
        score += 10

    if werksoort in ["Ruwbouw", "Prefab"]:
        score += 10

    return min(score, 100)


def score_kleur(score):
    if score >= 70:
        return "🔴 Hoog"
    elif score >= 40:
        return "🟠 Middel"
    else:
        return "🟢 Laag"


def vacature_signaal(vacatures):
    if vacatures >= 3:
        return "✅ Actief"
    elif vacatures > 0:
        return "🟠 Beperkt"
    else:
        return "❌ Geen"


# =========================
# DATA LADEN
# =========================

if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
else:
    df = pd.DataFrame(columns=[
        "Bedrijf", "Type", "Werksoort", "Projecten", "Vacatures",
        "Fase", "Score", "Prioriteit", "Vacature signaal",
        "Status", "Laatste contact", "Volgende actie", "Notitie"
    ])

# =========================
# SIDEBAR - INVOER
# =========================

st.sidebar.header("➕ Bedrijf toevoegen")

bedrijf = st.sidebar.text_input("Bedrijfsnaam")
type_bedrijf = st.sidebar.selectbox("Type bedrijf", ["Aannemer", "Installateur", "Prefab"])
werksoort = st.sidebar.selectbox("Werksoort", ["Ruwbouw", "Prefab", "Installatie", "Overig"])
projecten = st.sidebar.number_input("Aantal projecten", min_value=0, step=1)
vacatures = st.sidebar.number_input("Aantal vacatures", min_value=0, step=1)
fase = st.sidebar.selectbox("Projectfase", ["Start", "Uitvoering", "Afronding"])

status = st.sidebar.selectbox(
    "Status",
    ["Vandaag bellen", "Deze week", "Later", "Klaar"]
)

laatst_contact = st.sidebar.date_input("Laatste contact", value=date.today())
volgende_actie = st.sidebar.text_input("Volgende actie")
notitie = st.sidebar.text_area("Notitie")

if st.sidebar.button("💾 Opslaan"):
    score = bereken_score(projecten, vacatures, werksoort, fase)

    nieuw = {
        "Bedrijf": bedrijf,
        "Type": type_bedrijf,
        "Werksoort": werksoort,
        "Projecten": projecten,
        "Vacatures": vacatures,
        "Fase": fase,
        "Score": score,
        "Prioriteit": score_kleur(score),
        "Vacature signaal": vacature_signaal(vacatures),
        "Status": status,
        "Laatste contact": laatst_contact,
        "Volgende actie": volgende_actie,
        "Notitie": notitie
    }

    df = pd.concat([df, pd.DataFrame([nieuw])], ignore_index=True)
    df.to_csv(DATA_FILE, index=False)

    st.success(f"Opgeslagen ✅ Score: {score}")
    st.rerun()

# =========================
# OVERZICHT
# =========================

st.title("📊 Bouwvraag Radar")

if df.empty:
    st.info("Nog geen bedrijven ingevoerd")
else:
    volgorde = {
        "Vandaag bellen": 1,
        "Deze week": 2,
        "Later": 3,
        "Klaar": 4
    }

    df["Status_volgorde"] = df["Status"].map(volgorde)

    df_overzicht = df.sort_values(
        by=["Status_volgorde", "Score"],
        ascending=[True, False]
    )

    st.subheader("📞 Overzicht & prioriteit")
    st.dataframe(
        df_overzicht.drop(columns=["Status_volgorde"]),
        use_container_width=True
    )
