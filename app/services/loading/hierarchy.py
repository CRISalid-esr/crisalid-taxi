"""Hierarchy resolution for OpenAlexLoader."""

from loguru import logger
from app.utils.openalex.loading import (
    build_id_lookup,
    build_name_lookup,
    build_parent_lookup,
)


class HierarchyResolver:
    """Provides methods for resolving OpenAlex entity hierarchies and names."""

    def __init__(self):
        self.domain_names: dict[str, str] = {}
        self.field_names: dict[str, str] = {}
        self.subfield_names: dict[str, str] = {}

        self._domains_by_id: dict[str, dict] = {}
        self._fields_by_id: dict[str, dict] = {}
        self._subfields_by_id: dict[str, dict] = {}
        self._topics_by_id: dict[str, dict] = {}

        self.field_to_domain: dict[str, str] = {}
        self.subfield_to_field: dict[str, str] = {}

    def build_lookups(
        self,
        domains: list[dict],
        fields: list[dict],
        subfields: list[dict],
        topics: list[dict],
    ) -> None:
        """Build entity lookup tables after raw records are loaded."""
        logger.info("Étape 2/4 : Construction des relations entre les concepts (hiérarchies)...")
        self.domain_names = build_name_lookup(domains)
        self.field_names = build_name_lookup(fields)
        self.subfield_names = build_name_lookup(subfields)

        self._domains_by_id = build_id_lookup(domains)
        self._fields_by_id = build_id_lookup(fields)
        self._subfields_by_id = build_id_lookup(subfields)
        self._topics_by_id = build_id_lookup(topics)

        self.field_to_domain = build_parent_lookup(fields, "domain")
        self.subfield_to_field = build_parent_lookup(subfields, "field")
        logger.info("Étape 2/4 : Construction terminée avec succès.")

    def get_domain_by_uri(self, uri: str) -> dict | None:
        """Get domain record by URI. O(1) lookup."""
        return self._domains_by_id.get(uri)

    def get_field_by_uri(self, uri: str) -> dict | None:
        """Get field record by URI. O(1) lookup."""
        return self._fields_by_id.get(uri)

    def get_subfield_by_uri(self, uri: str) -> dict | None:
        """Get subfield record by URI. O(1) lookup."""
        return self._subfields_by_id.get(uri)

    def get_topic_by_uri(self, uri: str) -> dict | None:
        """Get topic record by URI. O(1) lookup."""
        return self._topics_by_id.get(uri)

    def get_domain_of_field(self, field_uri: str) -> str:
        """Resolve domain name for a field URI."""
        parent_uri = self.field_to_domain.get(field_uri, "")
        return self.domain_names.get(parent_uri, "?")

    def get_field_of_subfield(self, subfield_uri: str) -> str:
        """Resolve field name for a subfield URI."""
        parent_uri = self.subfield_to_field.get(subfield_uri, "")
        return self.field_names.get(parent_uri, "?")

    def get_domain_of_subfield(self, subfield_uri: str) -> str:
        """Resolve domain name for a subfield URI."""
        field_uri = self.subfield_to_field.get(subfield_uri, "")
        return self.get_domain_of_field(field_uri)

    def resolve_topic_hierarchy(self, topic: dict) -> dict:
        """Extract and resolve hierarchy for a topic."""
        sf_uri = (topic.get("subfield") or {}).get("id", "")
        field_uri = self.subfield_to_field.get(sf_uri, "")
        subfield_name = self.subfield_names.get(sf_uri, "?")
        field_name = self.field_names.get(field_uri, "?")
        domain_name = self.get_domain_of_field(field_uri)
        return {
            "domain_name": domain_name,
            "field_name": field_name,
            "subfield_name": subfield_name,
        }

    def resolve_subfield_hierarchy(self, subfield: dict) -> dict:
        """Extract and resolve hierarchy for a subfield."""
        field_uri = (subfield.get("field") or {}).get("id", "")
        return {
            "domain_id": self.field_to_domain.get(field_uri, ""),
            "domain_name": self.get_domain_of_field(field_uri),
            "field_id": field_uri,
            "field_name": self.field_names.get(field_uri, "?"),
        }

    @staticmethod
    def get_keywords(record: dict) -> list[str]:
        """Extract keywords from record."""
        kws = record.get("keywords", [])
        if not kws:
            return []
        if isinstance(kws[0], dict):
            return [kw.get("display_name", str(kw)) for kw in kws]
        return [str(k) for k in kws]
