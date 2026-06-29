"""OpenAlex payload builders."""

from app.utils.openalex.loading import build_embedding_text


def build_named_entity(entity_id: str, entity_name: str) -> dict[str, str]:
    """Build a standard id/name payload for a hierarchy node."""
    return {
        "id": entity_id,
        "name": entity_name,
    }


def build_domain_payload(domain: dict) -> dict:
    """Build the formatted domain payload."""
    return {
        "domain": build_named_entity(
            domain.get("id", ""),
            domain.get("display_name", "?"),
        ),
        "description": domain.get("description", ""),
    }


def build_field_payload(field: dict, domain_uri: str, domain_name: str) -> dict:
    """Build the formatted field payload."""
    return {
        "domain": build_named_entity(domain_uri, domain_name),
        "field": build_named_entity(
            field.get("id", ""),
            field.get("display_name", "?"),
        ),
        "description": field.get("description", ""),
    }


def build_subfield_payload(subfield: dict, hierarchy: dict[str, str]) -> dict:
    """Build the formatted subfield payload."""
    return {
        "domain": build_named_entity(hierarchy["domain_id"], hierarchy["domain_name"]),
        "field": build_named_entity(hierarchy["field_id"], hierarchy["field_name"]),
        "subfield": build_named_entity(
            subfield.get("id", ""),
            subfield.get("display_name", "?"),
        ),
        "description": subfield.get("description", ""),
    }


def build_topic_payload(  # pylint: disable=too-many-positional-arguments
    topic: dict,
    hierarchy: dict[str, str],
    subfield_uri: str,
    field_uri: str,
    domain_uri: str,
    keywords: list[str],
) -> dict:
    """Build the formatted topic payload."""
    return {
        "domain": build_named_entity(domain_uri, hierarchy["domain_name"]),
        "field": build_named_entity(field_uri, hierarchy["field_name"]),
        "subfield": build_named_entity(subfield_uri, hierarchy["subfield_name"]),
        "topic": build_named_entity(
            topic.get("id", ""),
            topic.get("display_name", "?"),
        ),
        "description": topic.get("description", ""),
        "keywords": keywords,
    }


def build_domain_embedding(domain: dict) -> str:
    """Build the domain embedding payload."""
    return build_embedding_text(
        [
            domain.get("display_name", "?"),
            domain.get("description", ""),
        ]
    )


def build_field_embedding(field: dict, domain_name: str) -> str:
    """Build the field embedding payload."""
    return build_embedding_text(
        [
            domain_name,
            field.get("display_name", "?"),
            field.get("description", ""),
        ]
    )


def build_subfield_embedding(subfield: dict, hierarchy: dict[str, str]) -> str:
    """Build the subfield embedding payload."""
    return build_embedding_text(
        [
            hierarchy["domain_name"],
            hierarchy["field_name"],
            subfield.get("display_name", "?"),
            subfield.get("description", ""),
        ]
    )


def build_topic_embedding(topic: dict, hierarchy: dict[str, str], keywords: list[str]) -> str:
    """Build the topic embedding payload."""
    return build_embedding_text(
        [
            hierarchy["domain_name"],
            hierarchy["field_name"],
            hierarchy["subfield_name"],
            topic.get("display_name", "?"),
            topic.get("description", ""),
        ],
        keywords=keywords,
    )
