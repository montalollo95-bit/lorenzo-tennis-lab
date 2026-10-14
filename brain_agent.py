import sqlite3
import time
import re
import streamlit as st
from google import genai
from google.genai import types

# =====================================================================
# 🔑 CONFIGURAZIONE API KEY GEMINI (Cloud Secure Mode)
# =====================================================================
API_KEY = st.secrets["GEMINI_API_KEY"]

DB_PATH = "tennis_lab.db"

def analizza_match_con_gemini(client, p1, p2, surface, p1_stats, p2_stats):
    """Invia il prompt a Gemini attivando la navigazione Web in tempo reale con sistema anti-crash."""
    
    prompt = f"""
    Sei un analista quantitativo di tennis per mercati finanziari.
    Analizza l'incontro su {surface}: {p1} vs {p2}.

    🛑 AZIONE OBBLIGATORIA PRIMA DI RISPONDERE:
    Usa lo strumento di ricerca web per cercare le notizie degli ultimi 7 giorni su "{p1} tennis news injury fatigue" e "{p2} tennis news injury fatigue". Controlla i tornei che hanno giocato la settimana scorsa per valutare il minutaggio, i viaggi intercontinentali (jet lag), problemi fisici o dichiarazioni di stanchezza.

    DATI STATISTICI (Tennis Abstract):
    Giocatore 1 ({p1}): {p1_stats}
    Giocatore 2 ({p2}): {p2_stats}

    Integra la matematica pura con il contesto umano e genera il referto.
    
    REGOLE OBBLIGATORIE DI FORMATTAZIONE OUTPUT:
    Restituisci ESATTAMENTE questo formato strutturato, senza testo prima o dopo i tag.

    [PROB_P1] <inserisci solo il numero intero della percentuale stimata per {p1}, es. 65>
    [PROB_P2] <inserisci solo il numero intero della percentuale stimata per {p2}, es. 35>
    [ODDS_P1] <inserisci la quota decimale fair calcolata per {p1}, es. 1.53>
    [ODDS_P2] <inserisci la quota decimale fair calcolata per {p2}, es. 2.85>
    [DOSSIER]
    ### 🎯 PRONOSTICO SECCO E MERCATO
    <Crea una tabella Markdown. Colonne: **Esito Previsto**, **Set Betting Probabile**, **Linea Over/Under**, **Quota Fair (Modello)**, **Trigger Live**>

    ### 🚑 Fattore Umano: Affaticamento & News (Real-Time Web)
    <Scrivi un resoconto basato ESCLUSIVAMENTE sulle ricerche web appena effettuate. Rispondi a: Chi ha giocato più ore negli ultimi 10 giorni? Qualcuno ha viaggiato di recente cambiando fuso orario? Ci sono medical time-out recenti, fasciature visibili o dichiarazioni di stanchezza?>

    ### 📊 Cruscotto Metriche Avanzato (Tennis Abstract)
    <Crea una tabella Markdown. Colonne: Metrica, {p1}, {p2}, Delta/Vantaggio. 
    Righe: Superficie Win %, Hold % (Servizio), Break % (Risposta), Dominance Ratio, Break Point Salvati %, Break Point Convertiti %.>

    ### 🧠 Dossier Strategico Quantitativo
    <Analisi tattica del match-up: incrocia i dati matematici della tabella con le notizie sull'affaticamento appena trovate per determinare il Vantaggio Reale.>
    """

    # 🛡️ SISTEMA ANTI-CRASH E ANTI-DISCONNESSIONE
    tentativi = 3
    for tentativo in range(tentativi):
        try:
            response = client.models.generate_content(
                model='gemini-3.8-flash', # ⬅️ MODELLO AGGIORNATO
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[{"google_search": {}}] 
                )
            )
            return response.text
        except Exception as e:
            # ⬅️ MODIFICA CHIAVE 1: Costringiamo l'app a stampare la diagnosi reale del server
            print(f"   ⚠️ Fallimento API (Tentativo {tentativo+1}/{tentativi}). VERO ERRORE DI GOOGLE: {e}")
            time.sleep(5) 
            if tentativo == tentativi - 1:
                print("   ❌ Errore persistente di rete. Interrompo l'analisi per questo match e passo al prossimo.")
                return None

def process_brain():
    print("🧠 Inizializzazione Cervello Quantitativo (Gemini AI con Accesso Web)...")
    
    client = genai.Client(api_key=API_KEY)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id, player1, player2, surface, p1_stats, p2_stats FROM daily_matches WHERE status = 'QUEUED'")
        matches = cursor.fetchall()
    except sqlite3.OperationalError:
        print("❌ Database non trovato. Esegui prima data_ingestion.py")
        return
    
    if not matches:
        print("📭 Nessun match in attesa di analisi (QUEUED).")
        conn.close()
        return
        
    print(f"📊 Trovati {len(matches)} match mirati. Avvio Ricerca Web e Analisi AI...\n")
    
    for row in matches:
        match_id, p1, p2, surface, p1_stats, p2_stats = row
        print(f"⚙️ Ricerca notizie ed elaborazione logica: {p1} vs {p2}...")
        
        if not p1_stats: p1_stats = "Dati TA assenti."
        if not p2_stats: p2_stats = "Dati TA assenti."
        
        risultato = analizza_match_con_gemini(client, p1, p2, surface, p1_stats, p2_stats)
        
        if risultato:
            prob_p1 = re.search(r'\[PROB_P1\]\s*([\d.]+)', risultato)
            prob_p2 = re.search(r'\[PROB_P2\]\s*([\d.]+)', risultato)
            odds_p1 = re.search(r'\[ODDS_P1\]\s*([\d.]+)', risultato)
            odds_p2 = re.search(r'\[ODDS_P2\]\s*([\d.]+)', risultato)
            dossier_match = re.search(r'\[DOSSIER\]\s*(.*)', risultato, re.DOTALL)
            
            pure_prob_p1 = float(prob_p1.group(1)) if prob_p1 else 50.0
            pure_prob_p2 = float(prob_p2.group(1)) if prob_p2 else 50.0
            market_odds_p1 = float(odds_p1.group(1)) if odds_p1 else 2.00
            market_odds_p2 = float(odds_p2.group(1)) if odds_p2 else 2.00
            
            dossier_text = dossier_match.group(1).strip() if dossier_match else risultato
            
            cursor.execute('''
                UPDATE daily_matches 
                SET pure_prob_p1 = ?, pure_prob_p2 = ?, 
                    market_odds_p1 = ?, market_odds_p2 = ?, 
                    dossier = ?, status = 'COMPLETED'
                WHERE id = ?
            ''', (pure_prob_p1, pure_prob_p2, market_odds_p1, market_odds_p2, dossier_text, match_id))
            
            conn.commit()
            print("   ✅ Indagine Web e Dossier archiviati.")
        else:
            print("   ❌ Fallimento definitivo nell'analisi AI. Match archiviato con errore.")
            cursor.execute("UPDATE daily_matches SET status = 'ERROR' WHERE id = ?", (match_id,))
            conn.commit()
            
        # ⬅️ MODIFICA CHIAVE 2: Aumentato il tempo fisiologico di respiro tra i match per evitare blocchi
        time.sleep(8)

    conn.close()
    print("\n🏁 Processo completato! Aggiorna la Dashboard.")

if __name__ == "__main__":
    process_brain()