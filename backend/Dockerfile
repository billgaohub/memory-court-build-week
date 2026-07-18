FROM python:3.11-slim

WORKDIR /app
COPY backend /app/backend
COPY cases /app/cases
COPY replay /app/replay

RUN pip install --no-cache-dir /app/backend

ENV CASES_ROOT=/app/cases
ENV REPLAY_ROOT=/app/replay
ENV OPENAI_MODEL=gpt-5.6

CMD ["sh", "-c", "uvicorn memory_court.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
