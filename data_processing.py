import pandas as pd
import gdown
import os
import streamlit as st

# URLs des fichiers Google Drive
prepared_data_url = 'https://drive.google.com/uc?id=1krOrcWcYr2F_shA4gUYZ1AQFsuWja9dM'
google_sheets_url = 'https://drive.google.com/uc?id=1sv6E1UsMV3fe-T_3p94uAUt1kz4xlXZA'

@st.cache_data
def download_files():
    data_dir = 'data'
    os.makedirs(data_dir, exist_ok=True)
    
    # Chemins locaux pour les fichiers téléchargés
    output_prepared = os.path.join(data_dir, 'prepared_data.csv')
    output_google_sheets = os.path.join(data_dir, 'google_sheets_data.xlsx')
    
    # Télécharger les fichiers s'ils n'existent pas encore
    if not os.path.exists(output_prepared):
        gdown.download(prepared_data_url, output_prepared, quiet=False)
    if not os.path.exists(output_google_sheets):
        gdown.download(google_sheets_url, output_google_sheets, quiet=False)

@st.cache_data
def load_prepared_data():
    data_dir = 'data'
    download_files()
    
    # Charger et filtrer les données CSV
    df = pd.read_csv(os.path.join(data_dir, 'prepared_data.csv'), parse_dates=['Date de commande'], decimal='.')
    
    # Filtrer à partir du 1er janvier 2024
    df_filtered = df[df['Date de commande'] >= '2024-01-01']
    
    return df_filtered

@st.cache_data
def load_google_sheets_data():
    data_dir = 'data'
    download_files()
    
    # Charger les données du fichier Google Sheets
    df_google_sheets = pd.read_excel(os.path.join(data_dir, 'google_sheets_data.xlsx'), engine='openpyxl')
    
    return df_google_sheets
