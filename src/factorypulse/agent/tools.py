"""Signatures contractuelles du futur agent ; aucune commande machine."""

def get_status(station_id: str, at_utc: str) -> dict:
    """TODO : état machine et signe de vie distincts, horloge de replay."""
    raise NotImplementedError("Equipe intégration : implémenter lecture seule, voir docs/AGENT_TOOLS.md")


def get_history(station_id: str, from_utc: str, to_utc: str) -> dict:
    """TODO : télémétries inclusives, max 500 événements."""
    raise NotImplementedError("Equipe intégration : implémenter lecture seule")


def get_logs(station_id: str, from_utc: str, to_utc: str) -> dict:
    """TODO : logs de station + logs SERVER cibles, max 100."""
    raise NotImplementedError("Equipe intégration : implémenter lecture seule")


def get_inspections(from_utc: str, to_utc: str) -> dict:
    """TODO : inspections Q01 dédupliquées, max 100."""
    raise NotImplementedError("Equipe intégration : implémenter lecture seule")
