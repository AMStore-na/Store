import requests
import json
import os
from github import Github

# Recupera i valori dai segreti
github_token = os.getenv('GITHUB_TOKEN')

# URL dei file su GitHub
mods_url = 'https://raw.githubusercontent.com/AMStore-na/Store/refs/heads/main/catalogoWindows.json'
state_url = 'https://raw.githubusercontent.com/AMStore-na/Store/refs/heads/main/OldState/old_catalogoWindows.json'
repo_api_url = 'https://api.github.com/repos/AMStore-na/Store/contents/OldState/old_catalogoWindows.json'

# Recupera il file JSON catalogoWindows.json
catalogo_response = requests.get(mods_url)
catalogo_data = catalogo_response.json()

# Recupera il file JSON old_catalogoWindows.json
state_response = requests.get(state_url)
state_data = state_response.json()

# Normalizza i dati per evitare problemi di confronto
for item in catalogo_data:
    # Aggiunge campi mancanti
    item.setdefault('Hash', None)  # Se il campo 'Hash' non esiste, lo imposta su None
    item.setdefault('HashX32', None)  # Se il campo 'HashX32' non esiste, lo imposta su None

for item in state_data:
    # Aggiunge campi mancanti
    item.setdefault('Hash', None)  # Se il campo 'Hash' non esiste, lo imposta su None
    item.setdefault('HashX32', None)  # Se il campo 'HashX32' non esiste, lo imposta su None

# Confronta i dati
if catalogo_data != state_data:
    print("I dati sono cambiati, aggiornamento in corso...")

    # Usa PyGithub per autenticarsi e ottenere il repo
    g = Github(github_token)
    repo = g.get_repo("AMStore-na/Store")
    
    # Ottieni il contenuto del file old_catalogoWindows.json
    file_content = repo.get_contents("OldState/old_catalogoWindows.json")
    
    # Aggiorna il contenuto del file old_catalogoWindows.json
    update_response = repo.update_file(
        file_content.path,
        "Aggiornamento catalogo con Hash e HashX32",
        json.dumps(catalogo_data, indent=4, ensure_ascii=False),  # Mantiene i caratteri speciali correttamente
        file_content.sha
    )
    
    print(f"File aggiornato con successo: {update_response}")
else:
    print("Nessuna modifica rilevata.")

