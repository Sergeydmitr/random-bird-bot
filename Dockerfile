FROM mirror.gcr.io/python:3.12-slim

# Set build variables
ARG WORKDIR=/app

# Set default working directory and permissions
WORKDIR $WORKDIR
RUN chown -R $USERNAME:$USERNAME $WORKDIR

# Python
ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

# Poetry
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR='/var/cache/pypoetry' \
    POETRY_HOME='/usr/local' \
    POETRY_VERSION=1.8.3

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 -


# Install project
COPY --chown=$USERNAME:$USERNAME pyproject.toml poetry.lock* $WORKDIR/
RUN poetry install --only main --no-root

# Copy project files
COPY --chown=$USERNAME:$USERNAME ./src $WORKDIR/src/
COPY --chown=$USERNAME:$USERNAME .env.example $WORKDIR/

# Run project
CMD ["poetry", "run", "python", "-m", "src"]
