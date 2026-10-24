# Mes boosters

Suivi de collection des boosters Pokémon français : chaque visuel de chaque extension, de Set de Base (1999) à Méga-Évolution, plus les boosters échantillons, avant-premières, McDonald's et Packs Récompense Play! Pokémon.

**App : https://guillaumecazelles.github.io/pokemon-boosters-fr/**

- Toucher un booster l'ajoute à la collection ; le toucher encore le retire. Maintenir appuyé l'agrandit.
- Une page par extension, avec son sigle officiel, sa date de sortie et le prix d'un booster.
- Filtres par bloc (Wizards, EX, Diamant & Perle, …, Méga-Évolution), boosters manquants, sans échantillons.
- Onglet Prix : prix moyen de vente Cardmarket d'un booster de chaque extension, valeur de la collection et coût pour la compléter.
- La collection est enregistrée dans le navigateur de chaque appareil ; sauvegarde et restauration depuis le menu ☰.
- Sur iPhone : Safari → Partager → « Sur l'écran d'accueil ».

## Mettre à jour

L'app est un seul fichier, `index.html`, généré par :

```bash
cd build
python build.py
```

`build.py` relit la liste des visuels de boosters sur Poképédia et le guide des prix Cardmarket, puis régénère `../index.html`. `python build.py --offline` réutilise les fichiers déjà téléchargés.

| Fichier | Contenu |
|---|---|
| `build/template.html` | l'app (HTML, CSS, JS) |
| `build/src/pp_boosters.json` | fichiers « Booster_… » de Poképédia (nom, URL, taille) |
| `build/src/fr_sets_full.json`, `en_sets.json` | extensions TCGdex (noms, dates, sigles) |
| `build/src/extra.json` | corrections manuelles : fichiers ignorés, extensions absentes de TCGdex, McDonald's, Packs Récompense, visuels ajoutés |
| `build/src/icon.png` | icône de l'écran d'accueil |

## Sources

Visuels : [Poképédia](https://www.pokepedia.fr) (images chargées depuis Poképédia, redimensionnées à la volée par [wsrv.nl](https://wsrv.nl)). Extensions : TCGdex. Prix : guide des prix public Cardmarket. Projet de fan non officiel ; Pokémon et les visuels des boosters appartiennent à Nintendo, Creatures et GAME FREAK.
