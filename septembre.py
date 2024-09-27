import streamlit as st
import pandas as pd
import plotly.express as px
from data_processing import load_prepared_data

def main():
    st.title("Suivi de Septembre 2024")

    # Charger les données
    df = load_prepared_data()
    
    # Filtrer les clients ayant passé leur première commande en septembre 2024
    df['Date de commande'] = pd.to_datetime(df['Date de commande'])
    df['Date 1ere commande'] = pd.to_datetime(df['Date 1ere commande'], errors='coerce')
    september_clients = df[(df['date 1ere commande (Restaurant)'].dt.month == 9) & 
                           (df['date 1ere commande (Restaurant)'].dt.year == 2024) & 
                           (df['Pays'] == 'FR')]

    # Calculer les mono-achat et multi-achat
    order_days = september_clients.groupby('Restaurant ID')['Date de commande'].apply(lambda x: x.dt.normalize().nunique()).reset_index()
    order_days.rename(columns={'Date de commande': 'Jours avec commande'}, inplace=True)
    
    # Fusionner pour obtenir les mono et multi-order clients
    september_clients = september_clients.merge(order_days, on='Restaurant ID', how='left')
    mono_order_clients = len(september_clients[september_clients['Jours avec commande'] == 1])
    multi_order_clients = len(september_clients[september_clients['Jours avec commande'] > 1])
    total_clients = mono_order_clients + multi_order_clients
    percent_mono_order = (mono_order_clients / total_clients) * 100 if total_clients > 0 else 0

    # Créer un DataFrame pour le graphique empilé
    stacked_data = pd.DataFrame({
        'Type de client': ['Mono-order', 'Multi-order'],
        'Nombre de clients': [mono_order_clients, multi_order_clients]
    })

    # Graphique empilé des acquisitions
    fig = px.bar(stacked_data, 
                 x='Type de client', 
                 y='Nombre de clients', 
                 title="Acquisitions en septembre 2024 (FR)", 
                 labels={'Nombre de clients': 'Nombre de clients'},
                 text='Nombre de clients')
    
    fig.update_layout(barmode='stack')
    st.plotly_chart(fig, use_container_width=True)

    # Boîtes d'information pour mono/multi-orders
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Clients Mono-order", value=mono_order_clients)
    with col2:
        st.metric(label="Clients Multi-order", value=multi_order_clients)
    with col3:
        st.metric(label="% Mono-order", value=f"{percent_mono_order:.2f}%")

    # Segmentation par ancienneté
    st.subheader("Répartition par ancienneté")
    september_clients['Ancienneté'] = (pd.Timestamp.today() - september_clients['Date 1ere commande']).dt.days

    seniority_bins = [(0, 5), (5, 10), (10, 15), (15, 20), (20, float('inf'))]
    seniority_labels = ['0-5 jours', '5-10 jours', '10-15 jours', '15-20 jours', '> 20 jours']
    september_clients['Groupe ancienneté'] = pd.cut(september_clients['Ancienneté'], bins=[0, 5, 10, 15, 20, float('inf')], labels=seniority_labels)

    # Calculer les stats pour chaque groupe d'ancienneté
    seniority_stats = september_clients.groupby('Groupe ancienneté').agg({
        'Restaurant ID': 'count',
        'Jours avec commande': lambda x: (x == 1).sum(),  # Mono-orders
    }).reset_index()

    seniority_stats['% Mono-order'] = (seniority_stats['Jours avec commande'] / seniority_stats['Restaurant ID']) * 100

    # Afficher les boîtes pour chaque groupe d'ancienneté
    col1, col2, col3, col4, col5 = st.columns(5)
    for idx, col in enumerate([col1, col2, col3, col4, col5]):
        groupe = seniority_labels[idx]
        row = seniority_stats[seniority_stats['Groupe ancienneté'] == groupe]
        if not row.empty:
            total = int(row['Restaurant ID'].values[0])
            mono = int(row['Jours avec commande'].values[0])
            percent_mono = row['% Mono-order'].values[0]
            col.metric(label=groupe, value=total, delta=f"{mono} mono", help=f"{percent_mono:.2f}% mono-order")

    # Tableau des clients mono-order
    st.subheader("Clients Mono-order")
    mono_clients = september_clients[september_clients['Jours avec commande'] == 1][['Restaurant ID', 'Restaurant', 'Code Postal', 'Date 1ere commande', 'Ancienneté']]
    mono_clients['Ancienneté'] = mono_clients['Ancienneté'].astype(int)
    
    # Affichage du tableau des clients mono-order
    st.dataframe(mono_clients)

if __name__ == "__main__":
    main()
