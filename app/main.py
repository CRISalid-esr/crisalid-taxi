"""Main application and routing logic for API"""

import uvicorn

from app.taxi_search import TaxiSearch

# pylint: disable=invalid-name
app = TaxiSearch

if __name__ == "__main__":  # pragma: no cover
    uvicorn.run("app.taxi_search:TaxiSearch", host="0.0.0.0", port=8000, workers=1)
