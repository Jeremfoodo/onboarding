import streamlit as st
from plot_data import load_and_filter_data, plot_mono_vs_multi_order, load_multi_order_clients, plot_second_order_curve
from data_processing import load_prepared_data

def main():
    st.title("Suivi des clients")

    # Section historique
    st.subheader("Historique")
    st.write("Voici les infos sur le taux de mono-order des clients français.")
    
    # Charger les données
    df = load_prepared_data()

    # Filtrer et afficher le graphique des clients mono vs multi-achat
    clients_fr = load_and_filter_data(df)
    fig_mono_vs_multi = plot_mono_vs_multi_order(clients_fr)
    st.plotly_chart(fig_mono_vs_multi)
    
    # Section deuxième commande
    st.subheader("Temps jusqu'à la deuxième commande")
    st.write("Temps nécessaire aux clients multi-catégories pour passer à leur deuxième commande (1er janvier - 1er juin 2024).")
    
    # Filtrer les clients multi-commande et afficher la courbe du temps jusqu'à la deuxième commande
    multi_order_clients = load_multi_order_clients(df)
    fig_second_order_curve = plot_second_order_curve(multi_order_clients)
    st.plotly_chart(fig_second_order_curve)

if __name__ == "__main__":
    main()
