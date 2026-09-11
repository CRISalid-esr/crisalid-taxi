"""Unit tests for the OpenAlexLoader class."""

from app.services.loading.loader import OpenAlexLoader


def test_openalex_loader_load(temp_openalex_dir):
    """Test loading and processing of OpenAlex classification data."""
    loader = OpenAlexLoader(temp_openalex_dir)

    assert loader._loaded is False

    success = loader.load()
    assert success is True
    assert loader._loaded is True

    # Check that cache is populated
    assert len(loader.domains) == 1
    assert len(loader.fields) == 1
    assert len(loader.subfields) == 1
    assert len(loader.topics) == 1

    # Check stats summary
    summary = loader.get_summary()
    assert summary["domains"] == 1
    assert summary["fields"] == 1
    assert summary["subfields"] == 1
    assert summary["topics"] == 1
    assert summary["total"] == 4

    # Second load call should skip reading and return True immediately (cached)
    assert loader.load() is True
