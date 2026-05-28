"""Main application and routing logic for API"""

import uvicorn

from app.crisalid_taxi import CrisalidTaxi

# pylint: disable=invalid-name
app = CrisalidTaxi

if __name__ == "__main__":  # pragma: no cover
    uvicorn.run("app.crisalid_taxi:CrisalidTaxi", host="0.0.0.0", port=8000, workers=1)
