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
coll1, coll2 = st.columns([4, 1])

with coll1:
    if st.button("📥 1. Scarica Partite di Domani", use_container_width=True):
        with st.spinner("Estrazione dati in corso (richiede qualche secondo)..."):
            try:
                import data_ingestion
                # Chiama direttamente la funzione interna senza subprocessi
                data_ingestion.main() 
                st.success("Palinsesto di domani scaricato e aggiornato!")
                st.rerun()
            except Exception as e:
                st.error(f"Errore durante l'estrazione: {e}")

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
        cursor = conn.cursor()
        
        # 🛡️ CREAZIONE AUTOMATICA TABELLA SE ASSENTE
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tournament TEXT,
                player1 TEXT,
                player2 TEXT,
                surface TEXT,
                p1_stats TEXT,
                p2_stats TEXT,
                pure_prob_p1 REAL,
                pure_prob_p2 REAL,
                market_odds_p1 REAL,
                market_odds_p2 REAL,
                dossier TEXT,
                status TEXT DEFAULT 'PENDING'
            )
        ''')
        conn.commit()
        
        df = pd.read_sql_query("SELECT * FROM daily_matches", conn)
        conn.close()
        return df
    except Exception as e:
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
