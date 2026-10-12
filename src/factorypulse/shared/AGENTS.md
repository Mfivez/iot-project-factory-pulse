# AGENTS - Module shared
**Socle commun, propriété transversale.** Toute modification nécessite une revue de plusieurs équipes.

- Ne pas renommer les six champs de l'enveloppe FP-LAB-1.1.
- Ne pas introduire Streamlit, YOLO ou GPIO dans ce module.
- Tests unitaires obligatoires pour un changement de validation ou de sérialisation.
- Conserver les données manquantes sous forme `None`/`null`.
- Les doublons exacts peuvent arriver en MQTT ; collision d'event_id contradictoire = erreur.
