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

# Générer un graphique interactif à barres empilées avec Plotly
def plot_mono_vs_multi_order(clients):
    # Préparer les données pour le graphique
    months = pd.period_range(start='2024-01', end=pd.Timestamp.today(), freq='M')
    
    data_list = []
    
    for month in months:
        month_clients = clients[clients['Mois 1ère commande'] == month]
        if not month_clients.empty:
            mono_order_clients = len(month_clients[month_clients['Jours avec commande'] == 1])
            multi_order_clients = len(month_clients[month_clients['Jours avec commande'] > 1])
            total_clients = mono_order_clients + multi_order_clients
            percent_mono_order = (mono_order_clients / total_clients) * 100 if total_clients > 0 else 0
            data_list.append({
                'Mois': month.to_timestamp(),
                'Clients mono-achat': mono_order_clients,
                'Clients multi-achats': multi_order_clients
            })

    # Créer le DataFrame pour le graphique
    plot_data = pd.DataFrame(data_list)

    # Créer le graphique à barres empilées avec Plotly
    fig = go.Figure(data=[
        go.Bar(name='Clients mono-achat', x=plot_data['Mois'], y=plot_data['Clients mono-achat'], marker_color='#FFA07A'),
        go.Bar(name='Clients multi-achats', x=plot_data['Mois'], y=plot_data['Clients multi-achats'], marker_color='#20B2AA')
    ])
    
    # Mettre à jour les paramètres du graphique
    fig.update_layout(
        barmode='stack',
        title="Évolution des nouveaux clients en France (Mono-achat vs Multi-achats)",
        xaxis_title="Mois",
        yaxis_title="Nombre de nouveaux clients",
        xaxis_tickformat='%Y-%m',
        legend_title="Type de client",
        hovermode="x"
    )
    
    # Ajouter des étiquettes sur les barres
    fig.update_traces(texttemplate='%{y}', textposition='inside')
    
    return fig
