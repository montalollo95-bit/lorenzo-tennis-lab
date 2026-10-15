import sqlite3
import pandas as pd
import streamlit as st

# Configurazione della pagina
st.set_page_config(page_title="Laboratorio Pronostici Tennis AI", layout="wide")

DB_PATH = "tennis_lab.db"

def get_data():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Creazione automatica della tabella se non esiste
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
                status TEXT DEFAULT 'PENDING',
                dossier TEXT,
                winner TEXT,
                profit_loss REAL
            )
        ''')
        conn.commit()
        
        df = pd.read_sql_query("SELECT * FROM daily_matches", conn)
        conn.close()
        return df
    except Exception as e:
        return pd.DataFrame()

st.title("🎾 Laboratorio Pronostici Tennis AI")
st.subheader("Pannello di Controllo")

# Due colonne perfettamente bilanciate per i pulsanti principali
col1, col2 = st.columns(2)

with col1:
    if st.button("📥 1. Scarica Partite di Domani", use_container_width=True):
        with st.spinner("Estrazione dati da Flashscore in corso..."):
            try:
                import data_ingestion
                data_ingestion.main()
                st.success("Palinsesto scaricato e aggiornato con successo!")
                st.rerun()
            except Exception as e:
                st.error(f"Errore durante l'estrazione: {e}")

with col2:
    if st.button("🧠 2. Avvia Analisi AI (In Coda)", use_container_width=True):
        with st.spinner("L'Intelligenza Artificiale sta analizzando i match in coda..."):
            try:
                import brain_agent
                brain_agent.process_brain()
                st.success("Analisi AI completata con successo!")
                st.rerun()
            except Exception as e:
                st.error(f"Errore durante l'analisi AI: {e}")
st.markdown("---")

# Visualizzazione dati e palinsesto
df = get_data()

if df.empty:
    st.info("Nessun dato presente nel database. Clicca su 'Scarica Partite di Domani' per iniziare.")
else:
    st.subheader("📋 Palinsesto e Selezione")
    
    pending_matches = df[df['status'] == 'PENDING']
    
    if not pending_matches.empty:
        for index, row in pending_matches.iterrows():
            col_match, col_btn = st.columns([4, 1])
            with col_match:
                st.write(f"**{row['tournament']}** ({row['surface']}): {row['player1']} vs {row['player2']}")
            with col_btn:
                if st.button("➕ Metti in Coda", key=f"queue_{row['id']}"):
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute("UPDATE daily_matches SET status = 'QUEUED' WHERE id = ?", (row['id'],))
                    conn.commit()
                    conn.close()
                    st.rerun()
    else:
        st.write("Nessun match in attesa nel palinsesto.")

st.markdown("---")
st.subheader("🏆 Archivio Pronostici e Dossier AI (COMPLETATI)")

completed_matches = df[df['status'] == 'COMPLETED']

if not completed_matches.empty:
    for index, row in completed_matches.iterrows():
        with st.expander(f"📊 {row['tournament']} | {row['player1']} vs {row['player2']} (Superficie: {row['surface']})"):
            col_info1, col_info2 = st.columns(2)
            with col_info1:
                st.markdown(f"**Probabilità Modello:**")
                st.write(f"- {row['player1']}: **{row['pure_prob_p1']}%** (Quota Fair: `{row['market_odds_p1']}`)")
                st.write(f"- {row['player2']}: **{row['pure_prob_p2']}%** (Quota Fair: `{row['market_odds_p2']}`)")
            with col_info2:
                st.markdown(f"**Stato Match:** `{row['status']}`")
            
            st.markdown("---")
            st.markdown("**Dossier Strategico e Analisi AI:**")
            st.markdown(row['dossier'] if row['dossier'] else "Nessun dettaglio disponibile.")
else:
    st.info("Nessun match analizzato ancora. Metti in coda le partite e avvia l'Analisi AI per popolare questa sezione.")
