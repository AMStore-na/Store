#!/usr/bin/env python3
"""Controlla che il catalogo macOS sia valido prima che arrivi agli utenti.

Uso:  python3 ScriptPython/ValidaCatalogoMacos.py [percorso del catalogo]
      (senza argomenti controlla catalogoMacos_1.json)

Le regole sono le stesse che applica l'app (Catalog.swift e OSVersion.swift):
se questo script dice "OK", l'app riesce a leggere il file.
Esce con codice 1 se trova errori, cosi' la GitHub Action diventa rossa.
Usa solo la libreria standard di Python: nessuna dipendenza da installare.
"""

import json
import os
import re
import sys

PERCORSO_PREDEFINITO = "catalogoMacos_1.json"
SCHEMA_SUPPORTATO = 1
ARCHITETTURE = {"arm64", "x86_64"}

CHIAVI_CATALOGO = {"schemaVersion", "apps"}
CHIAVI_APP = {"id", "name", "summary", "homepage", "icon", "variants"}
CHIAVI_VARIANTE = {"version", "icon", "architectures", "minimumOS",
                   "firstUnsupportedOS", "downloadURL", "sha256"}

errori = []
avvisi = []


def errore(dove, messaggio):
    errori.append(f"{dove}: {messaggio}" if dove else messaggio)


def avviso(dove, messaggio):
    avvisi.append(f"{dove}: {messaggio}")


# MARK: - Controlli sui singoli valori

def versione(testo):
    """Come OSVersion(_:) in Swift: da 1 a 3 numeri separati da punti."""
    parti = testo.split(".")
    if not 1 <= len(parti) <= 3:
        return None
    if not all(p.isdigit() and p.isascii() for p in parti):
        return None
    numeri = [int(p) for p in parti]
    return tuple(numeri + [0] * (3 - len(numeri)))


def testo_obbligatorio(oggetto, chiave, dove):
    if chiave not in oggetto or oggetto[chiave] is None:
        errore(dove, f'manca il campo obbligatorio "{chiave}"')
        return None
    valore = oggetto[chiave]
    if not isinstance(valore, str):
        errore(f"{dove}.{chiave}", "deve essere un testo tra virgolette")
        return None
    if not valore.strip():
        errore(f"{dove}.{chiave}", "e' vuoto")
        return None
    return valore


def testo_facoltativo(oggetto, chiave, dove):
    valore = oggetto.get(chiave)
    if valore is None:
        return None
    if not isinstance(valore, str):
        errore(f"{dove}.{chiave}", "deve essere un testo tra virgolette oppure null")
        return None
    return valore


def controlla_link(link, dove, obbligatorio_https):
    if link is None:
        return
    if re.search(r"\s", link):
        errore(dove, f'il link contiene spazi (usa %20): "{link}"')
    elif link.startswith("https://"):
        if len(link) <= len("https://"):
            errore(dove, "il link e' incompleto")
    elif link.startswith("http://"):
        messaggio = ('il link e\' "http": macOS blocca i download non sicuri, '
                     'serve "https"')
        if obbligatorio_https:
            errore(dove, messaggio)
        else:
            avviso(dove, messaggio)
    else:
        errore(dove, f'non sembra un link (deve iniziare con https://): "{link}"')


def chiavi_sconosciute(oggetto, ammesse, dove):
    for chiave in oggetto:
        if chiave not in ammesse:
            simili = [a for a in ammesse if a.lower() == chiave.lower()]
            suggerimento = f' (forse volevi "{simili[0]}"?)' if simili else ""
            avviso(dove, f'campo "{chiave}" sconosciuto: l\'app lo ignora{suggerimento}')


# MARK: - Controlli sulla struttura

