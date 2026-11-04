---
name: retry-instances
description: Réessayer les instances Vigilo hors service (main/citylist-hs.json) et ouvrir une PR qui remonte dans main/citylist.json celles redevenues joignables. À utiliser quand l'utilisateur veut vérifier si des instances en panne sont revenues et les réactiver.
---

# Réessayer les instances hors service

Déclenche le workflow `retry_instances.yml` (« Retry instances ») de
`jesuisundesdeux/vigilo-conf`, qui teste chaque instance de `main/citylist-hs.json`
(même contrôle que `instances_check.yml`) et, pour celles redevenues joignables, retire
`hs_since`/`hs_reason` et les déplace dans `main/citylist.json` via une **pull request**
(rien n'est mis en production sans relecture : une fusion sur `main` est immédiate).

## Étapes

1. Déclencher le workflow sur `main` :
   `mcp__github__actions_run_trigger` — owner `jesuisundesdeux`, repo `vigilo-conf`,
   workflow `retry_instances.yml`, ref `main`.
   (Si l'accès GitHub n'est pas encore accordé à vigilo-conf, l'ajouter avec `add_repo`.)
2. Retrouver le run (`mcp__github__actions_list` / `actions_get`) et suivre son état
   jusqu'à la fin (ne pas boucler avec `sleep`).
3. Rapporter le résultat :
   - si des instances sont remontées : donner le **lien de la PR** ouverte (à relire puis
     fusionner) et la liste des instances concernées (dans le résumé du run) ;
   - sinon : indiquer qu'**aucune instance HS n'est encore joignable** (le résumé du run
     liste pour chacune la raison toujours en panne).

## Notes

- Le workflow n'ouvre une PR que si au moins une instance est revenue (sortie `moved=1`
  du script `retry_instances.py`).
- Rappel : une PR créée par le workflow (avec `GITHUB_TOKEN`) ne redéclenche pas tout seul
  les workflows de vérification de la PR ; les relancer depuis l'onglet Actions si besoin.
- Pour contrôler les instances **en service**, voir la skill `refresh-instances`.
