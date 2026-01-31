FROM python:3.13-slim

WORKDIR /app

RUN pip install uv

COPY pyproject.toml ./

COPY alembic.ini ./

RUN uv venv

RUN uv sync

COPY ./src ./src

CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
