FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml ./
COPY src /app/src
RUN pip install --no-cache-dir -e .

# Copy agent code
COPY agents/documentation /app/agents/documentation
COPY agents/base_agent.py /app/agents/
COPY agents/__init__.py /app/agents/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV AGENT_ID=documentation

CMD ["python", "-m", "agents.documentation.agent"]
