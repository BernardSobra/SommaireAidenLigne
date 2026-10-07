"""Thèmes des rubriques de l'aide en ligne (brouillon, pas encore utilisé par aide.py).

Un thème est cherché dans cet ordre :
1. règles sur le titre (RegleTitre), pour les rubriques sans catégorie et les catégories trop générales ;
2. catégorie du dictionnaire WLangage (champ `category` de pages/<numéro d'aide>.md) ;
3. thème par défaut d'une catégorie générale ;
4. « Divers ».
"""
import os, re

DICTIONNAIRE = r"C:\Users\Admin\.claude\skills\windev-wlangage\pages"

# thème -> catégories du dictionnaire
THEMES = {
    "HFSQL": ["fonctions_hyper_file", "fonctions_cs", "hfcs", "cluster", "client_serveur", "wdadmin_hf", "wdjournal",
              "themes"],
    "SQL": ["fonctions_sql", "wdsql", "wdmaria_db", "wdmy_sql", "WDOracle", "wdpostgre_sql", "wdsql_server_demo",
            "wdsybase_demo", "wddixio"],
    "NoSQL": ["fonctions_mongo", "fonctions_redis", "fonctions_memcached"],
    "Big Data": ["fonctions_h_base", "fonctions_hdfs"],
    "Requêtes": ["requete", "requete_description", "test"],
    "Réplication": ["fonctions_replication", "replic_edit", "replic_synchro", "nomade"],
    "États et impression": ["etat", "etat_editeur", "etat_imbrique", "etat_champs", "fonctions_impression", "dossier"],
    "Chaînes": ["fonctions_chaine", "masques", "fonctions_masque"],
    "Traitement de texte": ["fonctions_traitement_texte"],
    "Dates": ["fonctions_date", "fonctions_pays"],
    "PDF": ["fonctions_pdf", "champ_lecteur_pdf"],
    "Tableur": ["fonctions_xls", "fonctions_tableur", "champ_tableur"],
    "XML": ["fonctions_xml", "fonctions_soap", "fonctions_xaml"],
    "JSON": ["fonctions_json"],
    "HTML": ["fonctions_html", "fonctions_editeur_html", "champ_html"],
    "Zip": ["fonctions_zip"],
    "Multimédia": ["fonctions_multimedia", "fonctions_exif", "fonctions_pic", "fonctions_ocr", "fonctions_code_barres",
                   "fonctions_scan", "fonctions_synthese_vocale", "fonctions_camera_video", "champ_web_camera",
                   "champ_image"],
    "E-mail": ["fonctions_emails", "fonctions_notes"],
    "FTP": ["fonctions_ftp"],
    "SSH": ["fonctions_ssh"],
    "HTTP": ["fonctions_http", "fonctions_uri", "fonctions_telechargement", "fonctions_rss", "fonctions_navigateur"],
    "Webservices": ["fonctions_webservice"],
    "Protocoles": ["fonctions_websocket", "fonctions_mqtt", "fonctions_modbus", "fonctions_snmp", "fonctions_upnp"],
    "Matériel": ["fonctions_btle", "fonctions_beacon", "fonctions_nfc", "fonctions_usb", "fonctions_gps_geo"],
    "Drive": ["fonctions_drive"],
    "Salesforce": ["fonctions_sales_force"],
    "Google": ["fonctions_google_agenda", "fonctions_google_contacts", "fonctions_google_document", "fonctions_google",
               "fonctions_notif"],
    "Services tiers": ["fonctions_facebook"],
    "Bitcoin": ["fonctions_bitcoin"],
    "IA": ["fonctions_ia"],
    "Sécurité": ["fonctions_gpw", "fonctions_cryptage", "fonctions_certificat", "fonctions_permission", "fonctions_auth_token",
                 "serveur_o_auth", "audits", "exigences"],
    "Champs": ["fonctions_champ", "fonctions_selecteur", "fonctions_interrupteur", "fonctions_bouton_segmente",
               "fonctions_champ_saisie_assistee", "fonctions_champ_saisie_jetons", "fonctions_combo",
               "fonctions_zone_multiligne", "fonctions_onglet", "fonctions_action_rapide", "champ_bouton",
               "champ_bouton_segmente", "champ_selecteur", "champ_interrupteur", "champ_liste_image", "champ_lien",
               "champ_flexbox", "champ_action_bar", "modele_champs", "commun", "volet_ancrable", "styles_wd"],
    "Tables et listes": ["fonctions_liste", "fonctions_table", "fonctions_table_hierarchique", "fonctions_zones_repetees",
                         "fonctions_file_pile", "champ_liste", "champ_table", "champ_zone_repetee", "champ_arbre"],
    "Tableau croisé": ["fonctions_tcd", "champ_tableau_croise_dynamique"],
    "Tableaux": ["fonctions_tableau", "fonctions_combi_enum"],
    "Graphes": ["fonctions_graphe"],
    "Cartes": ["fonctions_carte", "champ_carte", "fonctions_google_map", "fonctions_spatiales"],
    "Dessin": ["fonctions_dessin", "fonctions_dessin_liste", "fonctions_police", "fonctions_palette"],
    "Planning": ["fonctions_agenda", "fonctions_planning", "fonctions_rendez_vous", "fonctions_gantt", "fonctions_kanban",
                 "champ_diagramme_de_gantt", "fonctions_organigramme"],
    "Diagrammes": ["fonctions_editeur_diagrammes", "champ_editeur_diagrammes"],
    "Fenêtres et menus": ["fonctions_fenetre", "fonctions_page", "fonctions_menu", "fonctions_visite_guidee", "aide",
                          "gabarit", "page", "raccourcis"],
    "Dialogues": ["fonctions_dialogue_boite", "fonctions_dialogue_toast", "fonctions_sys_notif"],
    "Contacts": ["fonctions_contact"],
    "Pays et TVA": ["fonctions_siren_siret"],
    "WLangage": ["instructions_struc", "operateurs", "variables", "declaration_des_variables", "type_avance", "procedure",
                 "programmation", "type_de_donnees", "type_de_variable", "fonctions_reflexion", "fonctions_exception",
                 "fonctions_3_tiers", "divers_windev", "mots_reserves", "visual_basic", "divers_windows"],
    "POO": ["poo"],
    "Tâches parallèles": ["fonctions_taches_paralleles", "fonctions_thread"],
    "Éditeur de code": ["fonctions_editeur_de_code", "code", "fonctions_dbg"],
    "Système": ["fonctions_sys", "fonctions_exe", "fonctions_commande", "fonctions_planificateur",
                "fonctions_taches_planifiees_wb", "fonctions_presse_papier", "evenement_windows", "fonctions_fext",
                "vista", "64_bits", "linux", "wdscript"],
    "Multilingue": ["fonctions_multilangue"],
    "Mobile": ["android", "i_phone_i_pad", "fonctions_in_app"],
    "Déploiement": ["install_wdwdinst", "install_wdassistant", "install_ww", "install_ww_etapes", "install_wd", "wdsetup",
                    "wddeploie", "wdetat_utilisateur", "wdautomatic_update", "executable_wd", "fabrique_logicielle", "wdint", "wdmsg"],
    "Serveur WEBDEV": ["wdadmin", "fonctions_saas", "fonctions_admin", "site_ww", "page_awp", "test_webdev", "presentation",
                       "partie7", "divers_webdev", "divers_themes", "cc100_hebergement"],
    "Outils": ["gds", "fonctions_telemetrie", "robot", "cc100_suivi", "fonctions_faa", "faa", "composant",
               "assemblages_net", "modelisation", "projet", "environnement", "divers"],
    "Tutoriel": ["partie1", "partie2", "partie3", "partie4", "partie5", "partie6", "partie8", "partie9", "partie0",
                 "partie_1", "partie_2", "partie_3", "partie_4", "partie_5", "partie_6", "partie_7", "partie_8", "partie_9",
                 "partie_10", "partie_11", "partie_12", "partie_13", "Partie_1B", "introduction", "sommaire"],
    "Nouveautés": ["nouveautes"],
    "Support": ["support"],
    "WEBDEV": [],
}

