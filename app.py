import streamlit as st

# Configuration de la page principale
st.set_page_config(
    page_title="Application Onboarding",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Titre principal de l'application
st.title("Application Onboarding")

st.write("Utilisez le menu de navigation à gauche pour accéder aux différentes pages.")
st.write("Cette application permet de suivre les performances des clients en France.")

