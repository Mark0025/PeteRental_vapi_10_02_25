# Use Playwright's official image with all browser dependencies pre-installed
FROM mcr.microsoft.com/playwright:v1.54.0-noble

# Install Python and dependencies (Playwright image is Ubuntu-based)
RUN apt-get update && apt-get install -y \
    python3.12 \
    python3.12-venv \
    python3.12-dev \
    python3-pip \
    python3-full \
    pipx \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set up Python 3.12 as default and install uv
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1
# Install uv using pipx (proper way)
RUN pipx install uv
RUN pipx ensurepath
# Add pipx binaries to PATH
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

# Copy requirements and install dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

# Copy application code
COPY . .

# Create non-root user and switch  
RUN useradd -m appuser && chown -R appuser:appuser /app
# Make .venv accessible to appuser
RUN chown -R appuser:appuser /app/.venv
USER appuser

# Browsers are already installed in base image, just need to make accessible to appuser
# This ensures our app can access the pre-installed browsers

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
