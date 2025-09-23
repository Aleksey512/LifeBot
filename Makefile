all: install lint check test

install:
	uv sync

run:
	cd src && uv run main.py

lint:
	uv run ruff check ./src --fix

check:
	uv run mypy ./src 

test:
	uv run pytest -vv
