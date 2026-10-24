# Ce qui a changé par rapport à la première version

## Données

| Avant | Problème | Maintenant |
|---|---|---|
| Recherche Gutendex par titre, premier résultat | *The War of the Worlds* était en fait *The Mysteries of Udolpho* | Identifiant Gutenberg fixé pour chaque livre (`catalog.py`) |
| Fichier en cache réutilisé tel quel | *The Metamorphosis* était un fichier **vide**, jamais retéléchargé | `validate()` : taille minimale + mots attendus au début du texte, sinon le cache est supprimé et le livre retéléchargé |
| Découpage sur les lignes « CHAPTER » | 0 segment pour *The Jungle Book* et *The Time Machine*, et la table des matières comptée comme des chapitres | Segments de taille égale (~1 500 mots), quel que soit le livre |

## Analyse

| Avant | Problème | Maintenant |
|---|---|---|
| Llama 3 lit les 3 000 premiers caractères de chaque chapitre | ~10 % du livre analysé | **Tout** le texte est analysé |
| Note de 1 à 10 donnée par le LLM | Notes mal calibrées, qui sautent entre 2 et 8 | Comptage de mots d'émotion (lexique NRC), déterministe et traçable |
| Erreur → scores à 0 | Les erreurs faussaient les moyennes sans prévenir | Une erreur arrête le livre avec un message clair |
| Pas de lissage | Courbe = bruit | Filtre de Savitzky-Golay |
| 3 axes (absurde, peur, douceur) | *Dorian Gray* classé « absurde » | 6 émotions + imagerie + style + décor |
| Noms propres comptés | « Count Dracula », « the Queen »… lus comme des émotions | Mots en majuscule en milieu de phrase ignorés |

## Dessin

| Avant | Problème | Maintenant |
|---|---|---|
| Seule l'émotion dominante est gardée | 3 chats possibles : Dracula = Frankenstein, Dorian Gray = Alice | Paramètres **continus** (teinte, luminosité, oreilles, yeux, silhouette, bouche…) |
| Scores bruts comparés entre livres | Valeurs trop proches pour différencier les chats | **Rangs dans le corpus** : le livre le plus sombre a toujours le chat le plus sombre |
| Zigzag de la queue = `i % 2` | La forme ne venait pas des données | La queue suit l'arc émotionnel lissé |
| Longueur de la queue = nombre de chapitres | Queue de Dracula hors du cadre, par-dessus le titre | 20 points fixes, toujours dans le cadre (testé) |
| `if "ALICE" in titre` | Cas particulier codé en dur | Titres et auteurs viennent du catalogue |
| Aucune explication | Impossible de savoir pourquoi un chat est comme ça | Une explication par trait, affichée dans la galerie |

## Projet

- Package installable (`pip install -e .`) avec la commande `bookcats` : les imports marchent d'où qu'on lance le projet.
- 13 tests `pytest`, dont un test de non-régression pour la queue.
- Galerie HTML autonome, utilisable sur mobile.
- README rempli, `.gitignore` qui exclut les livres téléchargés et les caches.
