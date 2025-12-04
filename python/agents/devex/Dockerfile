FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml ./
COPY src /app/src
RUN pip install --no-cache-dir -e .

# Install DevEx specific dependencies
RUN pip install --no-cache-dir \
    typer \
    rich \
    watchfiles \
    aiohttp \
    psutil \
    pytest \
    pytest-cov \
    pytest-json-report

# Copy agent code
COPY agents/devex /app/agents/devex
COPY agents/base_agent.py /app/agents/
COPY agents/__init__.py /app/agents/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV AGENT_ID=devex

CMD ["python", "-m", "agents.devex.agent"]
