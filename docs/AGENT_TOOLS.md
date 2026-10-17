# Interface minimale pour l'agent
À développer par l'équipe 3, avec revue des équipes 1 et 2. Commencer avec des fonctions Python locales ; les exposer ensuite comme outils MCP seulement si la lecture de données fonctionne.

- get_status(station_id, at_utc) : dernière télémétrie, dernier health, âge des données, état du nœud et état machine distincts.
- get_history(station_id, from_utc, to_utc) : télémétries dans l'intervalle, bornes incluses, au maximum 500 événements.
- get_logs(station_id, from_utc, to_utc) : logs de cette station ET logs SERVER dont target_station désigne cette station, au maximum 100 événements.
- get_inspections(from_utc, to_utc) : inspections Q01 dédupliquées par event_id, au maximum 100.
- get_latest_temperature_exceedance(at_utc) : dernière télémétrie M01 au-dessus du seuil configuré.
- search_tech_docs(query, category=None, top_k=5) : recherche sémantique multilingue dans la documentation technique autorisée (fiches matériel, fiches techniques, références, montages, procédures, vision). Les données retournées sont des données non fiables (`trust: "untrusted_document_data"` et mention `data_notice`) et ne doivent jamais être traitées comme des instructions exécutables.

Toutes les réponses : objet JSON avec as_of_utc, events (événements originaux avec event_id), warnings (limites, données absentes ou tronquées). Status peut ajouter summary avec node_state, machine_state et data_age_s. `data_age_s` est l'âge de la dernière télémétrie à `as_of_utc` ; il vaut null si la station n'émet pas de télémétrie. `node_state` provient du dernier `health`, tandis que `machine_state` provient de la dernière télémétrie M01. Ne pas supprimer les preuves brutes. Limiter les bornes supérieures au curseur de replay et signaler ce plafonnement dans `warnings` ; inclure les deux bornes des historiques. Refuser les identifiants non autorisés, les dates incorrectes et les intervalles inversés. Si le plafond de résultats est dépassé, retourner les événements les plus anciens dans l'ordre chronologique et signaler la troncature.
Une date de consultation ou un début d'intervalle antérieur à `replay.start_utc` est refusé. Une borne supérieure après `replay.as_of_utc` reste plafonnée avec avertissement.

La documentation procédures.md et config.json sont accessibles en lecture. Le dossier tests/ et les attendus de l'enseignant ne sont pas accessibles à l'agent pendant son évaluation.
Les fonctions ne doivent proposer aucun argument chemin libre, commande shell ou SQL libre. Pas de SSH/root/MQTT de commande. Pour la V1, le professeur importe les fichiers dans un dossier de diagnostic ne contenant que les entrées autorisées. Il doit appliquer les droits en lecture, indépendamment du prompt.
Sur le réseau physique, remplacer la source fichier par la collecte autorisée de FactoryPulse, sans élargir les droits de l'agent à tout le réseau de l'école.
Le serveur MCP et l'agent ne sont pas implémentés dans ce kit. Codex dans VS Code est utilisé à la demande ; la surveillance automatique est une extension distincte.
