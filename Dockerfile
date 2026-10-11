FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir .
COPY identa.toml domains.csv ./
CMD ["python", "-m", "identa", "run", "--config", "identa.toml", "--domains", "domains.csv"]
