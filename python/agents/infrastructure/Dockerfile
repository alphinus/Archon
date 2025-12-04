FROM python:3.12-slim

WORKDIR /app

# Install Docker CLI (for image operations)
RUN apt-get update && \
    apt-get install -y docker.io && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY pyproject.toml ./
COPY src /app/src
RUN pip install --no-cache-dir -e .

# Install Infrastructure Agent specific dependencies
RUN pip install --no-cache-dir \
    pyyaml \
    docker

# Copy agent code
COPY agents/infrastructure /app/agents/infrastructure
COPY agents/base_agent.py /app/agents/
COPY agents/__init__.py /app/agents/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV AGENT_ID=infrastructure

CMD ["python", "-m", "agents.infrastructure.agent"]
