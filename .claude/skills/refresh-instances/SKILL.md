---
name: refresh-instances
description: Relancer à la demande la vérification de l'état des instances Vigilo listées dans main/citylist.json (workflow « Check instances »), puis rapporter le bilan. À utiliser quand l'utilisateur veut un contrôle frais des instances en service (ok / en panne).
---

# Rafraîchir l'état des instances

Déclenche le workflow **existant** `instances_check.yml` (« Check instances ») de
`jesuisundesdeux/vigilo-conf`, qui teste chaque instance de `main/citylist.json`
(get_scope, get_issues, image du panneau, HTTPS/CORS) et publie un rapport.

## Étapes

1. Déclencher le workflow sur `main` :
   `mcp__github__actions_run_trigger` — owner `jesuisundesdeux`, repo `vigilo-conf`,
   workflow `instances_check.yml`, ref `main`.
   (Si l'accès GitHub n'est pas encore accordé à vigilo-conf, l'ajouter avec `add_repo`.)
2. Retrouver le run lancé (`mcp__github__actions_list` ou `actions_get`) et suivre son
   état jusqu'à la fin (ne pas boucler avec `sleep` ; espacer les vérifications).
3. Rapporter le bilan :
   - le **résumé** du run (tableau « Vigilo instances: N OK, M down ») ;
   - le JSON détaillé est aussi publié dans la release `check-instance-<DATE>`
     (ou `GET /repos/jesuisundesdeux/vigilo-conf/releases/latest`).
4. Si des instances sont **down**, les signaler clairement : il faudra les déplacer
   dans `main/citylist-hs.json` (avec `hs_since` + `hs_reason`).

## Notes

- Le workflow tourne aussi tout seul chaque lundi et à chaque modification de
  `citylist.json` ; cette skill sert à le relancer **manuellement**.
- Pour l'opération inverse (réessayer les instances HS et les remonter), voir la skill
  `retry-instances`.
