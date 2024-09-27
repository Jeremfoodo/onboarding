import streamlit as st
import home
import historique
import septembre  # Nouveau module pour l'onglet Septembre

# Configuration de la page
st.set_page_config(page_title="Application Onboarding", page_icon="📊", layout="wide")

# Barre de navigation en haut
page = st.selectbox(
    "Navigation", 
    ["Accueil", "Historique", "Septembre"],  # Ajout de "Septembre"
    index=0,
    key="navigation"
)

# Rediriger vers la page sélectionnée
if page == "Accueil":
    home.main()
elif page == "Historique":
    historique.main()
elif page == "Septembre":
    septembre.main()
