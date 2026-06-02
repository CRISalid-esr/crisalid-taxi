"""Test OpenAlexLoader service - Display embedding texts."""

from app.services.openalex_loader import get_openalex_loader
import os


def test_openalex_hierarchy_display():
    """Display OpenAlex embedding texts."""
    
    # Get path from env var
    data_path = os.getenv("OPENALEX_DATA_PATH")
    loader = get_openalex_loader(data_path)
    
    print("\n" + "=" * 120)
    print("🌐 DOMAINS EMBEDDING TEXT")
    print("=" * 120)
    domains = loader.get_domains_embedding()
    print("\n".join(domains[:2]))
    
    print("\n" + "=" * 120)
    print("📂 FIELDS EMBEDDING TEXT")
    print("=" * 120)
    fields = loader.get_fields_embedding()
    print("\n".join(fields[:2]))
    
    print("\n" + "=" * 120)
    print("📁 SUBFIELDS EMBEDDING TEXT")
    print("=" * 120)
    subfields = loader.get_subfields_embedding()
    print("\n".join(subfields[:2]))
    
    print("\n" + "=" * 120)
    print("📄 TOPICS EMBEDDING TEXT")
    print("=" * 120)
    topics = loader.get_topics_embedding()
    print("\n".join(topics[:2]))

    assert all(isinstance(item, str) and item for item in domains[:2])
    assert all(isinstance(item, str) and item for item in fields[:2])
    assert all(isinstance(item, str) and item for item in subfields[:2])
    assert all(isinstance(item, str) and item for item in topics[:2])
    
    print("\n" + "=" * 120)
    print("✅ Test OpenAlexLoader réussi")
    summary = loader.get_summary()
    print(f"📊 Summary: {summary['domains']} domains | {summary['fields']} fields | {summary['subfields']} subfields | {summary['topics']} topics")
    print("=" * 120 + "\n")


if __name__ == "__main__":
    test_openalex_hierarchy_display()
