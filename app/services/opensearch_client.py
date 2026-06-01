"""OpenSearch client service."""
from opensearchpy import OpenSearch
from loguru import logger

from app.config import get_app_settings


class OpenSearchClient:
    """OpenSearch client wrapper."""

    def __init__(self):
        """Initialize OpenSearch client."""
        settings = get_app_settings()
        logger.debug(f"Connecting to OpenSearch at {settings.opensearch_scheme}://{settings.opensearch_host}:{settings.opensearch_port}")
        self.client = OpenSearch(
            hosts=[{
                "host": settings.opensearch_host,
                "port": settings.opensearch_port,
                "scheme": settings.opensearch_scheme,
            }],
            verify_certs=False,
            timeout=5
        )

    def ping(self) -> bool:
        """Test connection to OpenSearch."""
        try:
            result = self.client.ping()
            logger.debug(f"OpenSearch ping result: {result}")
            return result
        except Exception as e:
            logger.error(f"OpenSearch ping failed: {type(e).__name__}: {e}")
            return False

    def get_info(self) -> dict:
        """Get OpenSearch cluster info."""
        try:
            return self.client.info()
        except Exception as e:
            logger.error(f"Failed to get OpenSearch info: {e}")
            return {}


def get_opensearch_client() -> OpenSearchClient:
    """Get OpenSearch client (creates new instance each time)."""
    return OpenSearchClient()
