"""Met à jour AideEnLigne.json depuis le dossier Thunderbird « PC SOFT - Quoi de neuf dans l'aide en ligne ».

- Mode incrémental (par défaut) : seuls les messages « Non lu » sont lus et ajoutés au JSON.
- Mode complet : tout le dossier est relu. Automatique au premier lancement de chaque mois,
  ou avec l'option --complet.
- Si le JSON a changé, un git commit est fait à la fin (jamais de push).

Le dossier de messages est lu en lecture seule : Thunderbird peut rester ouvert.
"""
import os, re, json, html, subprocess, sys
from datetime import date

DEPOT = os.path.dirname(os.path.abspath(__file__))
JSON = os.path.join(DEPOT, "AideEnLigne.json")
ETAT = os.path.join(DEPOT, "etat.json")
BOITE = os.path.expandvars(
    r"%APPDATA%\Thunderbird\Profiles\exy3pdyr.default-esr\Mail\Feeds\PC SOFT - Quoi de neuf dans l'aide en ligne"
)

LU = 0x0001
SUPPRIME = 0x0008


def lire_messages(chemin):
    """Renvoie la liste (statut, texte) de chaque message de la boîte mbox."""
    with open(chemin, "rb") as f:
        texte = f.read().decode("utf-8", errors="replace")
    messages = []
    for bloc in re.split(r"^From - .*$\n", texte, flags=re.M):
        m = re.search(r"^X-Mozilla-Status:\s*([0-9A-Fa-f]+)", bloc, re.M)
        if m:
            messages.append((int(m.group(1), 16), bloc))
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


def cle(r):
    return (r["Titre"], r["Adresse"], r["Commentaire"])


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


def main():
    aujourd = date.today()
    mois = aujourd.strftime("%Y-%m")
    etat = lire_etat()
    existant = lire_json()
    complet = ("--complet" in sys.argv) or (etat.get("DernierComplet") != mois) or not existant

    messages = [(s, b) for s, b in lire_messages(BOITE) if not s & SUPPRIME]
    if not complet:
        messages = [(s, b) for s, b in messages if not s & LU]

    # Complet : on repart de zéro. Incrémental : on complète l'existant.
    resultat = [] if complet else list(existant)
    deja = {cle(r) for r in resultat}
    ajoutes = 0
    for _, bloc in messages:
        r = vers_enregistrement(bloc)
        if r and cle(r) not in deja:
            resultat.append(r)
            deja.add(cle(r))
            ajoutes += 1

    nouveau = json.dumps(resultat, ensure_ascii=False, indent=2)
    ancien = ""
    if os.path.exists(JSON):
        with open(JSON, encoding="utf-8") as f:
            ancien = f.read()
    mode = "complet" if complet else "incrémental"
    print(f"Mode {mode} : {len(messages)} messages lus, {len(resultat)} enregistrements dans le JSON.")

    if nouveau == ancien:
        print("JSON inchangé, pas de commit.")
    else:
        with open(JSON, "w", encoding="utf-8") as f:
            f.write(nouveau)
        print(f"JSON mis à jour ({len(existant)} -> {len(resultat)} enregistrements).")
        if not os.path.isdir(os.path.join(DEPOT, ".git")):
            print("Pas de dépôt git ici (git init à faire) : pas de commit.")
        else:
            git("add", "AideEnLigne.json")
            msg = f"Mise à jour AideEnLigne.json ({mode}) : {len(resultat)} rubriques"
            r = git("commit", "-m", msg)
            print("Commit fait." if r.returncode == 0 else "Échec du commit : " + (r.stdout + r.stderr).strip())

    if complet:
        etat["DernierComplet"] = mois
    etat["DernierLancement"] = aujourd.isoformat()
    with open(ETAT, "w", encoding="utf-8") as f:
        json.dump(etat, f, indent=2)


main()
