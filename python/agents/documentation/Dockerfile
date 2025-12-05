FROM python:3.12-slim

WORKDIR /app

# Install uv for dependency management
RUN pip install --no-cache-dir uv

# Install dependencies
COPY pyproject.toml uv.lock* ./
COPY src /app/src

# Install base package and agents group
RUN uv pip install --system --no-cache -e . --group agents

# Copy agent code
COPY agents/documentation /app/agents/documentation
COPY agents/base_agent.py /app/agents/
COPY agents/__init__.py /app/agents/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV AGENT_ID=documentation

CMD ["python", "-m", "agents.documentation.agent"]
