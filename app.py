import streamlit as st

st.set_page_config(page_title="BouwVraag Radar", layout="wide")

st.title("🧠 BouwVraag Radar")
st.write("Dagelijkse sales‑prioriteiten voor bouw & prefab")

st.sidebar.header("➕ Nieuw bedrijf")

naam = st.sidebar.text_input("Bedrijfsnaam")
type_bedrijf = st.sidebar.selectbox(
    "Type bedrijf",
    ["Aannemer", "Prefab / Productie"]
)

rollen = st.sidebar.multiselect(
    "Rollen",
    ["Timmerman", "Beton / Ruwbouw", "Prefab medewerker"]
)

score = st.sidebar.slider("Vraagscore", 0, 100, 50)
notitie = st.sidebar.text_area("Notitie")

if "bedrijven" not in st.session_state:
    st.session_state.bedrijven = []

if st.sidebar.button("Opslaan"):
    st.session_state.bedrijven.append({
        "naam": naam,
        "type": type_bedrijf,
        "rollen": ", ".join(rollen),
        "score": score,
        "notitie": notitie
    })
    st.sidebar.success("Bedrijf toegevoegd")

st.subheader("🔥 Vandaag bellen")

hoog = [b for b in st.session_state.bedrijven if b["score"] >= 70]

for b in sorted(hoog, key=lambda x: x["score"], reverse=True)[:5]:
    st.markdown(f"""
**{b['naam']}** — Score {b['score']}  
Rollen: {b['rollen']}  
Type: {b['type']}  
Notitie: {b['notitie']}
---
""")

st.subheader("📊 Alle bedrijven")

for b in st.session_state.bedrijven:
    st.markdown(f"""
**{b['naam']}**  
Type: {b['type']}  
Rollen: {b['rollen']}  
Score: {b['score']}  
Notitie: {b['notitie']}
---
""")
