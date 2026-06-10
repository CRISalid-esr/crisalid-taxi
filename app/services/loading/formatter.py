"""Payload formatting for OpenAlexLoader."""

from loguru import logger
from app.services.loading.hierarchy import HierarchyResolver
from app.utils.openalex.payloads import (
    build_domain_embedding,
    build_domain_payload,
    build_field_embedding,
    build_field_payload,
    build_subfield_embedding,
    build_subfield_payload,
    build_topic_embedding,
    build_topic_payload,
)


class PayloadFormatter:
    """Provides methods for formatting OpenAlex entities into API or embedding payloads."""

    def __init__(self, hierarchy: HierarchyResolver):
        self._hierarchy = hierarchy

    # ========================================================================
    # FORMATTED OUTPUT METHODS - Returns hierarchical dict payloads
    # ========================================================================

    def get_domains_formatted(self, domains: list[dict]) -> list[dict]:
        """Get domains formatted as dict payloads."""
        return [build_domain_payload(domain) for domain in domains]

    def get_fields_formatted(self, fields: list[dict]) -> list[dict]:
        """Get fields formatted as dict payloads."""
        return [
            build_field_payload(
                field,
                (field.get("domain") or {}).get("id", ""),
                self._hierarchy.domain_names.get((field.get("domain") or {}).get("id", ""), "?"),
            )
            for field in fields
        ]

    def get_subfields_formatted(self, subfields: list[dict]) -> list[dict]:
        """Get subfields formatted as dict payloads."""
        return [
            build_subfield_payload(subfield, self._hierarchy.resolve_subfield_hierarchy(subfield))
            for subfield in subfields
        ]

    def get_topics_formatted(self, topics: list[dict]) -> list[dict]:
        """Get topics formatted as dict payloads."""
        result = []
        for topic in topics:
            hierarchy = self._hierarchy.resolve_topic_hierarchy(topic)
            subfield_uri = (topic.get("subfield") or {}).get("id", "")
            field_uri = self._hierarchy.subfield_to_field.get(subfield_uri, "")
            domain_uri = self._hierarchy.field_to_domain.get(field_uri, "")
            result.append(
                build_topic_payload(
                    topic,
                    hierarchy,
                    subfield_uri,
                    field_uri,
                    domain_uri,
                    self._hierarchy.get_keywords(topic),
                )
            )
        return result

    # ========================================================================
    # EMBEDDING OUTPUT METHODS - Returns flat payloads for embedding input
    # ========================================================================

    def get_domains_embedding(self, domains: list[dict]) -> list[str]:
        """Get domains as concatenated text payloads for embedding."""
        return [build_domain_embedding(domain) for domain in domains]

    def get_fields_embedding(self, fields: list[dict]) -> list[str]:
        """Get fields as concatenated text payloads for embedding."""
        return [
            build_field_embedding(
                field,
                self._hierarchy.domain_names.get((field.get("domain") or {}).get("id", ""), "?"),
            )
            for field in fields
        ]

    def get_subfields_embedding(self, subfields: list[dict]) -> list[str]:
        """Get subfields as concatenated text payloads for embedding."""
        return [
            build_subfield_embedding(subfield, self._hierarchy.resolve_subfield_hierarchy(subfield))
            for subfield in subfields
        ]

    def get_topics_embedding(self, topics: list[dict]) -> list[str]:
        """Get topics as concatenated text payloads for embedding."""
        return [
            build_topic_embedding(
                topic,
                self._hierarchy.resolve_topic_hierarchy(topic),
                self._hierarchy.get_keywords(topic),
            )
            for topic in topics
        ]

    # ========================================================================
    # EMBEDDING PREPARATION
    # ========================================================================

    def get_all_embedding_items(
        self,
        domains: list[dict],
        fields: list[dict],
        subfields: list[dict],
        topics: list[dict],
        changed_levels: set[str],
    ) -> list[dict]:
        """Format all loaded entities into embedding payloads.

        Only returns items for levels whose underlying data files have changed.
        """
        items = []

        if "domains" in changed_levels:
            for d in domains:
                items.append(
                    {
                        "id": d["id"],
                        "display_name": d.get("display_name", ""),
                        "text": build_domain_embedding(d),
                        "type": "domain",
                    }
                )

        if "fields" in changed_levels:
            for f in fields:
                d_id = self._hierarchy.field_to_domain.get(f["id"], "")
                items.append(
                    {
                        "id": f["id"],
                        "display_name": f.get("display_name", ""),
                        "text": build_field_embedding(
                            f,
                            domain_name=self._hierarchy.domain_names.get(d_id, "?"),
                        ),
                        "type": "field",
                    }
                )

        if "subfields" in changed_levels:
            for s in subfields:
                items.append(
                    {
                        "id": s["id"],
                        "display_name": s.get("display_name", ""),
                        "text": build_subfield_embedding(
                            s,
                            hierarchy=self._hierarchy.resolve_subfield_hierarchy(s),
                        ),
                        "type": "subfield",
                    }
                )

        if "topics" in changed_levels:
            for t in topics:
                items.append(
                    {
                        "id": t["id"],
                        "display_name": t.get("display_name", ""),
                        "text": build_topic_embedding(
                            t,
                            hierarchy=self._hierarchy.resolve_topic_hierarchy(t),
                            keywords=t.get("keywords", []),
                        ),
                        "type": "topic",
                    }
                )

        logger.info(
            f"Étape 3/4 : Préparation de {len(items)} concepts ayant été modifiés récemment..."
        )
        return items
