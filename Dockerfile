FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir .
COPY identa.railway.toml domains.csv ./
COPY evidence ./evidence
COPY scripts/railway_entry.sh ./scripts/railway_entry.sh
CMD ["sh", "scripts/railway_entry.sh"]
