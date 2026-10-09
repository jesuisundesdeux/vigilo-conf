# AGENTS.md — vigilo-conf

Informations pour les agents IA (et les humains) qui travaillent sur ce dépôt.

## Le projet

Configuration partagée de [Vigilo](https://vigilo.city), lue **en direct** (fichiers bruts sur
`raw.githubusercontent.com/jesuisundesdeux/vigilo-conf/main/main/…`) par :

- l'application web [vigilo-webapp](https://github.com/jesuisundesdeux/vigilo-webapp) (app.vigilo.city) ;
- d'anciennes applications mobiles encore en circulation ;
- le site [vigilo-website](https://github.com/jesuisundesdeux/vigilo-website) (construit chaque jour) ;
- le backend [vigilo-backend](https://github.com/jesuisundesdeux/vigilo-backend) (catégories nationales, mises en cache).

Une modification fusionnée sur `main` est donc **immédiatement en production** pour tous ces clients.

## Fichiers

| Fichier | Contenu |
|---|---|
| `main/citylist.json` | Instances en service : `{"Nom affiché": {"api_path", "scope", "prod", "country"}}`. `prod: false` = instance de test, visible seulement en mode beta. Schéma : `main/citylist.schema.json` |
| `main/citylist-hs.json` | Instances hors service retirées de `citylist.json`, avec `hs_since` (date) et `hs_reason`. Pour réactiver : remettre l'entrée dans `citylist.json` sans ces deux champs |
| `main/categorielist.json` | Catégories nationales : `catid`, `catname`, `catname_en_US`, `catcolor` (nom ou couleur CSS), `catresolvable`, `catdisable` (facultatif). Schéma : `main/categorielist.schema.json` |

## Règles à respecter

- **Ne jamais changer ni réutiliser un `catid`** : les observations existantes y font référence. Pour retirer une
  catégorie, mettre `"catdisable": true`. Les numéros à partir de 1000 sont réservés aux catégories propres à chaque
  instance (backend ≥ 0.0.23) : ne pas les utiliser ici.
- **Nom d'une instance** (clé de `citylist.json`) : il sert d'identifiant dans les URL (`?instance=<nom>`) et dans le
  stockage local des utilisateurs : ne pas le renommer sans raison.
- `scope` au format `XX_nom` (numéro de département ou code pays, puis nom sans espace), identique au scope configuré
  sur l'instance ; `api_path` sans `/` final.
- JSON valide et conforme aux schémas (vérifié par la CI) ; garder l'indentation existante et ne modifier que les
  lignes nécessaires (diffs lisibles).
- Messages de commit et documentation en **français**.

## Vérifications

- `json_city_check.yml`, `json_category_check.yml` : validation des JSON par leurs schémas à chaque push.
- `instances_check.yml` : interroge chaque instance de `citylist.json` (`get_scope.php`, `get_issues.php`) à chaque
  modification, chaque lundi et à la demande ; échoue si une instance ne répond pas (la déplacer alors dans
  `citylist-hs.json`). Crée une release GitHub `check-instance-<DATE>` contenant `check_result.json` (date UTC, bilan ok/down,
  détail par instance) lors d'un push sur les fichiers surveillés, du planning hebdomadaire ou d'un déclenchement
  manuel. La dernière release est accessible via
  `GET /repos/jesuisundesdeux/vigilo-conf/releases/latest`.

En local :

```sh
python3 -c "import json; [json.load(open(f)) for f in ['main/citylist.json','main/citylist-hs.json','main/categorielist.json']]"
```

Pour tester le check des instances et inspecter le JSON produit :

```sh
python3 .github/scripts/check_instances.py
python3 -c "import json; d=json.load(open('check_result.json')); print(d['date'], d['summary'])"
```
