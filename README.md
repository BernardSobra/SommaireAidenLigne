# AideEnLigne

Index des rubriques de l'aide en ligne PC SOFT (WINDEV / WEBDEV / WINDEV Mobile), construit à partir du compte Thunderbird **PC SOFT AIDE EN LIGNE**, dossier **« PC SOFT - Quoi de neuf dans l'aide en ligne »**.

## Fichiers

| Fichier | Rôle |
|---|---|
| `AideEnLigne.json` | Les données : une rubrique par adresse d'aide |
| `aide.py` | Script Python qui met à jour le JSON depuis Thunderbird |
| `etat.json` | État du script (mois du dernier passage complet). Non versionné |
| `sauvegarde\` | Copie de la boîte Thunderbird avant marquage « lu » ou épuration. Non versionné |

## Format de `AideEnLigne.json`

Fichier UTF-8 contenant un tableau d'objets. Chaque objet a trois champs texte :

| Champ | Origine dans le message | Contenu |
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

### Clé unique : l'adresse

Une rubrique est identifiée par son **adresse** (le numéro d'aide après `?`), jamais par son titre. Le JSON contient donc une seule entrée par adresse. Quand une rubrique revient avec un texte différent, le message le plus récent remplace l'ancien, à la même place dans le fichier.

## Mise à jour : `python aide.py`

Le script lit directement le dossier Thunderbird, en lecture seule (Thunderbird peut rester ouvert pour la lecture). Le chemin du profil est la constante `BOITE`, en tête du script.

| Mode | Quand | Ce qui est lu |
|---|---|---|
| **Incrémental** | par défaut | seulement les messages **« Non lu »** |
| **Complet** | au premier lancement de chaque mois, ou avec `--complet` | tous les messages, ajoutés au JSON existant |

**Le JSON n'est jamais vidé** : dans les deux modes, le script part du JSON existant. Une rubrique qui n'est plus dans la messagerie (message supprimé ou épuré) reste dans le JSON. Le passage complet sert à tout relire, tout ajouter et mettre à jour les commentaires.

À la fin :

1. **Commit** : si le JSON a changé, `git add` et `git commit` automatiques, avec le nombre de rubriques nouvelles et modifiées dans le message. Jamais de `push`.
2. **Marquage « lu »** : les messages pris en compte sont passés en « lu » dans Thunderbird, **uniquement si Thunderbird est fermé**. Sinon le script le signale, ne touche à rien et les messages restent « Non lu » (ils seront repris au prochain lancement, sans doublon grâce à la clé d'adresse). Avant toute modification de la boîte, elle est copiée dans `sauvegarde\`.
3. **Épuration** (option `--epure`, utilisable avec les deux modes) : les anciens messages d'une même adresse sont supprimés de la messagerie, seul le plus récent est gardé. Thunderbird doit être fermé. Une adresse n'est épurée que si elle est déjà dans le JSON. Le fichier d'index `.msf` est supprimé et Thunderbird le reconstruit à son démarrage. Si besoin, les messages peuvent être récupérés avec la mise à jour de l'aide de PC SOFT, ou avec la copie de `sauvegarde\`.

```bash
python aide.py --epure
```

Pour marquer les messages comme lus : fermer Thunderbird, lancer `python aide.py`, rouvrir Thunderbird.

## Contenu (état au 07/10/2026)

- **1 882 rubriques**, issues de 3 539 messages (les autres sont des enregistrements multiples d'une même adresse).
- Répartition d'après le suffixe du titre :

| Type | Nombre |
|---|---|
| Fonction | 676 |
| Type de variable | 363 |
| Propriété | 131 |
| syntaxe préfixée | 15 |
| Exemple | 3 |
| titre sans suffixe entre parenthèses | 664 |

## Source et droits

Les textes viennent de la documentation en ligne de PC SOFT (`https://doc.pcsoft.fr`). Ils restent la propriété de PC SOFT : le JSON est un index de travail, à ne pas republier tel quel.
