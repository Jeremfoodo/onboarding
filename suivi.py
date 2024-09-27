import streamlit as st
from plot_data import load_and_filter_data, plot_mono_vs_multi_order
from data_processing import load_prepared_data

def main():
    st.title("Suivi des clients")

    # Section historique
    st.subheader("Historique")
    st.write("Voici les infos sur le taux de mono-order des clients français.")

    # Charger les données et filtrer pour la France
    df = load_prepared_data()
    clients_fr = load_and_filter_data(df)

    # Afficher le graphique interactif avec Plotly
    fig = plot_mono_vs_multi_order(clients_fr)
    st.plotly_chart(fig)

if __name__ == "__main__":
    main()
