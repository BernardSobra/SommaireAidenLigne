"""Met à jour AideEnLigne.json depuis le dossier Thunderbird « PC SOFT - Quoi de neuf dans l'aide en ligne ».

- Mode incrémental (par défaut) : seuls les messages « Non lu » sont lus.
- Mode complet : tout le dossier est relu et ajouté au JSON. Automatique au premier lancement
  de chaque mois, ou avec l'option --complet. Le JSON n'est jamais vidé : une rubrique absente
  de la messagerie reste dans le JSON.
- Une rubrique est identifiée par son ID (numéro d'aide). Si elle existe déjà, seul son commentaire
  est mis à jour si besoin ; sinon elle est ajoutée.
- EstLST est vrai si le commentaire contient « Article LST ».
- La référence categories.md (fonctions du dictionnaire WLangage) est ajoutée au JSON : ID, titre, nom
  anglais, thème (= catégorie sans le préfixe « fonctions_ »), plateformes. Elle n'apporte pas de
  commentaire (renseigné ensuite par la messagerie). Sans catégorie, le thème vient des règles de themes.py.
- Chaque rubrique a un Theme (voir themes.py) et des Plateformes (en-tête Keywords du message).
- Si le JSON a changé, un git commit est fait (jamais de push), sauf avec l'option --sans-commit.
- Les messages pris en compte sont ensuite marqués comme lus, uniquement si Thunderbird est fermé.
- Option --epure (quel que soit le mode) : supprime de la messagerie les anciens messages d'une même
  adresse, en gardant le plus récent. Thunderbird doit être fermé.
- Avant toute modification de la boîte, une copie est faite dans sauvegarde\\.
"""
import os, re, json, html, shutil, subprocess, sys
from functools import lru_cache
from datetime import date

import themes

DEPOT = os.path.dirname(os.path.abspath(__file__))
JSON = os.path.join(DEPOT, "AideEnLigne.json")
ETAT = os.path.join(DEPOT, "etat.json")
SAUVEGARDE = os.path.join(DEPOT, "sauvegarde")
BOITE = os.path.expandvars(
    r"%APPDATA%\Thunderbird\Profiles\exy3pdyr.default-esr\Mail\Feeds\PC SOFT - Quoi de neuf dans l'aide en ligne"
)

REFERENCE = r"C:\DATA\DEVELOPPEMENT\windev-wlangage\windev-wlangage\index\categories.md"
URL_AIDE = "https://doc.pcsoft.fr/fr-FR/?"

LU = 0x0001
SUPPRIME = 0x0008

PLATEFORMES = {"Etats & Requêtes": "États et Requêtes"}  # puis passé en majuscules


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
    mots = re.search(r"^Keywords:[ \t]*(.*)$", bloc, re.M)
    plateformes = [PLATEFORMES.get(p.strip(), p.strip()).upper() for p in mots.group(1).split(";") if p.strip()] if mots else []
    return {
        "ID": numero_aide(adresse),
        "Titre": html.unescape(sujet.group(1).strip()),
        "Adresse": adresse,
        "Commentaire": commentaire,
        "Plateformes": plateformes,
    }


def numero_aide(adresse):
    """Numéro d'aide d'une adresse : https://doc.pcsoft.fr/fr-FR/?1410091156 => 1410091156."""
    m = re.search(r"\?(\d+)", adresse)
    return m.group(1) if m else ""


@lru_cache(maxsize=None)
def page_info(numero):
    """Nom anglais, catégorie et plateformes d'une rubrique, d'après sa page du dictionnaire WLangage."""
    info = {"anglais": "", "categorie": "", "plateformes": []}
    try:
        with open(os.path.join(themes.DICTIONNAIRE, numero + ".md"), encoding="utf-8") as f:
            tete = f.read(1500)
    except OSError:
        return info
    m = re.search(r'^english:\s*"([^"]*)"', tete, re.M)
    info["anglais"] = m.group(1) if m else ""
    m = re.search(r'^category:\s*"([^"]*)"', tete, re.M)
    info["categorie"] = m.group(1) if m else ""
    m = re.search(r'^source_help:\s*(\[.*\])', tete, re.M)
    if m:
        try:
            info["plateformes"] = [PLATEFORMES.get(x, x).upper() for x in json.loads(m.group(1))]
        except ValueError:
            pass
    return info


