#!make
PYTHON_EXEC ?= python3.12
NODE_VERSION ?= 20.15.1
VENV ?= "./.venv"
PNPM ?= pnpm@9.6.0
SHELL := /bin/bash

venv:
	[ -d $(VENV) ] || $(PYTHON_EXEC) -m venv $(VENV)
	source $(VENV)/bin/activate && pip install -U pip wheel setuptools
	source $(VENV)/bin/activate && pip install nodeenv
	source $(VENV)/bin/activate && nodeenv -p -n $(NODE_VERSION)
	source $(VENV)/bin/activate && npm install -g $(PNPM)
	source $(VENV)/bin/activate && pip install -e .
	source $(VENV)/bin/activate && SYNC_DATABASE_URL="sqlite:///epg/database/database.db" alembic upgrade head
