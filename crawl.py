"""Découvre les rubriques de l'aide en ligne absentes de AideEnLigne.json en suivant les liens des pages.

- Départ : les rubriques déjà dans le JSON. Chaque page lue donne ses liens (./?NNNN) ; tout numéro inconnu
  est lu à son tour (priorité aux nouveautés), jusqu'à épuisement.
- Une page lue donne : Titre, Anglais (« En anglais : ... »), Commentaire (paragraphe de définition, balise
  Description), Plateformes (icônes). Thème : règles de themes.py, comme aide.py.
- Fusion dans AideEnLigne.json : rubrique inconnue = ajoutée ; rubrique connue = seuls les champs vides
  (Anglais, Commentaire, Plateformes) sont complétés, jamais écrasés.
- Reprise possible : crawl_etat.json (pages vues, file d'attente) et crawl_pages.json (données lues).
  Ctrl+C = arrêt propre, fusion faite. Pas de commit (commit.bat).

Options : --limite N (arrêt après N pages lues), --pause S (secondes entre deux requêtes par tâche, 0.3),
--taches N (requêtes en parallèle, 3), --fusion-seule, --refaire (relit tout, ignore l'état).
"""
import os, re, json, html, sys, time, threading, urllib.request, urllib.error
from collections import deque
from concurrent.futures import ThreadPoolExecutor

import aide

DEPOT = aide.DEPOT
ETAT = os.path.join(DEPOT, "crawl_etat.json")
PAGES = os.path.join(DEPOT, "crawl_pages.json")
ACCUEIL = "PC SOFT - Documentation en ligne"

# icône de plateforme (nom du fichier, sans -off) => plateforme du JSON
ICONES = {
    "WD": "WINDEV", "WINDOWSWD": "WINDEV", "LXWD": "WINDEV", "JAVA": "WINDEV", "MCU": "WINDEV",
    "WBS": "WEBDEV", "WBN": "WEBDEV", "WINDOWSWB": "WEBDEV", "LXWB": "WEBDEV", "PHP": "WEBDEV", "AJAX": "WEBDEV",
    "ANDROID": "WINDEV MOBILE", "ANDROIDWIDGET": "WINDEV MOBILE", "IPHONE": "WINDEV MOBILE",
    "WIDGETIOS": "WINDEV MOBILE", "APPLEWATCH": "WINDEV MOBILE", "CATALYST": "WINDEV MOBILE",
    "ER": "ÉTATS ET REQUÊTES",
}
ORDRE = ["WINDEV", "WEBDEV", "WINDEV MOBILE", "ÉTATS ET REQUÊTES"]


def lire_page(numero):
    """Télécharge ?numero. Renvoie le HTML, ou None si l'erreur persiste (la page sera retentée plus tard)."""
    req = urllib.request.Request(aide.URL_AIDE + str(numero), headers={"User-Agent": "AideEnLigne-index/1.0 (usage personnel)"})
    for essai in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return ""
        except (urllib.error.URLError, TimeoutError, OSError):
            pass
        time.sleep(2 * (essai + 1))
    return None


def texte(fragment):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", fragment)).replace("\xa0", " ")).strip()


def analyser(numero, h):
    """(données de la page ou None si elle n'existe pas, numéros d'aide liés)."""
    liens = {int(n) for n in re.findall(r'href="(?:\./|https://doc\.pcsoft\.fr/fr-FR/)\?(\d+)[&"#]', h)}
    t = re.search(r"<title>(.*?)</title>", h, re.S)
    titre = re.search(r'<div class="title">(.*?)</div>', h, re.S)
    if not t or not titre or texte(t.group(1)) == ACCUEIL:
        return None, liens
    titre = texte(titre.group(1))
    anglais = re.search(r'<div class="subtitle">\s*En anglais\s*(?:&nbsp;|\s)*:\s*(.*?)</div>', h, re.S)
    commentaire = ""
    d = re.search(r'<meta name="Description"[^>]*content="([^"]*)"', h)
    if d:
        commentaire = texte(d.group(1))
        if commentaire.startswith(titre):
            commentaire = commentaire[len(titre):].lstrip(" -").strip()
    plateformes = set()
    for icone in re.findall(r'images/fr/([A-Za-z0-9]+)\.png[^"]*"[^>]*class="imgplateforme plateforme_on"', h):
        if icone in ICONES:
            plateformes.add(ICONES[icone])
    return {
        "ID": numero,
        "Titre": titre,
        "Anglais": texte(anglais.group(1)) if anglais else "",
        "Commentaire": commentaire,
        "Plateformes": [p for p in ORDRE if p in plateformes],
    }, liens


