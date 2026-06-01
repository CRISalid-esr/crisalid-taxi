FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt && \
    pip install --no-cache-dir pytest==7.4.3 pytest-asyncio==0.21.1 pytest-cov==4.1.0

COPY ./app /code/app
COPY ./tests /code/tests

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
