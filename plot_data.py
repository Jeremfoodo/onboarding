import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Charger et filtrer les données pour les clients français entre le 1er janvier 2024 et aujourd'hui
def load_and_filter_data(df):
    # Exclure les commandes et paiements annulés
    to_exclude_commande = ['CANCELLED', 'ABANDONED', 'FAILED', 'WAITING']
    to_exclude_paiement = ['CANCELLED', 'ERROR']
    
    df = df[~df['Statut commande'].isin(to_exclude_commande)]
    df = df[~df['Statut paiement'].isin(to_exclude_paiement)]
    df = df[~df['Canal'].str.contains('trading', case=False, na=False)]
    
    # Filtrer les commandes à partir du 1er janvier 2024
    df['Date de commande'] = pd.to_datetime(df['Date de commande'], errors='coerce')
    df = df[df['Date de commande'] >= pd.Timestamp('2024-01-01')]
    
    # Supprimer les enregistrements sans date de première commande
    df = df.dropna(subset=['date 1ere commande (Restaurant)'])
    
    # Ne garder que les clients français
    clients_fr = df[df['Pays'] == 'FR']
    
    # Obtenir la date de première commande et le pays pour chaque client
    clients = clients_fr.groupby('Restaurant ID').agg({
        'date 1ere commande (Restaurant)': 'first',
        'Pays': 'first'
    }).reset_index()
    clients.rename(columns={'date 1ere commande (Restaurant)': 'Date 1ère commande'}, inplace=True)
    
    # Convertir 'Date 1ère commande' en datetime si ce n'est pas déjà fait
    clients['Date 1ère commande'] = pd.to_datetime(clients['Date 1ère commande'], errors='coerce')
    
    # Ne garder que les clients dont la première commande est en 2024
    clients = clients[(clients['Date 1ère commande'] >= pd.Timestamp('2024-01-01')) &
                      (clients['Date 1ère commande'] <= pd.Timestamp.today())]
    
    # Calculer le nombre de jours distincts avec des commandes pour chaque client
    order_days = df.groupby('Restaurant ID')['Date de commande'].apply(lambda x: x.dt.normalize().nunique()).reset_index()
    order_days.rename(columns={'Date de commande': 'Jours avec commande'}, inplace=True)
    
    # Fusionner avec le DataFrame des clients
    clients = clients.merge(order_days, on='Restaurant ID', how='left')
    
    # Ajouter le mois de la première commande
    clients['Mois 1ère commande'] = clients['Date 1ère commande'].dt.to_period('M')
    
    return clients

import pandas as pd
import plotly.graph_objects as go

# Charger et filtrer les données et préparer les clients multi-commande
def load_multi_order_clients(df):
    df['Date de commande'] = pd.to_datetime(df['Date de commande'], errors='coerce')
    df = df[df['Date de commande'] >= pd.Timestamp('2024-01-01')]
    
    # Ne garder que les clients ayant passé leur première commande entre le 1er janvier et le 1er juin 2024
    df = df[(df['date 1ere commande (Restaurant)'] >= pd.Timestamp('2024-01-01')) & 
            (df['date 1ere commande (Restaurant)'] <= pd.Timestamp('2024-06-01'))]
    
    df = df.dropna(subset=['date 1ere commande (Restaurant)'])
    
    # Obtenir les clients avec plus d'une commande (multi-commande)
    clients = df.groupby('Restaurant ID').agg({
        'date 1ere commande (Restaurant)': 'first',
        'Date de commande': lambda x: x.dt.normalize().nunique()  # Nombre de jours distincts avec commandes
    }).reset_index()
    
    multi_order_clients = clients[clients['Date de commande'] > 1]
    
    # Joindre les clients multi-commande avec leurs dates de commande
    df_multi_order = df[df['Restaurant ID'].isin(multi_order_clients['Restaurant ID'])]
    
    # Calculer le nombre de jours entre la première et la deuxième commande
    second_order_days = df_multi_order.groupby('Restaurant ID').apply(
        lambda x: (x['Date de commande'].dt.normalize().drop_duplicates().sort_values().iloc[1] -
                   x['Date de commande'].dt.normalize().drop_duplicates().sort_values().iloc[0]).days
    ).reset_index()
    
    second_order_days.columns = ['Restaurant ID', 'Days to 2nd order']
    
    # Fusionner les données des clients multi-commande avec les jours jusqu'à la deuxième commande
    multi_order_clients = multi_order_clients.merge(second_order_days, on='Restaurant ID', how='left')
    
    return multi_order_clients

# Générer la courbe du pourcentage de clients passant à la deuxième commande
def plot_second_order_curve(multi_order_clients):
    # Créer les données cumulatives pour tracer la courbe
    total_clients = len(multi_order_clients)
    multi_order_clients_60_days = multi_order_clients[multi_order_clients['Days to 2nd order'] <= 60]
    
    # Créer les données cumulatives jour par jour
    cumulative_data = multi_order_clients_60_days['Days to 2nd order'].value_counts().sort_index().cumsum() / total_clients * 100
    
    # Créer le graphique interactif avec Plotly
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=cumulative_data.index,
        y=cumulative_data.values,
        mode='lines+markers',
        marker=dict(size=8),
        name="Pourcentage de clients",
        line=dict(color='royalblue', width=2)
    ))
    
    # Ajouter le layout
    fig.update_layout(
        title="Pourcentage de clients passant à la deuxième commande",
        xaxis_title="Temps jusqu'à la deuxième commande (jours)",
        yaxis_title="% de clients passés à multi-achats",
        xaxis=dict(tickmode='linear', dtick=5),
        yaxis=dict(range=[0, 100]),
        hovermode="x unified"
    )
    
    return fig