def controlla_variante(variante, dove):
    if not isinstance(variante, dict):
        errore(dove, "ogni variante deve essere un oggetto { ... }")
        return
    chiavi_sconosciute(variante, CHIAVI_VARIANTE, dove)

    testo_obbligatorio(variante, "version", dove)

    archs = variante.get("architectures")
    if archs is None:
        errore(dove, 'manca il campo obbligatorio "architectures"')
    elif not isinstance(archs, list) or not archs:
        errore(f"{dove}.architectures", 'deve essere una lista non vuota, es. ["arm64", "x86_64"]')
    else:
        for i, a in enumerate(archs):
            if a not in ARCHITETTURE:
                errore(f"{dove}.architectures[{i}]",
                       f'"{a}" non e\' valido: si accettano solo "arm64" e "x86_64"')
        if len(set(map(str, archs))) != len(archs):
            avviso(f"{dove}.architectures", "contiene un'architettura ripetuta")

    minimo = None
    testo = testo_obbligatorio(variante, "minimumOS", dove)
    if testo is not None:
        minimo = versione(testo)
        if minimo is None:
            errore(f"{dove}.minimumOS", f'"{testo}" non e\' una versione valida (es. "10.13")')

    testo = testo_facoltativo(variante, "firstUnsupportedOS", dove)
    if testo is not None:
        limite = versione(testo)
        if limite is None:
            errore(f"{dove}.firstUnsupportedOS", f'"{testo}" non e\' una versione valida (es. "11.0")')
        elif minimo is not None and limite <= minimo:
            errore(f"{dove}.firstUnsupportedOS",
                   "deve essere maggiore di minimumOS, altrimenti la variante non va su nessun Mac")

    link = testo_obbligatorio(variante, "downloadURL", dove)
    controlla_link(link, f"{dove}.downloadURL", obbligatorio_https=True)

    controlla_link(testo_facoltativo(variante, "icon", dove), f"{dove}.icon", obbligatorio_https=False)

    sha = testo_facoltativo(variante, "sha256", dove)
    if sha is not None and not re.fullmatch(r"[0-9a-fA-F]{64}", sha):
        errore(f"{dove}.sha256", "deve essere di 64 caratteri esadecimali (0-9, a-f)")


def controlla_app(app, dove, id_visti):
    if not isinstance(app, dict):
        errore(dove, "ogni app deve essere un oggetto { ... }")
        return
    chiavi_sconosciute(app, CHIAVI_APP, dove)

    identificativo = testo_obbligatorio(app, "id", dove)
    if identificativo is not None:
        if identificativo in id_visti:
            errore(f"{dove}.id", f'"{identificativo}" e\' gia\' usato da {id_visti[identificativo]}')
        else:
            id_visti[identificativo] = dove

    nome = testo_obbligatorio(app, "name", dove)
    if nome:
        dove = f'{dove} ("{nome}")'
    testo_facoltativo(app, "summary", dove)
    controlla_link(testo_obbligatorio(app, "homepage", dove), f"{dove}.homepage", obbligatorio_https=False)
    controlla_link(testo_facoltativo(app, "icon", dove), f"{dove}.icon", obbligatorio_https=False)

    varianti = app.get("variants")
    if varianti is None:
        errore(dove, 'manca il campo obbligatorio "variants"')
    elif not isinstance(varianti, list):
        errore(f"{dove}.variants", "deve essere una lista [ ... ]")
    elif not varianti:
        errore(f"{dove}.variants", "e' vuota: l'app non comparirebbe su nessun Mac")
    else:
        for i, variante in enumerate(varianti):
            controlla_variante(variante, f"{dove}.variants[{i}]")


def controlla_catalogo(catalogo):
    if not isinstance(catalogo, dict):
        errore("", 'il file deve iniziare con { "schemaVersion": 1, "apps": [ ... ] }')
        return
    chiavi_sconosciute(catalogo, CHIAVI_CATALOGO, "catalogo")

    schema = catalogo.get("schemaVersion")
    if schema is None:
        errore("catalogo", 'manca "schemaVersion" (deve valere 1)')
    elif type(schema) is not int:
        errore("catalogo.schemaVersion", "deve essere il numero 1, senza virgolette")
    elif schema != SCHEMA_SUPPORTATO:
        errore("catalogo.schemaVersion",
               f"vale {schema}, ma l'app capisce solo la versione {SCHEMA_SUPPORTATO}")

    apps = catalogo.get("apps")
    if apps is None:
        errore("catalogo", 'manca la lista "apps"')
    elif not isinstance(apps, list):
        errore("catalogo.apps", "deve essere una lista [ ... ]")
    else:
        id_visti = {}
        for i, app in enumerate(apps):
            controlla_app(app, f"apps[{i}]", id_visti)


