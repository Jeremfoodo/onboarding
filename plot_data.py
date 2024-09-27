import pandas as pd
import plotly.graph_objects as go

# Fonction pour filtrer les clients français et préparer les données pour mono vs multi-commande
def load_and_filter_data(df):
    # Assurer que les colonnes de dates sont bien en datetime
    df['Date de commande'] = pd.to_datetime(df['Date de commande'], errors='coerce')
    df['date 1ere commande (Restaurant)'] = pd.to_datetime(df['date 1ere commande (Restaurant)'], errors='coerce')
    
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
    
    # Ne garder que les clients ayant une première commande en 2024
    clients = clients[(clients['Date 1ère commande'] >= pd.Timestamp('2024-01-01')) &
                      (clients['Date 1ère commande'] <= pd.Timestamp.today())]
    
    # Ajouter le mois de la première commande
    clients['Mois 1ère commande'] = clients['Date 1ère commande'].dt.to_period('M')
    
    return clients



# Fonction pour créer un graphique interactif Plotly pour mono vs multi-order
def plot_mono_vs_multi_order(clients):
    months = pd.period_range(start='2024-01', end=pd.Timestamp.today(), freq='M')
    
    data_list = []
    for month in months:
        month_clients = clients[clients['Mois 1ère commande'] == month]
        mono_order_clients = len(month_clients[month_clients['Jours avec commande'] == 1])
        multi_order_clients = len(month_clients[month_clients['Jours avec commande'] > 1])
        total_clients = mono_order_clients + multi_order_clients
        percent_mono_order = (mono_order_clients / total_clients) * 100 if total_clients > 0 else 0
        data_list.append({
            'Mois': month.to_timestamp(),
            'Clients mono-achat': mono_order_clients,
            'Clients multi-achats': multi_order_clients,
            'Pourcentage mono-achat': percent_mono_order
        })

    plot_data = pd.DataFrame(data_list)

    fig = go.Figure(data=[
        go.Bar(name='Clients mono-achat', x=plot_data['Mois'], y=plot_data['Clients mono-achat'], marker_color='#FFA07A', text=plot_data['Pourcentage mono-achat'], texttemplate='%{text:.2f}%', textposition='outside'),
        go.Bar(name='Clients multi-achats', x=plot_data['Mois'], y=plot_data['Clients multi-achats'], marker_color='#20B2AA')
    ])
    
    fig.update_layout(
        barmode='stack',
        title="Évolution des nouveaux clients en France (Mono-achat vs Multi-achats)",
        xaxis_title="Mois",
        yaxis_title="Nombre de nouveaux clients",
        xaxis_tickformat='%Y-%m',
        legend_title="Type de client",
        hovermode="x"
    )
    
    return fig

# Fonction pour charger et filtrer les clients multi-commandes
def load_multi_order_clients(df):
    # Assurer que les colonnes de dates sont bien en datetime
    df['Date de commande'] = pd.to_datetime(df['Date de commande'], errors='coerce')
    df['date 1ere commande (Restaurant)'] = pd.to_datetime(df['date 1ere commande (Restaurant)'], errors='coerce')
    
    # Ne garder que les clients ayant passé leur première commande entre le 1er janvier et le 1er juin 2024
    df = df[(df['date 1ere commande (Restaurant)'] >= pd.Timestamp('2024-01-01')) & 
            (df['date 1ere commande (Restaurant)'] <= pd.Timestamp('2024-06-01'))]
    
    # Supprimer les enregistrements sans date de première commande
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


# Fonction pour tracer la courbe du pourcentage de clients passant à la deuxième commande
def plot_second_order_curve(multi_order_clients):
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
