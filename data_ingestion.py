import sqlite3
import requests
from datetime import datetime, timedelta
import streamlit as st  # ⬅️ ESSENZIALE: Importa Streamlit per leggere le chiavi segrete

DB_PATH = "tennis_lab.db"

# Lettura sicura della chiave segreta dalla cassaforte di Streamlit Cloud
try:
    API_KEY = st.secrets["RAPIDAPI_KEY"]
except Exception:
    API_KEY = ""  # Fallback locale se eseguito fuori da Streamlit

API_HOST = "flashscore-api1.p.rapidapi.com"

def inizializza_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
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
    cursor.execute("DELETE FROM daily_matches")
    conn.commit()
    conn.close()

def estrai_da_api(date_str, etichetta_giorno):
    matches = []
    url = f"https://{API_HOST}/api/flashscore/v2/matches/list-by-date"
    
    querystring = {
        "language": "it",
        "timezone": "Europe/Rome",
        "sport_id": "2",  # 2 = Tennis
        "date": date_str
    }
    
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": API_HOST
    }

    try:
        response = requests.get(url, headers=headers, params=querystring, timeout=12)
        if response.status_code != 200:
            return matches
            
        dati_json = response.json()
        
        if isinstance(dati_json, list):
            tornei = dati_json
        else:
            tornei = dati_json.get('data', []) or dati_json.get('tournaments', [])
            
        if not tornei:
            return matches

        for torneo in tornei:
            nome_torneo = torneo.get('NAME') or torneo.get('name') or torneo.get('tournament_name') or torneo.get('TOURNAMENT_NAME') or "Torneo Sconosciuto"
            circuiti_maggiori = ["ATP", "WTA"]
            
            if any(circuito in nome_torneo.upper() for circuito in circuiti_maggiori):
                superficie = "Hard"
                if "terra" in nome_torneo.lower() or "clay" in nome_torneo.lower(): superficie = "Clay"
                elif "erba" in nome_torneo.lower() or "grass" in nome_torneo.lower(): superficie = "Grass"
                
                eventi = torneo.get('EVENTS') or torneo.get('events') or torneo.get('matches') or []
                
                for evento in eventi:
                    home = evento.get('HOME_NAME') or evento.get('home_participant_name') or evento.get('home_team', {}).get('name') or ''
                    away = evento.get('AWAY_NAME') or evento.get('away_participant_name') or evento.get('away_team', {}).get('name') or ''
                    
                    if home and away:
                        if "/" not in home and "/" not in away and "-" not in home:
                            p1 = home.split("(")[0].strip()
                            p2 = away.split("(")[0].strip()
                            torneo_etichettato = f"[{etichetta_giorno}] {nome_torneo}"
                            matches.append((torneo_etichettato, p1, p2, superficie))
                            
    except Exception as e:
        print(f"Errore API per {etichetta_giorno}: {e}")
        
    return matches

def salva_nel_database(matches):
    if not matches:
        return
        
    matches_unici = list(dict.fromkeys(matches))
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for torneo, p1, p2, surface in matches_unici:
        cursor.execute('''
            INSERT INTO daily_matches (tournament, player1, player2, surface, status) 
            VALUES (?, ?, ?, ?, 'PENDING')
        ''', (torneo, p1, p2, surface))
    conn.commit()
    conn.close()

def main():
    inizializza_database()
    oggi_str = datetime.now().strftime('%Y-%m-%d')
    domani_str = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    matches_oggi = estrai_da_api(oggi_str, "OGGI")
    matches_domani = estrai_da_api(domani_str, "DOMANI")
    
    salva_nel_database(matches_oggi + matches_domani)

if __name__ == "__main__":
    main()
