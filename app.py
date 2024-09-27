import streamlit as st
import historique
import home

# Configuration de la page
st.set_page_config(page_title="Application Onboarding", page_icon="📊", layout="wide")

# Barre de navigation en haut
page = st.selectbox(
    "Navigation", 
    ["Accueil", "Historique"],
    index=0,
    key="navigation"
)

# Rediriger vers la page sélectionnée
if page == "Accueil":
    home.main()
elif page == "Historique":
    historique.main()