# Défaut d'une catégorie générale quand aucune règle de titre ne s'applique
GENERIQUES = {"proprietes": "Propriétés", "windev": "Outils"}

CATEGORIE_VERS_THEME = {c: t for t, l in THEMES.items() for c in l}

# (motif sur le titre, thème), dans l'ordre. Sert aux rubriques sans catégorie et aux catégories générales.
REGLES_TITRE = [
    (r"FAA", "Outils"),
    (r"^Nouveautés", "Nouveautés"),
    (r"Licence", "Licences"),
    (r"^[Hh][A-ZÉ]|HFSQL|IndexSémantique|NbRubriqueCléSpatiale|CléSémantique|Serveur HFSQL", "HFSQL"),
    (r"Chat IA|\bIA\b|^ia[A-ZÉ]|^IA[A-ZÉ]|Compagnon IA|Agent IA|agents IA|émantique|Gemini|ChatGPT|Transcription audio|"
     r"Dictée vocale|MCP|Prompt|Embedding|Hnsw|^Tools|NomModel|CléApi|Vecteur|DemandeEnCours|^Conversation|SousAgents|"
     r"LibelléAssistant|ImageAssistant|Services IA|^Modèle|AutoriseQuestions|Confiance|Fournisseur|Segment|"
     r"DuréeChevauchement|DuréeChunk|Langue(Audio|Transcription)|TexteConfirmé|TextePartiel|ProcédureProgression|"
     r"ChatIA|Variable\s+ia|QuestionInteractive|SaisieUtilisateur|Fautes de frappe|Anonymiser des photos|Estimer l'âge", "IA"),
    (r"Grille", "Grille"),
    (r"Rouleau|Sélecteur de fichiers|Skeleton|Réglette|Enroulable|DéfilementCirculaire|Vibration|Grisé|Notation|"
     r"ModeAncrage", "Champs"),
    (r"[Cc]arte|Calque|^Marqueur", "Cartes"),
    (r"[Gg]raphe|^gr[A-Z]|courbe de lissage", "Graphes"),
    (r"Drive", "Drive"),
    (r"Bitcoin", "Bitcoin"),
    (r"Shopify|Teams|Didit|BigQuery", "Services tiers"),
    (r"Certificat|Sécurité|sécurité|Coffre|signature|UAC|Clé de sécurité|Sécuriser", "Sécurité"),
    (r"Éditeur de code|Editeur de code|EditeurCode|Complétion de code|CodeSQL|CodeWLangage|CodeDonne|DéclarationCSS", "Éditeur de code"),
    (r"[Ss]erveur d['’]application WEBDEV|Administrateur WEBDEV|comptes WEBDEV|compte de déploiement|"
     r"IIS|Site web|site WEBDEV|Cluster WEBDEV|mode maintenance|^Web\s*:|Webiser|webiser|Impression depuis le serveur|"
     r"Fournir un lien|Présentation du Serveur", "Serveur WEBDEV"),
    (r"Connecteur[s]? Natif|BigQuery", "SQL"),
    (r"Type Chaîne|Chaîne|Markdown|Chaînes littérales", "Chaînes"),
    (r"^Doc[A-Z]|ReprendreNumérotation", "Traitement de texte"),
    (r"Variable\s+pdf|^pdf[A-Z]", "PDF"),
    (r"[Dd]iagrammes", "Diagrammes"),
    (r"JSON", "JSON"),
    (r"XML", "XML"),
    (r"HTTP", "HTTP"),
    (r"FacturX|Factur-X", "États et impression"),
    (r"EPUB", "Multimédia"),
    (r"composant Web|contenu destiné au Web", "HTML"),
    (r"[Mm]ultilingue", "Multilingue"),
    (r"Robot de surveillance|GDS", "Outils"),
    (r"RéutiliseConnexion", "HFSQL"),
    (r"GraphQL|graphql|Webservice", "Webservices"),
    (r"Email|IMAP|Office 365|emails", "E-mail"),
    (r"SSH", "SSH"),
    (r"MQTT", "Protocoles"),
    (r"Impression|impression|spooler|états interactifs|états et des requêtes|Tâche?Impression", "États et impression"),
    (r"Planning|Zone Répétée|zone répétée|Tables WEBDEV|champ Table|OuvrePopupListe|Liste", "Tables et listes"),
    (r"TCD", "Tableau croisé"),
    (r"^dTexte|<Image>|Palette|palette", "Dessin"),
    (r"Toast|toast|notifications", "Dialogues"),
    (r"menu|Menu|FenListe|Fenêtre|Interagir", "Fenêtres et menus"),
    (r"iOS|Android|itinérant|App Store|Datalogic", "Mobile"),
    (r"Transaction", "HFSQL"),
    (r"Hot Reload|DLL", "Outils"),
    (r"Procédure|^Instructions|clonage|WLangage|POUR TOUT|Entier|Dimension|Compile|SectionCritique|EnMode|SysNom|"
     r"Récupérer l'heure", "WLangage"),
    (r"Police|Couleur|Cadre|Icone|Bulle|Monochrome|Arrondi|Cadrage|Largeur|Hauteur|^X \(|^Y \(|Visible|MiseEnPage|Titre \(|"
     r"Thème \(|Image \(|Taille|ModeAffichage|ModeLoupe|ModeManipulation", "Apparence"),
    (r"Copie non bloquante|fichiers après installation|Signer et faire reconnaître|exe|Installation|installation|"
     r"Déploiement|déploiement|Mise à jour automatique", "Déploiement"),
    (r"Notation|Aide de WINDEV|Dépannage|6 (astuces|évolutions)|Paroles d'expert|Derniers articles|BEST PRA", "Outils"),
]
REGLES_TITRE = [(re.compile(m), t) for m, t in REGLES_TITRE]


