FROM python:3.12

WORKDIR /epg

COPY . .

RUN pip install -e . && SYNC_DATABASE_URL="sqlite:///epg/database/database.db" alembic upgrade head

EXPOSE 8080