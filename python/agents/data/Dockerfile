FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml ./
COPY src /app/src
RUN pip install --no-cache-dir -e .

# Install agent-specific dependencies
RUN pip install --no-cache-dir faker asyncpg aioredis

# Copy agent code
COPY agents/data /app/agents/data
COPY agents/base_agent.py /app/agents/
COPY agents/__init__.py /app/agents/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV AGENT_ID=data

CMD ["python", "-m", "agents.data.agent"]
