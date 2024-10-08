import streamlit as st
import pandas as pd
import plotly.express as px
from data_processing import load_prepared_data
from plot_data import plot_second_order_curve

def main():
    st.title("Suivi de Septembre 2024")

    # Charger les données
    df = load_prepared_data()
    
    # Filtrer les clients ayant passé leur première commande en septembre 2024
    df['Date de commande'] = pd.to_datetime(df['Date de commande'])
    df['date 1ere commande (Restaurant)'] = pd.to_datetime(df['date 1ere commande (Restaurant)'], errors='coerce')
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

    # Filtrer les clients multi-order de janvier à juin 2024 (base historique)
    base_clients = df[(df['date 1ere commande (Restaurant)'] >= pd.Timestamp('2024-01-01')) & 
                      (df['date 1ere commande (Restaurant)'] <= pd.Timestamp('2024-06-30'))]

    # Calculer les jours de commande pour la base historique
    base_order_days = base_clients.groupby('Restaurant ID')['Date de commande'].apply(lambda x: x.dt.normalize().nunique()).reset_index()
    base_order_days.rename(columns={'Date de commande': 'Jours avec commande'}, inplace=True)
    base_clients = base_clients.merge(base_order_days, on='Restaurant ID', how='left')

    # Filtrer les multi-order clients de la base historique
    multi_base_clients = base_clients[base_clients['Jours avec commande'] > 1]

    # Calculer le temps nécessaire pour la deuxième commande pour la base historique
    second_order_base = multi_base_clients.groupby('Restaurant ID').apply(
        lambda x: (x['Date de commande'].dt.normalize().drop_duplicates().sort_values().iloc[1] - 
                   x['Date de commande'].dt.normalize().sort_values().iloc[0]).days
    ).reset_index()
    second_order_base.columns = ['Restaurant ID', 'Days to 2nd order']

    # Filtrer les clients multi-order de septembre 2024
    multi_september_clients = september_clients[september_clients['Jours avec commande'] > 1]

    # Calculer le temps nécessaire pour la deuxième commande pour septembre 2024
    second_order_september = multi_september_clients.groupby('Restaurant ID').apply(
        lambda x: (x['Date de commande'].dt.normalize().drop_duplicates().sort_values().iloc[1] - 
                   x['Date de commande'].dt.normalize().sort_values().iloc[0]).days
    ).reset_index()
    second_order_september.columns = ['Restaurant ID', 'Days to 2nd order']

    # Créer le graphique avec deux lignes
    fig_second_order = plot_second_order_curve(second_order_base, second_order_september)
    st.plotly_chart(fig_second_order, use_container_width=True)

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
    september_clients['Ancienneté'] = (pd.Timestamp.today() - september_clients['date 1ere commande (Restaurant)']).dt.days

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
            total = int(row['Restaurant ID'].values[0])  # Total des clients
            mono = int(row['Jours avec commande'].values[0])  # Mono-orders
            percent_mono = (mono / total) * 100 if total > 0 else 0  # Pourcentage de mono-orders
                
            # Format plus clair avec trois lignes dans chaque boîte
            col.metric(label=groupe, value=f"Total: {total}", 
                        delta=f"Mono: {mono} ({percent_mono:.1f}%)", 
                        delta_color="off")

    # Tableau des clients mono-order
    st.subheader("Clients Mono-order")
    mono_clients = september_clients[september_clients['Jours avec commande'] == 1][['Restaurant ID', 'Restaurant', 'Postal code', 'date 1ere commande (Restaurant)', 'Ancienneté']]
    mono_clients['Ancienneté'] = mono_clients['Ancienneté'].astype(int)
    
    # Affichage du tableau des clients mono-order
    st.dataframe(mono_clients)

if __name__ == "__main__":
    main()
