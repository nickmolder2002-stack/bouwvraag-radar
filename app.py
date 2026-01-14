import streamlit as st
import pandas as pd
import os
from datetime import date

st.set_page_config(page_title="BouwVraag Radar", layout="wide")

DATA_FILE = "data.csv"

# ---------------- SCORE ----------------
def bereken_score(projecten, vacatures, werksoort, fase):
    score = 0
    score += projecten * 5
    if vacatures == "Ja":
        score += 20
    score += 15 if werksoort in ["Beton / Ruwbouw", "Prefab"] else 10
    score += {"Piek": 15, "Start": 10}.get(fase, 5)
    return min(score, 100)

def score_label(score):
    if score >= 70:
        return "🔴 Hoog"
    elif score >= 40:
        return "🟠 Middel"
    return "🟢 Laag"

# ---------------- DATA ----------------
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
else:
    df = pd.DataFrame(columns=[
        "Bedrijf", "Type", "Werksoort", "Projecten",
        "Vacatures", "Fase", "Score", "Prioriteit",
        "Status", "Laatste contact", "Volgende actie", "Notitie"
    ])

# ---------------- UI ----------------
st.title("🧠 BouwVraag Radar")

st.sidebar.header("➕ Nieuw bedrijf")
bedrijf = st.sidebar.text_input("Bedrijfsnaam")
type_bedrijf = st.sidebar.selectbox("Type bedrijf", ["Aannemer", "Prefab", "Onderhoud"])
werksoort = st.sidebar.selectbox("Werksoort", ["Timmerman", "Beton / Ruwbouw", "Prefab"])
projecten = st.sidebar.slider("Aantal projecten", 0, 10, 3)
vacatures = st.sidebar.selectbox("Vacatures actief?", ["Nee", "Ja"])
fase = st.sidebar.selectbox("Projectfase", ["Start", "Piek", "Afronding"])
status = st.sidebar.selectbox("Status", ["Vandaag bellen", "Deze week", "Later", "Klaar"])
laatst_contact = st.sidebar.date_input("Laatste contact", value=date.today())
volgende_actie = st.sidebar.text_input("Volgende actie")
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
        "Prioriteit": score_label(score),
        "Status": status,
        "Laatste contact": laatst_contact,
        "Volgende actie": volgende_actie,
        "Notitie": notitie
    }
    df = pd.concat([df, pd.DataFrame([nieuw])], ignore_index=True)
    df.to_csv(DATA_FILE, index=False)
    st.success(f"Opgeslagen ✅ Score: {score}")

# ---------------- OVERZICHT ----------------
st.subheader("📞 Vandaag bellen")
if not df.empty:
    vandaag = df[df["Status"] == "Vandaag bellen"].sort_values("Score", ascending=False)
    st.dataframe(vandaag, use_container_width=True)
else:
    st.info("Nog geen data")

st.subheader("📊 Volledig overzicht")
if not df.empty:
    volgorde = {"Vandaag bellen": 1, "Deze week": 2, "Later": 3, "Klaar": 4}
    df["Sort"] = df["Status"].map(volgorde)
    df = df.sort_values(by=["Sort", "Score"], ascending=[True, False])
    st.dataframe(df.drop(columns=["Sort"]), use_container_width=True)
else:
    st.info("Nog geen bedrijven ingevoerd")
