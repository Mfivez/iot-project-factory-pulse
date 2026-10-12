# AGENTS - Couche transport / intégration
MQTT sera introduit après validation des JSONL locaux.

- Ne pas placer de logique métier ni calcul d'alertes dans le transport.
- Topics prévus : `factorypulse/site1/m01/telemetry`,
  `factorypulse/site1/q01/inspection`, `factorypulse/site1/m01/health`.
- QoS 1 peut livrer un doublon : préserver l'event_id et dédupliquer en aval.
- Pas de credentials en dur, pas de topic de commande moteur pour l'agent.
- Documenter les modes offline/reprise quand cette couche sera développée.
