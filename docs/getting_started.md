# 🚀 Getting Started & Docker

This guide explains how to get started quickly and run the `crisalid-taxi` API using Docker and Docker Compose.

---

## 📋 Prerequisites

To run the project via Docker, make sure you have installed:
*   **Docker** and **Docker Compose**
*   *Optional:* Python 3.11+ and `uv` (if you also want to develop locally)

---

## ⚡ Quick Start with Docker Compose

The project relies on a multi-container stack including the FastAPI API, OpenSearch (vector database), and OpenSearch Dashboards (web-based admin interface).

### 1. Environment Configuration

Copy the `.env.sample` configuration template to a `.env` file:

```bash
cp .env.sample .env
```

> ⚠️ **Important:** Modify the default variables if necessary, especially the OpenAlex data paths (`OPENALEX_DATA_HOST_PATH`) and the API key for your Embedding Provider.

### 2. Starting the Services

Start the entire stack in the background:

```bash
docker-compose up -d
```

This command will:
1.  Build the FastAPI API Docker image.
2.  Start the FastAPI API server (listening on port **8000**).
3.  Start an OpenSearch 2.11.0 instance (listening on port **9200**).
4.  Start OpenSearch Dashboards (accessible on port **5601**).

### 3. Verify Everything Is Running

Once started, you can validate that the services are responding properly.

#### Check the API readiness status
```bash
curl http://localhost:8000/readiness
```

#### Check OpenSearch health
```bash
curl http://localhost:9200/
```
*Expected response (example):*
```json
{
  "name": "opensearch-node",
  "cluster_name": "opensearch-cluster",
  "version": {
    "number": "2.11.0"
  }
}
```

#### Access Swagger/OpenAPI documentation
*   **Swagger UI:** http://localhost:8000/docs
*   **ReDoc:** http://localhost:8000/redoc

---

## 🛑 Stop the Services

To stop and remove all containers created by Docker Compose:

```bash
docker-compose down
```

> 💡 *Note:* To also remove the created volumes (if you wish to completely reset the OpenSearch index), you can add the `-v` flag: `docker-compose down -v`.
