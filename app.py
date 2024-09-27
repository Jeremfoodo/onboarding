import streamlit as st
import pandas as pd
from plot_data import load_and_filter_data, plot_mono_vs_multi_order
import matplotlib.pyplot as plt

# Charger les données (supposons que la fonction load_prepared_data() soit déjà définie)
from data_processing import load_prepared_data

# Créer l'application avec les onglets
def main():
    st.title("Application Onboarding")

    tab1, tab2 = st.tabs(["Accueil", "Suivi"])

    with tab2:
        st.header("Suivi")
        
        # Section historique
        st.subheader("Historique")
        st.write("Voici les infos sur le taux de mono-order des clients français.")
        
        # Charger les données et filtrer pour la France
        df = load_prepared_data()
        clients_fr = load_and_filter_data(df)
        
        # Afficher les graphiques
        fig = plot_mono_vs_multi_order(clients_fr)
        st.pyplot(fig)

if __name__ == "__main__":
    main()
