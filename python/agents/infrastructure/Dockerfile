FROM python:3.12-slim

WORKDIR /app

# Install Docker CLI (for image operations)
RUN apt-get update && \
    apt-get install -y docker.io && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install uv for dependency management
RUN pip install --no-cache-dir uv

# Install dependencies
COPY pyproject.toml uv.lock* ./
COPY src /app/src

# Install base package and agents group
RUN uv pip install --system --no-cache -e . --group agents

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
