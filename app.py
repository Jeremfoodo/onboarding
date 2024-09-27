import streamlit as st
from data_processing import load_prepared_data, load_google_sheets_data

def main():
    st.title("Application Onboarding")

    # Charger les données
    st.write("Téléchargement et filtrage des données à partir du 1er janvier 2024...")
    df_filtered = load_prepared_data()
    st.write("Données filtrées (à partir du 1er janvier 2024) :")
    st.dataframe(df_filtered)

    st.write("Téléchargement des données Google Sheets...")
    df_google_sheets = load_google_sheets_data()
    st.write("Données de Google Sheets :")
    st.dataframe(df_google_sheets)

if __name__ == "__main__":
    main()

