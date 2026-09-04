# 🚖 crisalid-taxi

FastAPI microservice for managing the OpenAlex taxonomy. A minimal and extensible API that performs fast in-memory semantic classification using vector embeddings and OpenSearch.

---

## 🗺️ Modular Documentation (Navigation Tree)

For more information about installation, development, usage, or internal mechanics, please refer to the following documentation sections:

*   📁 **[docs/](docs/)**
    *   🚀 **[getting_started.md](docs/getting_started.md)**: Quick Start & Docker (Docker Compose, initial validation tests).
    *   ⚙️ **[configuration.md](docs/configuration.md)**: Environment variables, secrets, and `.env` file configuration options.
    *   🔄 **[pipeline.md](docs/pipeline.md)**: OpenAlex taxonomy loading, caching, and incremental change detection (`StateTracker`).
    *   🔌 **[api.md](docs/api.md)**: API endpoints reference (`/liveness`, `/readiness`, `POST /match`) and real JSON payload examples.
    *   🛠️ **[development.md](docs/development.md)**: Local development guide (virtual environment with `uv`, tests with `pytest`, and code quality tools).

*Click on any of the files above to access its documentation page.*

---

## 📋 Prerequisites in brief

*   **Docker & Docker Compose** (to run the entire service stack)
*   **Python 3.11+** & **uv** (only for local development outside containers)

---

## ⚡ Quick Start (Docker)

1.  **Configure the environment:**
    ```bash
    cp .env.sample .env
    ```
2.  **Start the entire stack (FastAPI, OpenSearch, Dashboards):**
    ```bash
    docker compose up -d
    ```
3.  **Test if the API is ready:**
    ```bash
    curl http://localhost:8000/readiness
    ```

For full deployment instructions, see the [Quick Start & Docker](docs/getting_started.md) guide.

---

## 🔒 Security

*   **Secrets**: All secrets are managed exclusively through environment variables.
*   **Environment Files**: `.env.local` and `.env` are ignored by Git.
*   **Configuration**: Use `.env.sample` as a template and never commit real secrets.