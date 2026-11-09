FROM python:3.13-slim

ENV PYTHONONTWRITEBYTECODE = 1 \
    PYTHONUNBUFFERED=1

WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY alembic.ini .
COPY migrations ./migrations
COPY app ./app
COPY scripts/start.sh ./start.sh

RUN useradd --create-home appuser
USER appuser

EXPOSE 8000
CMD ["sh", "./start.sh"]

