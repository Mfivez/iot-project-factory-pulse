# Interface minimale pour l'agent
À développer par l'équipe 3, avec revue des équipes 1 et 2. Commencer avec des fonctions Python locales ; les exposer ensuite comme outils MCP seulement si la lecture de données fonctionne.

- get_status(station_id, at_utc) : dernière télémétrie, dernier health, âge des données, état du nœud et état machine distincts.
- get_history(station_id, from_utc, to_utc) : télémétries dans l'intervalle, bornes incluses, au maximum 500 événements.
- get_logs(station_id, from_utc, to_utc) : logs de cette station ET logs SERVER dont target_station désigne cette station, au maximum 100 événements.
- get_inspections(from_utc, to_utc) : inspections Q01 dédupliquées par event_id, au maximum 100.

Toutes les réponses : objet JSON avec as_of_utc, events (événements originaux avec event_id), warnings (limites, données absentes ou tronquées). Status peut ajouter summary avec node_state, machine_state et data_age_s. Ne pas supprimer les preuves brutes. Limiter les bornes supérieures au curseur de replay ; refuser les identifiants non autorisés et les dates incorrectes.
La documentation procédures.md et config.json sont accessibles en lecture. Le dossier tests/ et les attendus de l'enseignant ne sont pas accessibles à l'agent pendant son évaluation.
Les fonctions ne doivent proposer aucun argument chemin libre, commande shell ou SQL libre. Pas de SSH/root/MQTT de commande. Pour la V1, le professeur importe les fichiers dans un dossier de diagnostic ne contenant que les entrées autorisées. Il doit appliquer les droits en lecture, indépendamment du prompt.
Sur le réseau physique, remplacer la source fichier par la collecte autorisée de FactoryPulse, sans élargir les droits de l'agent à tout le réseau de l'école.
Le serveur MCP et l'agent ne sont pas implémentés dans ce kit. Codex dans VS Code est utilisé à la demande ; la surveillance automatique est une extension distincte.
