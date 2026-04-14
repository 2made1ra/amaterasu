# Use a lightweight Python base image
FROM python:3.12-slim-bookworm

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set the working directory
WORKDIR /app

# Copy the project files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
# --frozen ensures the lockfile is used without modification
# --no-install-project skips installing the project itself as a package (optional)
RUN uv sync --frozen --no-install-project

# Copy the rest of the application
COPY app ./app

# Expose the application port
EXPOSE 8000

# Run the application using uv run to ensure the environment is correctly loaded
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
