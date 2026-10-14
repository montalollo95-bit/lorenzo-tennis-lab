import streamlit as st
import sqlite3
import pandas as pd
import subprocess
import sys

DB_PATH = "tennis_lab.db"

# 🎨 Configurazione Pagina
st.set_page_config(page_title="Laboratorio Pronostici Tennis AI", layout="wide", page_icon="🎾")

st.title("🎾 Laboratorio Pronostici Tennis AI")

# =====================================================================
# 🎛️ PANNELLO DI CONTROLLO (Come da tua immagine)
# =====================================================================
st.subheader("Pannello di Controllo")
col1, col2 = st.columns(2)

with col1:
    if st.button("📥 1. Scarica Partite di Domani", use_container_width=True):
        with st.spinner("Estrazione da Diretta.it in corso (richiede qualche secondo)..."):
            # Esegue lo script data_ingestion in modo silente
            subprocess.run([sys.executable, "data_ingestion.py"])
        st.success("✅ Palinsesto di domani scaricato e aggiornato!")
        st.rerun()

with col2:
    if st.button("🧠 2. Avvia Analisi AI (In Coda)", use_container_width=True):
        with st.spinner("Il Cervello AI sta analizzando i match in coda. Attendi..."):
            # Esegue lo script brain_agent in modo silente
            subprocess.run([sys.executable, "brain_agent.py"])
        st.success("✅ Analisi AI completata!")
        st.rerun()

st.markdown("---")

# =====================================================================
# 📊 GESTIONE DATABASE E CODE
# =====================================================================
def get_data():
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT * FROM daily_matches", conn)
        conn.close()
        return df
    except sqlite3.OperationalError:
        return pd.DataFrame()

df = get_data()

if df.empty:
    st.info("Nessun dato presente nel database. Clicca su 'Scarica Partite di Domani' per iniziare.")
else:
    st.subheader("📅 Palinsesto e Selezione")
    
    # Filtriamo i match in attesa di decisione
    pending_matches = df[df['status'] == 'PENDING']
    
    if not pending_matches.empty:
        for index, row in pending_matches.iterrows():
            col_match, col_btn = st.columns([4, 1])
            with col_match:
                st.write(f"**{row['tournament']}** ({row['surface']}): {row['player1']} vs {row['player2']}")
            with col_btn:
                if st.button("➕ Metti in Coda AI", key=f"queue_{row['id']}"):
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute("UPDATE daily_matches SET status = 'QUEUED' WHERE id = ?", (row['id'],))
                    conn.commit()
                    conn.close()
                    st.rerun()
    else:
        st.success("Nessun match in PENDING. Seleziona nuovi match o avvia l'analisi!")

    # =====================================================================
    # 📑 REFERTI COMPLETATI
    # =====================================================================
    completed_matches = df[df['status'] == 'COMPLETED']
    if not completed_matches.empty:
        st.markdown("---")
        st.subheader("📑 Dossier AI Completati")
        for index, row in completed_matches.iterrows():
            with st.expander(f"✅ {row['player1']} vs {row['player2']} ({row['tournament']})"):
                st.markdown(row['dossier'])