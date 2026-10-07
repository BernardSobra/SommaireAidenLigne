# AideEnLigne

Index des rubriques de l'aide en ligne PC SOFT (WINDEV / WEBDEV / WINDEV Mobile), extrait des messages de flux enregistrés dans `R:\MessagesAideWindev\` (fichiers `.eml`).

## Fichiers

| Fichier | Rôle |
|---|---|
| `AideEnLigne.json` | Les données : un enregistrement par message `.eml` |
| `aide.py` | Script Python qui génère le JSON à partir des `.eml` |

## Format de `AideEnLigne.json`

Fichier UTF-8 contenant un tableau d'objets. Chaque objet a trois champs texte :

| Champ | Origine dans le `.eml` | Contenu |
|---|---|---|
| `Titre` | en-tête `Subject` | Nom de la rubrique, entités HTML décodées (`&lt;Carte&gt;` devient `<Carte>`), avec son type entre parenthèses |
| `Adresse` | en-tête `Content-Base` | URL de la rubrique, sans le paramètre `&name=...` |
| `Commentaire` | corps `<body>` | Résumé de la rubrique, balises retirées, espaces réduits |

### Exemple

```json
{
  "Titre": "<Carte>.IdentifiantGgl (Fonction)",
  "Adresse": "https://doc.pcsoft.fr/fr-FR/?1410091156",
  "Commentaire": "Renvoie ou modifie le style de la carte affichée dans le champ Carte. Ce style correspond à un ID de carte défini dans la console Google Cloud."
}
```

## Contenu (état au 07/10/2026)

- **3 539 enregistrements**, un par fichier `.eml`.
- Aucun champ vide : chaque enregistrement a un titre, une adresse et un commentaire.
- **Doublons** : seulement 1 882 adresses et 1 905 titres distincts, et 2 104 enregistrements distincts. Une même rubrique peut avoir été enregistrée plusieurs fois (fichiers `... 1435-2.eml`, ou versions successives de la doc). Dédoublonner par `Adresse` ou par `Titre` selon l'usage.
- Répartition par type, d'après le suffixe du titre :

| Type | Nombre |
|---|---|
| Fonction | 1 120 |
| Type de variable | 820 |
| Propriété | 232 |
| syntaxe préfixée | 29 |
| autres suffixes (IA, Update, GDS, Exemple...) | quelques unités chacun |
| titre sans suffixe entre parenthèses | 1 264 |

## Régénérer le JSON

```bash
python aide.py
```

Le script lit `R:\MessagesAideWindev` et écrit `AideEnLigne.json` dans ce dossier. Les chemins sont les variables `rep` et `sortie` en tête du script.

## Source et droits

Les textes viennent de la documentation en ligne de PC SOFT (`https://doc.pcsoft.fr`). Ils restent la propriété de PC SOFT : le JSON est un index de travail, à ne pas republier tel quel.
