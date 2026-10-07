# vigilo-conf

Configuration partagée par les applications Vigilo ([app.vigilo.city](https://app.vigilo.city), application Android, site [vigilo.city](https://vigilo.city)).

- `main/citylist.json` : les instances (territoires), avec l'adresse de leur API (`api_path`), leur `scope` et `prod` (`false` : instance de test, visible seulement en mode beta).
- `main/categorielist.json` : les catégories d'observations.
- `main/citylist-hs.json` : les instances hors service, retirées de `citylist.json`, avec la date (`hs_since`) et la raison (`hs_reason`). Pour réactiver une instance, remettre son entrée dans `citylist.json` sans ces deux champs.

## Vérification des instances

Le workflow [Check instances](.github/workflows/instances_check.yml) interroge chaque instance de `citylist.json` (`get_scope.php`, `get_issues.php`) à chaque modification du fichier, chaque lundi et à la demande. Le rapport (instances hors service, version du backend, date de la dernière observation) est affiché dans le résumé de l'exécution ; l'exécution échoue si une instance ne répond pas.
