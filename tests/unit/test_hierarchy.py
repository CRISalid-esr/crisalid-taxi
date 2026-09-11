"""Unit tests for the HierarchyResolver class."""

from app.services.loading.hierarchy import HierarchyResolver


def test_hierarchy_resolver_build_and_resolve():
    """Test lookup tables construction and resolution."""
    domains = [{"id": "https://openalex.org/domains/1", "display_name": "Domain One"}]
    fields = [
        {
            "id": "https://openalex.org/fields/11",
            "display_name": "Field Eleven",
            "domain": {"id": "https://openalex.org/domains/1"},
        }
    ]
    subfields = [
        {
            "id": "https://openalex.org/subfields/111",
            "display_name": "Subfield Triple One",
            "field": {"id": "https://openalex.org/fields/11"},
        }
    ]
    topics = [
        {
            "id": "https://openalex.org/topics/1111",
            "display_name": "Topic Quad One",
            "subfield": {"id": "https://openalex.org/subfields/111"},
            "keywords": ["tagA", "tagB"],
        }
    ]

    resolver = HierarchyResolver()
    resolver.build_lookups(domains, fields, subfields, topics)

    # O(1) lookups
    assert resolver.get_domain_by_uri("https://openalex.org/domains/1") == domains[0]
    assert resolver.get_field_by_uri("https://openalex.org/fields/11") == fields[0]
    assert resolver.get_subfield_by_uri("https://openalex.org/subfields/111") == subfields[0]
    assert resolver.get_topic_by_uri("https://openalex.org/topics/1111") == topics[0]

    # Parent relationship resolution
    assert resolver.get_domain_of_field("https://openalex.org/fields/11") == "Domain One"
    assert resolver.get_field_of_subfield("https://openalex.org/subfields/111") == "Field Eleven"
    assert resolver.get_domain_of_subfield("https://openalex.org/subfields/111") == "Domain One"

    # Hierarchy resolution dictionary
    subfield_hierarchy = resolver.resolve_subfield_hierarchy(subfields[0])
    assert subfield_hierarchy == {
        "domain_id": "https://openalex.org/domains/1",
        "domain_name": "Domain One",
        "field_id": "https://openalex.org/fields/11",
        "field_name": "Field Eleven",
    }

    topic_hierarchy = resolver.resolve_topic_hierarchy(topics[0])
    assert topic_hierarchy == {
        "domain_name": "Domain One",
        "field_name": "Field Eleven",
        "subfield_name": "Subfield Triple One",
    }

    # Keyword resolution
    assert resolver.get_keywords(topics[0]) == ["tagA", "tagB"]
