"""Unit tests for the PayloadFormatter class."""

from app.services.loading.hierarchy import HierarchyResolver
from app.services.loading.formatter import PayloadFormatter


def test_payload_formatter():
    """Test payload formatter methods and payload builders."""
    domains = [
        {
            "id": "https://openalex.org/domains/1",
            "display_name": "Domain One",
            "description": "Desc D1",
        }
    ]
    fields = [
        {
            "id": "https://openalex.org/fields/11",
            "display_name": "Field Eleven",
            "description": "Desc F1.1",
            "domain": {"id": "https://openalex.org/domains/1"},
        }
    ]
    subfields = [
        {
            "id": "https://openalex.org/subfields/111",
            "display_name": "Subfield Triple One",
            "description": "Desc S1.1.1",
            "field": {"id": "https://openalex.org/fields/11"},
        }
    ]
    topics = [
        {
            "id": "https://openalex.org/topics/1111",
            "display_name": "Topic Quad One",
            "description": "Desc T1.1.1.1",
            "subfield": {"id": "https://openalex.org/subfields/111"},
            "keywords": ["tagA", "tagB"],
        }
    ]

    hierarchy = HierarchyResolver()
    hierarchy.build_lookups(domains, fields, subfields, topics)
    formatter = PayloadFormatter(hierarchy)

    # 1. API Payloads formatting
    domains_formatted = formatter.get_domains_formatted(domains)
    assert domains_formatted[0]["domain"]["name"] == "Domain One"
    assert domains_formatted[0]["description"] == "Desc D1"

    fields_formatted = formatter.get_fields_formatted(fields)
    assert fields_formatted[0]["field"]["name"] == "Field Eleven"
    assert fields_formatted[0]["domain"]["name"] == "Domain One"

    subfields_formatted = formatter.get_subfields_formatted(subfields)
    assert subfields_formatted[0]["subfield"]["name"] == "Subfield Triple One"
    assert subfields_formatted[0]["field"]["name"] == "Field Eleven"

    topics_formatted = formatter.get_topics_formatted(topics)
    assert topics_formatted[0]["topic"]["name"] == "Topic Quad One"
    assert topics_formatted[0]["subfield"]["name"] == "Subfield Triple One"
    assert topics_formatted[0]["keywords"] == ["tagA", "tagB"]

    # 2. Embedding text payload checks
    domains_embed = formatter.get_domains_embedding(domains)
    assert domains_embed[0] == "Domain One, Desc D1"

    fields_embed = formatter.get_fields_embedding(fields)
    assert fields_embed[0] == "Domain One, Field Eleven, Desc F1.1"

    subfields_embed = formatter.get_subfields_embedding(subfields)
    assert subfields_embed[0] == "Domain One, Field Eleven, Subfield Triple One, Desc S1.1.1"

    topics_embed = formatter.get_topics_embedding(topics)
    assert (
        topics_embed[0]
        == "Domain One, Field Eleven, Subfield Triple One, Topic Quad One, Desc T1.1.1.1, tagA, tagB"
    )

    # 3. Changed levels filtering
    changed_items = formatter.get_all_embedding_items(
        domains, fields, subfields, topics, changed_levels={"domains", "topics"}
    )
    # Only domains and topics should be returned
    assert len(changed_items) == 2
    types_returned = {item["type"] for item in changed_items}
    assert types_returned == {"domain", "topic"}
