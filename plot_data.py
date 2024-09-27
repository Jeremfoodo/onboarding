import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
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

# Générer le graphique à barres empilées
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
                'Clients multi-achats': multi_order_clients,
                'Pourcentage mono-achat': round(percent_mono_order)
            })

    # Créer le DataFrame pour le graphique
    plot_data = pd.DataFrame(data_list)

    # Générer le graphique à barres empilées
    x_positions = np.arange(len(plot_data))
    
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(x_positions, plot_data['Clients mono-achat'], label='Clients mono-achat', color='#FFA07A')
    ax.bar(x_positions, plot_data['Clients multi-achats'], bottom=plot_data['Clients mono-achat'], label='Clients multi-achats', color='#20B2AA')
    
    ax.set_title("Évolution des nouveaux clients en France par mois")
    ax.set_xlabel('Mois')
    ax.set_ylabel('Nombre de nouveaux clients')
    ax.set_xticks(x_positions)
    ax.set_xticklabels(plot_data['Mois'].dt.strftime('%Y-%m'), rotation=45)
    
    # Ajouter le pourcentage de clients mono-achat au-dessus de chaque barre
    for i, row in plot_data.iterrows():
        total = row['Clients mono-achat'] + row['Clients multi-achats']
        if total > 0:
            percentage = row['Pourcentage mono-achat']
            ax.text(i, total + 0.5, f'{percentage:.0f}%', ha='center', va='bottom')

    plt.tight_layout()
    plt.legend(title='Type de client')

    return fig
