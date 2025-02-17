import json
import shutil
import os

# Carica i file JSON
def load_json(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

# Salva i dati nel file JSON
def save_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# Funzione principale per aggiornare i file
def update_catalogo():
    try:
        # Carica i due file JSON
        catalogo_file = 'catalogoWindows.json'
        old_catalogo_file = 'old_catalogoWindows.json'

        # Verifica se entrambi i file esistono
        if not os.path.exists(catalogo_file) or not os.path.exists(old_catalogo_file):
            print(f"Errore: Uno o entrambi i file {catalogo_file} o {old_catalogo_file} non esistono.")
            return

        catalogo_data = load_json(catalogo_file)
        old_catalogo_data = load_json(old_catalogo_file)

        # Confronta i due file (se i dati sono diversi)
        if catalogo_data != old_catalogo_data:
            print("I file sono diversi. Aggiornamento di old_catalogoWindows.json...")

            # Aggiorna old_catalogoWindows.json con i nuovi dati
            save_json(catalogo_data, old_catalogo_file)
            print(f"{old_catalogo_file} è stato aggiornato con successo.")
        else:
            print("I file sono identici. Nessun aggiornamento necessario.")
    except Exception as e:
        print(f"Errore durante l'aggiornamento: {e}")

if __name__ == "__main__":
    update_catalogo()
