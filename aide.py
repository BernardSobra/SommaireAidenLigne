"""Met à jour AideEnLigne.json depuis le dossier Thunderbird « PC SOFT - Quoi de neuf dans l'aide en ligne ».

- Mode incrémental (par défaut) : seuls les messages « Non lu » sont lus.
- Mode complet : tout le dossier est relu. Automatique au premier lancement de chaque mois,
  ou avec l'option --complet.
- Une rubrique est identifiée par son adresse (numéro d'aide). Si elle existe déjà, elle est mise à jour.
- Si le JSON a changé, un git commit est fait (jamais de push).
- Les messages pris en compte sont ensuite marqués comme lus, uniquement si Thunderbird est fermé
  (une copie de la boîte est faite avant, dans sauvegarde\\).
"""
import os, re, json, html, shutil, subprocess, sys
from datetime import date

DEPOT = os.path.dirname(os.path.abspath(__file__))
JSON = os.path.join(DEPOT, "AideEnLigne.json")
ETAT = os.path.join(DEPOT, "etat.json")
SAUVEGARDE = os.path.join(DEPOT, "sauvegarde")
BOITE = os.path.expandvars(
    r"%APPDATA%\Thunderbird\Profiles\exy3pdyr.default-esr\Mail\Feeds\PC SOFT - Quoi de neuf dans l'aide en ligne"
)

LU = 0x0001
SUPPRIME = 0x0008


def lire_messages(chemin):
    """Renvoie [(statut, position du statut dans le fichier, texte)] pour chaque message de la boîte mbox."""
    with open(chemin, "rb") as f:
        brut = f.read()
    texte = brut.decode("latin-1")  # 1 octet = 1 caractère : les positions restent exactes
    debuts = [(m.start(), m.end()) for m in re.finditer(r"^From - .*$\n", texte, flags=re.M)]
    messages = []
    for i, (_, fin) in enumerate(debuts):
        limite = debuts[i + 1][0] if i + 1 < len(debuts) else len(brut)
        m = re.search(r"^X-Mozilla-Status:[ \t]*([0-9A-Fa-f]{4})", texte[fin:limite], re.M)
        if m:
            messages.append((int(m.group(1), 16), fin + m.start(1), brut[fin:limite].decode("utf-8", errors="replace")))
    return messages


def vers_enregistrement(bloc):
    sujet = re.search(r"^Subject:\s*(.*)$", bloc, re.M)
    base = re.search(r"^Content-Base:\s*(\S+)", bloc, re.M)
    corps = re.search(r"<body[^>]*>(.*?)</body>", bloc, re.S)
    if not (sujet and base):
        return None
    adresse = re.sub(r"&name=.*$", "", html.unescape(base.group(1)))
    commentaire = ""
    if corps:
        commentaire = html.unescape(re.sub(r"<[^>]+>", "", corps.group(1)))
        commentaire = re.sub(r"\s+", " ", commentaire).strip()
    return {
        "Titre": html.unescape(sujet.group(1).strip()),
        "Adresse": adresse,
        "Commentaire": commentaire,
    }


def lire_json():
    if not os.path.exists(JSON):
        return []
    with open(JSON, encoding="utf-8") as f:
        return json.load(f)


def lire_etat():
    try:
        with open(ETAT, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def git(*args):
    return subprocess.run(["git", "-C", DEPOT, *args], capture_output=True, text=True, encoding="utf-8")


def thunderbird_ouvert():
    r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq thunderbird.exe", "/NH"], capture_output=True, text=True)
    return "thunderbird.exe" in r.stdout.lower()


def marquer_lus(positions):
    """Passe le bit « lu » du X-Mozilla-Status aux positions données (même longueur : le fichier ne bouge pas)."""
    os.makedirs(SAUVEGARDE, exist_ok=True)
    shutil.copy2(BOITE, os.path.join(SAUVEGARDE, "boite_avant_marquage"))
    taille = os.path.getsize(BOITE)
    with open(BOITE, "r+b") as f:
        for pos in positions:
            f.seek(pos)
            statut = int(f.read(4), 16)
            f.seek(pos)
            f.write(b"%04X" % (statut | LU))
    assert os.path.getsize(BOITE) == taille


def main():
    aujourd = date.today()
    mois = aujourd.strftime("%Y-%m")
    etat = lire_etat()
    existant = lire_json()
    complet = ("--complet" in sys.argv) or (etat.get("DernierComplet") != mois) or not existant

    messages = [m for m in lire_messages(BOITE) if not m[0] & SUPPRIME]
    if not complet:
        messages = [m for m in messages if not m[0] & LU]

    # Par adresse ; un message plus récent remplace l'ancien. Complet : on repart de zéro.
    connues = {r["Adresse"]: r for r in existant}
    rubriques = {} if complet else dict(connues)
    nouvelles = modifiees = 0
    a_marquer = []
    for statut, pos, bloc in messages:
        r = vers_enregistrement(bloc)
        if not r:
            continue
        ancien_r = connues.get(r["Adresse"])
        if ancien_r is None:
            nouvelles += 1
        elif ancien_r != r:
            modifiees += 1
        rubriques[r["Adresse"]] = r
        if not statut & LU:
            a_marquer.append(pos)
    resultat = list(rubriques.values())

    nouveau = json.dumps(resultat, ensure_ascii=False, indent=2)
    ancien = ""
    if os.path.exists(JSON):
        with open(JSON, encoding="utf-8") as f:
            ancien = f.read()
    mode = "complet" if complet else "incrémental"
    print(f"Mode {mode} : {len(messages)} messages lus, {len(resultat)} rubriques "
          f"({nouvelles} nouvelles, {modifiees} modifiées par rapport au JSON).")

    if nouveau == ancien:
        print("JSON inchangé, pas de commit.")
    else:
        with open(JSON, "w", encoding="utf-8") as f:
            f.write(nouveau)
        if not os.path.isdir(os.path.join(DEPOT, ".git")):
            print("Pas de dépôt git ici (git init à faire) : pas de commit.")
        else:
            git("add", "AideEnLigne.json")
            msg = f"Mise à jour AideEnLigne.json ({mode}) : {len(resultat)} rubriques, +{nouvelles} nouvelles, {modifiees} modifiées"
            r = git("commit", "-m", msg)
            print("Commit fait." if r.returncode == 0 else "Échec du commit : " + (r.stdout + r.stderr).strip())

    if a_marquer:
        if thunderbird_ouvert():
            print(f"Thunderbird est ouvert : {len(a_marquer)} messages NON marqués comme lus "
                  "(ferme Thunderbird et relance le script).")
        else:
            marquer_lus(a_marquer)
            print(f"{len(a_marquer)} messages marqués comme lus.")

    if complet:
        etat["DernierComplet"] = mois
    etat["DernierLancement"] = aujourd.isoformat()
    with open(ETAT, "w", encoding="utf-8") as f:
        json.dump(etat, f, indent=2)


main()