def lire_reference():
    """Rubriques de categories.md : [(ID, titre, nom anglais, catégorie)]. Liste vide si le fichier est absent."""
    if not os.path.exists(REFERENCE):
        return []
    resultat, categorie = [], ""
    with open(REFERENCE, encoding="utf-8") as f:
        for ligne in f:
            m = re.match(r"## (\S+) \(\d+\)", ligne)
            if m:
                categorie = m.group(1)
                continue
            m = re.match(r"- \[(.+?)\]\(\.\./pages/(\d+)\.md\)(?: — \*(.+)\*)?", ligne)
            if m:
                resultat.append((m.group(2), m.group(1), m.group(3) or "", categorie))
    return resultat


def theme_depuis_categorie(categorie):
    """fonctions_camera_video => camera_video (les autres catégories restent telles quelles)."""
    return categorie[len("fonctions_"):] if categorie.startswith("fonctions_") else categorie


def mise_en_forme(r):
    """Rubrique complète, champs dans l'ordre du JSON. Le Theme est recalculé à chaque passage."""
    numero = r["ID"]
    titre = r["Titre"]
    info = page_info(numero)
    categorie = r.get("Categorie") or info["categorie"]
    commentaire = r.get("Commentaire", "")
    if categorie:
        theme = theme_depuis_categorie(categorie)
    else:
        # rubrique hors dictionnaire : règles sur le titre, nom mis dans le style des catégories
        theme = themes.style_categorie(themes.theme(titre, numero)[0])
    return {
        "ID": int(numero),
        "Theme": theme,
        "Plateformes": [p.upper() for p in r.get("Plateformes", [])],
        "Titre": titre,
        "Anglais": r.get("Anglais") or info["anglais"],
        "Adresse": r["Adresse"],
        "Commentaire": commentaire,
        # Article de la LST (les résumés de la messagerie commencent par « Article LST »)
        "EstLST": "Article LST" in commentaire,
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


_sauvegarde_faite = False


def sauvegarder():
    """Copie la boîte dans sauvegarde\\ (une seule fois par lancement, avant la première modification)."""
    global _sauvegarde_faite
    if not _sauvegarde_faite:
        os.makedirs(SAUVEGARDE, exist_ok=True)
        shutil.copy2(BOITE, os.path.join(SAUVEGARDE, "boite_avant_modification"))
        _sauvegarde_faite = True


def epurer(rubriques):
    """Supprime de la boîte les anciens messages d'une même adresse (garde le dernier).

    Une adresse n'est épurée que si elle est déjà dans le JSON. Renvoie le nombre de messages supprimés.
    L'index .msf est supprimé : Thunderbird le reconstruit au démarrage.
    """
    with open(BOITE, "rb") as f:
        brut = f.read()
    texte = brut.decode("latin-1")
    debuts = [m.start() for m in re.finditer(r"^From - .*$\n", texte, flags=re.M)]
    morceaux = []
    for i, d in enumerate(debuts):
        fin = debuts[i + 1] if i + 1 < len(debuts) else len(brut)
        r = vers_enregistrement(brut[d:fin].decode("utf-8", errors="replace"))
        morceaux.append((d, fin, r["ID"] if r else None))
    dernier = {}
    for i, (_, _, adresse) in enumerate(morceaux):
        if adresse:
            dernier[adresse] = i
    garder = [i for i, (_, _, a) in enumerate(morceaux) if a is None or dernier[a] == i or a not in rubriques]
    supprimes = len(morceaux) - len(garder)
    if not supprimes:
        return 0
    sauvegarder()
    nouveau = brut[:debuts[0]] + b"".join(brut[morceaux[i][0]:morceaux[i][1]] for i in garder)
    temp = BOITE + ".tmp"
    with open(temp, "wb") as f:
        f.write(nouveau)
    os.replace(temp, BOITE)
    if os.path.exists(BOITE + ".msf"):
        os.remove(BOITE + ".msf")
    return supprimes


def marquer_lus(positions):
    """Passe le bit « lu » du X-Mozilla-Status aux positions données (même longueur : le fichier ne bouge pas)."""
    sauvegarder()
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

    # Clé = ID. On part toujours du JSON existant : rien n'en est retiré, même si le message a disparu
    # de la messagerie. Dédoublonnage par ID dès le chargement (le dernier l'emporte).
    rubriques = {}
    for r in existant:
        # accepte aussi l'ancien nom "_ID" ; ID peut être un entier ou une chaîne dans le fichier
        numero = str(r.get("ID") or r.get("_ID") or numero_aide(r["Adresse"]))
        rubriques[numero] = dict(r, ID=numero)

    # 1. Référence : on ajoute ce qui manque ; une rubrique existante n'est pas modifiée.
    de_reference = 0
    for numero, titre, anglais, categorie in lire_reference():
        if numero in rubriques:
            continue
        rubriques[numero] = {"ID": numero, "Titre": titre, "Anglais": anglais, "Adresse": URL_AIDE + numero,
                             "Commentaire": "", "Categorie": categorie,
                             "Plateformes": page_info(numero)["plateformes"]}
        de_reference += 1

    # 2. Messagerie : si l'ID existe, seul le commentaire change (si besoin) ; sinon la rubrique est ajoutée.
    nouvelles = modifiees = 0
    a_marquer = []
    for statut, pos, bloc in messages:
        r = vers_enregistrement(bloc)
        if not r or not r["ID"]:
            continue
        courante = rubriques.get(r["ID"])
        if courante is None:
            rubriques[r["ID"]] = r
            nouvelles += 1
        elif r["Commentaire"] and courante.get("Commentaire") != r["Commentaire"]:
            courante["Commentaire"] = r["Commentaire"]
            modifiees += 1
        if not statut & LU:
            a_marquer.append(pos)
    resultat = [mise_en_forme(r) for r in rubriques.values()]

    nouveau = json.dumps(resultat, ensure_ascii=False, indent=2)
    ancien = ""
    if os.path.exists(JSON):
        with open(JSON, encoding="utf-8") as f:
            ancien = f.read()
    mode = "complet" if complet else "incrémental"
    print(f"Mode {mode} : {len(messages)} messages lus, {len(resultat)} rubriques "
          f"({de_reference} de la référence, {nouvelles} nouvelles de la messagerie, "
          f"{modifiees} commentaires modifiés).")

    if nouveau == ancien:
        print("JSON inchangé, pas de commit.")
    else:
        with open(JSON, "w", encoding="utf-8") as f:
            f.write(nouveau)
        if "--sans-commit" in sys.argv:
            print("JSON mis à jour (--sans-commit : pas de commit).")
        elif not os.path.isdir(os.path.join(DEPOT, ".git")):
            print("Pas de dépôt git ici (git init à faire) : pas de commit.")
        else:
            git("add", "AideEnLigne.json")
            msg = f"Mise à jour AideEnLigne.json ({mode}) : {len(resultat)} rubriques, +{de_reference} de la référence, +{nouvelles} nouvelles, {modifiees} commentaires modifiés"
            r = git("commit", "-m", msg)
            print("Commit fait." if r.returncode == 0 else "Échec du commit : " + (r.stdout + r.stderr).strip())

    epure = "--epure" in sys.argv
    if a_marquer or epure:
        if thunderbird_ouvert():
            print("Thunderbird est ouvert : boîte non modifiée "
                  f"({len(a_marquer)} messages non marqués comme lus"
                  + (", épuration non faite" if epure else "") + "). Ferme Thunderbird et relance le script.")
        else:
            if a_marquer:
                marquer_lus(a_marquer)
                print(f"{len(a_marquer)} messages marqués comme lus.")
            if epure:
                print(f"Épuration : {epurer(rubriques)} anciens messages supprimés de la messagerie.")

    if complet:
        etat["DernierComplet"] = mois
    etat["DernierLancement"] = aujourd.isoformat()
    with open(ETAT, "w", encoding="utf-8") as f:
        json.dump(etat, f, indent=2)


main()
