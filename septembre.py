import streamlit as st
import pandas as pd
import plotly.express as px
from data_processing import load_prepared_data

def apply_custom_style():
    st.markdown("""
        <style>
        /* Style pour les boîtes */
        .stMetric {
            background-color: #f0f2f6;
            padding: 10px;
            border-radius: 8px;
            box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.1);
        }
        /* Style pour chaque boîte d'ancienneté */
        .box-container {
            background-color: #e0f7fa;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            text-align: center;
        }
        .mono-order {
            color: #00796b;
            font-weight: bold;
        }
        .percent {
            color: #0288d1;
            font-weight: bold;
        }
        </style>
    """, unsafe_allow_html=True)

apply_custom_style()

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

    # Appliquer le style personnalisé pour les boîtes
apply_custom_style()

    # Afficher les boîtes pour chaque groupe d'ancienneté avec des conteneurs stylisés
    col1, col2, col3, col4, col5 = st.columns(5)
    for idx, col in enumerate([col1, col2, col3, col4, col5]):
        groupe = seniority_labels[idx]
        row = seniority_stats[seniority_stats['Groupe ancienneté'] == groupe]
        if not row.empty:
            total = int(row['Restaurant ID'].values[0])  # Total des clients
            mono = int(row['Jours avec commande'].values[0])  # Mono-orders
            percent_mono = (mono / total) * 100 if total > 0 else 0  # Pourcentage de mono-orders
        
            # Utilisation de conteneurs HTML pour styliser les boîtes
            with col:
                st.markdown(f"""
                    <div class="box-container">
                        <div>{groupe}</div>
                        <div><span>Total:</span> <strong>{total}</strong></div>
                        <div><span class="mono-order">Mono-orders:</span> <strong>{mono}</strong></div>
                        <div><span class="percent">% Mono-order:</span> <strong>{percent_mono:.1f}%</strong></div>
                    </div>
                """, unsafe_allow_html=True)



    # Tableau des clients mono-order
    st.subheader("Clients Mono-order")
    mono_clients = september_clients[september_clients['Jours avec commande'] == 1][['Restaurant ID', 'Restaurant', 'Code Postal', 'date 1ere commande (Restaurant)', 'Ancienneté']]
    mono_clients['Ancienneté'] = mono_clients['Ancienneté'].astype(int)
    
    # Affichage du tableau des clients mono-order
    st.dataframe(mono_clients)

if __name__ == "__main__":
    main()