# MARK: - Lettura del file

def senza_chiavi_doppie(coppie):
    """Segnala le chiavi scritte due volte nello stesso oggetto."""
    oggetto = {}
    for chiave, valore in coppie:
        if chiave in oggetto:
            errore("", f'il campo "{chiave}" compare due volte nello stesso blocco')
        oggetto[chiave] = valore
    return oggetto


def leggi(percorso):
    try:
        with open(percorso, "rb") as f:
            grezzo = f.read()
    except OSError as e:
        errore("", f"non riesco ad aprire {percorso}: {e.strerror}")
        return None

    if grezzo.startswith(b"{\\rtf"):
        errore("", "il file e' in formato RTF (salvato da TextEdit come testo formattato), "
                   "non e' JSON. In TextEdit: Formato > Converti in testo normale, poi salva.")
        return None
    if grezzo.startswith(b"\xef\xbb\xbf"):
        avviso("file", "inizia con un BOM UTF-8 invisibile; meglio salvarlo senza")
        grezzo = grezzo[3:]
    try:
        testo = grezzo.decode("utf-8")
    except UnicodeDecodeError:
        errore("", "il file non e' in codifica UTF-8")
        return None
    for virgoletta in "“”‘’":
        if virgoletta in testo:
            riga = testo[:testo.index(virgoletta)].count("\n") + 1
            errore("", f"riga {riga}: virgoletta tipografica {virgoletta} al posto di \" "
                       "(in TextEdit: Modifica > Sostituzioni > togli 'Virgolette intelligenti')")
            return None
    try:
        return json.loads(testo, object_pairs_hook=senza_chiavi_doppie)
    except json.JSONDecodeError as e:
        errore("", f"JSON non valido alla riga {e.lineno}, colonna {e.colno}: {traduci(e.msg)}")
        return None


def traduci(msg):
    traduzioni = {
        "Illegal trailing comma": "virgola di troppo prima di } o ]",
        "Expecting ',' delimiter": "manca una virgola",
        "Expecting property name enclosed in double quotes":
            "atteso un nome tra virgolette (spesso: virgola di troppo prima di } o ])",
        "Expecting value": "manca un valore (spesso: virgola di troppo o file vuoto)",
        "Expecting ':' delimiter": "mancano i due punti dopo il nome del campo",
        "Extra data": "c'e' testo in piu' dopo la fine del catalogo",
        "Unterminated string starting at": "una virgoletta aperta non viene chiusa",
        "Invalid control character at": "c'e' un a capo o un carattere invisibile dentro un testo",
    }
    for inglese, italiano in traduzioni.items():
        if msg.startswith(inglese):
            return italiano
    return msg


def main():
    percorso = sys.argv[1] if len(sys.argv) > 1 else PERCORSO_PREDEFINITO
    in_github = os.environ.get("GITHUB_ACTIONS") == "true"

    catalogo = leggi(percorso)
    if catalogo is not None:
        controlla_catalogo(catalogo)

    for a in avvisi:
        print(f"::warning file={percorso}::{a}" if in_github else f"AVVISO  {a}")
    for e in errori:
        print(f"::error file={percorso}::{e}" if in_github else f"ERRORE  {e}")

    if errori:
        print(f"\n{percorso}: {len(errori)} errore/i. L'app non riuscirebbe a leggere il catalogo.")
        return 1
    n = len(catalogo.get("apps", []))
    print(f"\n{percorso}: OK, {n} app, {len(avvisi)} avviso/i.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
