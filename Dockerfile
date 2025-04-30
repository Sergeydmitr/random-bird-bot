FROM mirror.gcr.io/python-3.12-slim

# Set build variables
ARG WORKDIR=/app
ARG USERNAME=nonroot

# Set default working directory and permissions
WORKDIR $WORKDIR
RUN chown -R $USERNAME:$USERNAME $WORKDIR

# Install project
COPY --chown=$USERNAME:$USERNAME pyproject.toml poetry.lock* $WORKDIR/
RUN poetry install --only main --no-root

# Copy project files
COPY --chown=$USERNAME:$USERNAME ./src $WORKDIR/src/
COPY --chown=$USERNAME:$USERNAME .env.example $WORKDIR/

# Run project
CMD ["poetry", "run", "python", "-m", "src"]
