import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="BouwVraag Radar", layout="wide")

DATA_FILE = "data.csv"

# Data laden of nieuw maken
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
else:
    df = pd.DataFrame(columns=["Bedrijf", "Type", "Rol", "Score", "Notitie"])

st.title("🧠 BouwVraag Radar")

# Sidebar invoer
st.sidebar.header("Nieuw bedrijf")

bedrijf = st.sidebar.text_input("Bedrijfsnaam")
type_bedrijf = st.sidebar.selectbox("Type", ["Aannemer", "Prefab", "Onderhoud"])
rol = st.sidebar.text_input("Gezochte rol")
score = st.sidebar.slider("Kans op behoefte (%)", 0, 100, 50)
notitie = st.sidebar.text_area("Notitie")

if st.sidebar.button("Opslaan"):
    nieuw = {
        "Bedrijf": bedrijf,
        "Type": type_bedrijf,
        "Rol": rol,
        "Score": score,
        "Notitie": notitie
    }
    df = pd.concat([df, pd.DataFrame([nieuw])], ignore_index=True)
    df.to_csv(DATA_FILE, index=False)
    st.success("Opgeslagen ✅")

# Vandaag bellen
st.subheader("📞 Vandaag bellen")
if not df.empty:
    vandaag = df.sort_values("Score", ascending=False).head(5)
    st.dataframe(vandaag, use_container_width=True)
else:
    st.info("Nog geen bedrijven ingevoerd")

# Alle bedrijven
st.subheader("📋 Alle bedrijven")
st.dataframe(df, use_container_width=True)
