# 🐳 Docker Container Troubleshooting

## Problem
Container `8c6c3038dcf9` startet nicht.

## Diagnose-Schritte

### 1. Docker-Prozess prüfen
```bash
docker ps -a
```

### 2. Container-Logs ansehen
```bash
docker logs 8c6c3038dcf9afca502db48cef44f97271deec43fca8fa6117a01b305dd61773
```

### 3. Container Status
```bash
docker inspect 8c6c3038dcf9 | grep -A 10 State
```

## Lösungsvorschläge

### Option 1: Docker Compose neu starten
```bash
# Alle Container stoppen
docker compose down

# Neu starten
docker compose up -d archon-server

# Logs verfolgen
docker compose logs -f archon-server
```

### Option 2: Einzelnen Container neu erstellen
```bash
# Container löschen
docker rm -f 8c6c3038dcf9

# Neu bauen und starten
docker compose up -d --build archon-server
```

### Option 3: Kompletter Neuaufbau
```bash
# Alles löschen (Vorsicht: auch Volumes!)
docker compose down -v

# Neu bauen
docker compose build archon-server

# Starten
docker compose up -d archon-server
```

### Option 4: Lokaler Start (ohne Docker)
```bash
cd python

# Virtual Environment aktivieren
source .venv/bin/activate

# Server starten
python -m uvicorn src.server.main:app --host 0.0.0.0 --port 8181 --reload
```

## Häufige Fehlerursachen

1. **Port bereits belegt**
   - Prüfen: `lsof -i:8181`
   - Lösung: Prozess beenden oder Port ändern

2. **Fehlende Environment Variables**
   - Prüfen: `.env` Datei vorhanden?
   - Lösung: `.env.example` zu `.env` kopieren

3. **Python-Imports fehlschlagen**
   - Prüfen: Dependencies installiert?
   - Lösung: `pip install -r requirements.txt` im Container

4. **Docker Daemon hängt**
   - Symptom: `docker ps` hängt
   - Lösung: Docker Desktop neu starten

## Nächster Schritt

**Empfehlung:** Versuche zuerst Option 1 (docker compose down/up)
