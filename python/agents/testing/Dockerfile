FROM python:3.12-slim

WORKDIR /app

# Install uv for dependency management
RUN pip install --no-cache-dir uv

# Install dependencies
COPY pyproject.toml uv.lock* ./
COPY src /app/src

# Install base package and agents group (includes structlog, redis, etc.)
RUN uv pip install --system --no-cache -e . --group agents

# Install Testing Agent specific dependencies
RUN pip install --no-cache-dir \
    pytest \
    pytest-cov \
    pytest-xdist \
    pytest-rerunfailures \
    pytest-json-report \
    psutil

# Copy agent code
COPY agents/testing /app/agents/testing
COPY agents/base_agent.py /app/agents/
COPY agents/__init__.py /app/agents/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV AGENT_ID=testing

CMD ["python", "-m", "agents.testing.agent"]
