import sqlite3
import requests
from datetime import datetime, timedelta

DB_PATH = "tennis_lab.db"
API_KEY = st.secrets["RAPIDAPI_KEY"]
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
        response = requests.get(url, headers=headers, params=querystring, timeout=15)
        response.raise_for_status()
        dati_json = response.json()
        
        # FIX: Controlliamo se ci restituisce direttamente una lista invece di un dizionario
        if isinstance(dati_json, list):
            tornei = dati_json
        else:
            tornei = dati_json.get('data', []) or dati_json.get('tournaments', [])
            
        if not tornei:
            print(f"   ⚠️ Il server API ha risposto, ma il palinsesto di {etichetta_giorno} è vuoto.")
            return matches

        for torneo in tornei:
            # Ricerca flessibile del nome del torneo (minuscolo o maiuscolo)
            nome_torneo = torneo.get('NAME') or torneo.get('name') or torneo.get('tournament_name') or torneo.get('TOURNAMENT_NAME') or "Torneo Sconosciuto"
            
            circuiti_maggiori = ["ATP", "WTA"]
            
            if any(circuito in nome_torneo.upper() for circuito in circuiti_maggiori):
                
                superficie = "Hard"
                if "terra" in nome_torneo.lower() or "clay" in nome_torneo.lower(): superficie = "Clay"
                elif "erba" in nome_torneo.lower() or "grass" in nome_torneo.lower(): superficie = "Grass"
                
                # Cerca gli eventi dentro il torneo
                eventi = torneo.get('EVENTS') or torneo.get('events') or torneo.get('matches') or []
                
                for evento in eventi:
                    # Estrae i nomi dei giocatori intercettando i vari formati
                    home = evento.get('HOME_NAME') or evento.get('home_participant_name') or evento.get('home_team', {}).get('name') or ''
                    away = evento.get('AWAY_NAME') or evento.get('away_participant_name') or evento.get('away_team', {}).get('name') or ''
                    
                    if home and away:
                        if "/" not in home and "/" not in away and "-" not in home:
                            p1 = home.split("(")[0].strip()
                            p2 = away.split("(")[0].strip()
                            
                            torneo_etichettato = f"[{etichetta_giorno}] {nome_torneo}"
                            matches.append((torneo_etichettato, p1, p2, superficie))
                            
    except Exception as e:
        print(f"⚠️ Errore durante la chiamata API per {etichetta_giorno}: {e}")
        
    return matches

def salva_nel_database(matches):
    if not matches:
        print("📭 Nessun match VIP trovato per Oggi o Domani tramite API.")
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
    print(f"✅ Inseriti {len(matches_unici)} match VIP pronti per la Dashboard.")

if __name__ == "__main__":
    print("🎾 Inizializzazione: Connessione Diretta Flashscore API (No Browser)")
    inizializza_database()
    
    oggi_str = datetime.now().strftime('%Y-%m-%d')
    domani_str = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    print(f"   📡 Estrazione palinsesto di OGGI ({oggi_str})...")
    matches_oggi = estrai_da_api(oggi_str, "OGGI")
    
    print(f"   📡 Estrazione palinsesto di DOMANI ({domani_str})...")
    matches_domani = estrai_da_api(domani_str, "DOMANI")
    
    salva_nel_database(matches_oggi + matches_domani)