def categorie(numero_aide):
    """Catégorie du dictionnaire pour un numéro d'aide, ou None."""
    chemin = os.path.join(DICTIONNAIRE, numero_aide + ".md")
    if not os.path.exists(chemin):
        return None
    with open(chemin, encoding="utf-8") as f:
        m = re.search(r'^category:\s*"([^"]*)"', f.read(1500), re.M)
    return m.group(1) if m and m.group(1) else None


# Catégories trop larges : un titre explicite l'emporte sur la catégorie
LARGES = {"divers_windev", "type_de_variable", "projet", "environnement", "divers", "divers_webdev", "divers_themes",
          "divers_windows", "themes", "windev", "proprietes"}


def theme(titre, numero_aide):
    cat = categorie(numero_aide)
    if cat and cat not in LARGES and cat in CATEGORIE_VERS_THEME:
        return CATEGORIE_VERS_THEME[cat], "catégorie"
    for motif, th in REGLES_TITRE:
        if motif.search(titre):
            return th, "titre"
    if cat in GENERIQUES:
        return GENERIQUES[cat], "défaut"
    if cat in CATEGORIE_VERS_THEME:
        return CATEGORIE_VERS_THEME[cat], "catégorie"
    if titre.endswith("(Propriété)"):
        return "Propriétés", "défaut"
    return "Divers", "défaut"