def charger(chemin, defaut):
    try:
        with open(chemin, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return defaut


def sauver(chemin, valeur):
    temp = chemin + ".tmp"
    with open(temp, "w", encoding="utf-8") as f:
        json.dump(valeur, f, ensure_ascii=False)
    os.replace(temp, chemin)


def fusionner(pages):
    """Fusionne crawl_pages.json dans AideEnLigne.json (JSON relu à l'instant : aide.py a pu le modifier)."""
    rubriques = {}
    for r in aide.lire_json():
        numero = str(r["ID"])
        rubriques[numero] = dict(r, ID=numero)
    ajoutees = completees = 0
    for numero, p in pages.items():
        if p is None:
            continue
        courante = rubriques.get(numero)
        if courante is None:
            rubriques[numero] = {"ID": numero, "Titre": p["Titre"], "Anglais": p["Anglais"],
                                 "Adresse": aide.URL_AIDE + numero, "Commentaire": p["Commentaire"],
                                 "Plateformes": p["Plateformes"]}
            ajoutees += 1
            continue
        change = False
        for champ in ("Anglais", "Commentaire", "Plateformes"):
            if not courante.get(champ) and p[champ]:
                courante[champ] = p[champ]
                change = True
        completees += change
    resultat = [aide.mise_en_forme(r) for r in rubriques.values()]
    nouveau = json.dumps(resultat, ensure_ascii=False, indent=2)
    ancien = ""
    if os.path.exists(aide.JSON):
        with open(aide.JSON, encoding="utf-8") as f:
            ancien = f.read()
    if nouveau != ancien:
        with open(aide.JSON, "w", encoding="utf-8") as f:
            f.write(nouveau)
    print(f"Fusion : {len(resultat)} rubriques, +{ajoutees} nouvelles, {completees} complétées.")


def main():
    args = sys.argv[1:]
    valeur = lambda nom, defaut: type(defaut)(args[args.index(nom) + 1]) if nom in args else defaut
    limite, pause, taches = valeur("--limite", 0), valeur("--pause", 0.3), valeur("--taches", 3)
    pages = {} if "--refaire" in args else charger(PAGES, {})
    if "--fusion-seule" in args:
        fusionner(pages)
        return
    etat = {} if "--refaire" in args else charger(ETAT, {})
    vus = set(etat.get("vus", []))
    connus = {str(r["ID"]) for r in aide.lire_json()}
    # file prioritaire : numéros découverts mais inconnus du JSON ; puis les rubriques du JSON (leurs liens)
    nouveaux = deque(n for n in etat.get("nouveaux", []) if n not in vus)
    graines = deque(sorted(n for n in connus if n not in vus))
    en_file = set(nouveaux) | set(graines)
    verrou = threading.Lock()
    arret = threading.Event()
    compte = {"lues": 0, "existantes": 0, "nouvelles": 0, "erreurs": 0}

    def suivant():
        with verrou:
            if limite and compte["lues"] >= limite:
                return None
            for file in (nouveaux, graines):
                if file:
                    compte["lues"] += 1
                    return file.popleft()
        return None

    def travail():
        while not arret.is_set():
            numero = suivant()
            if numero is None:
                return
            h = lire_page(numero)
            time.sleep(pause)
            with verrou:
                if h is None:
                    compte["erreurs"] += 1
                    continue
                vus.add(numero)
                page, liens = analyser(numero, h) if h else (None, set())
                pages[numero] = page
                if page:
                    compte["existantes"] += 1
                    compte["nouvelles"] += numero not in connus
                for n in map(str, liens):
                    if n not in vus and n not in en_file:
                        en_file.add(n)
                        (graines if n in connus else nouveaux).append(n)
                if compte["lues"] % 200 == 0:
                    enregistrer()
                    print(f"{compte['lues']} lues, {compte['nouvelles']} nouvelles, {len(nouveaux)} à voir en priorité, "
                          f"{len(graines)} rubriques connues à relire, {compte['erreurs']} erreurs", flush=True)

    def enregistrer():
        sauver(PAGES, pages)
        sauver(ETAT, {"vus": sorted(vus), "nouveaux": list(nouveaux)})

    # file d'attente en attente : comme les graines connues sont lues en dernier, on les mélange pas
    try:
        with ThreadPoolExecutor(max_workers=taches) as ex:
            for _ in range(taches):
                ex.submit(travail)
    except KeyboardInterrupt:
        arret.set()
        print("Arrêt demandé...")
    enregistrer()
    print(f"Terminé : {compte['lues']} pages lues, {compte['existantes']} existent, {compte['nouvelles']} absentes du JSON, "
          f"{compte['erreurs']} erreurs (retentées au prochain lancement).")
    fusionner(pages)


main()
