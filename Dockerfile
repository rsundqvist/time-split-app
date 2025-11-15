ARG PYTHON_BASE=3.14-slim
ARG _VIRTUAL_ENV=/opt/venv

FROM python:$PYTHON_BASE AS build
ARG _VIRTUAL_ENV

ENV PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

# Intall system dependencies
RUN apt-get update && \
    apt-get install --no-install-recommends -y \
    # Install build tools
    curl git build-essential \
    ssh \
    # Install entrypoint runner
    tini=0.19.* \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Poetry setup
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VERSION=2.2.1
RUN python -m venv $POETRY_HOME && \
    $POETRY_HOME/bin/pip install poetry==$POETRY_VERSION

# https://github.com/python-poetry/poetry/issues/6397#issuecomment-1236327500
# docker build . -t tmp && docker run --rm -it tmp /bin/bash

# Create project env
ENV VIRTUAL_ENV=$_VIRTUAL_ENV
RUN python -m venv $_VIRTUAL_ENV
# Install project dependencies (no root).
COPY README.md pyproject.toml poetry.lock ./
RUN $POETRY_HOME/bin/poetry install --only main --no-root --no-directory

# Install main project; can't use poetry since it will install as .pth to src/.
COPY src/ ./src
RUN $VIRTUAL_ENV/bin/python -m pip install . --no-deps

FROM python:$PYTHON_BASE AS app
ARG _VIRTUAL_ENV
ENV VIRTUAL_ENV=$_VIRTUAL_ENV
ENV PATH="$_VIRTUAL_ENV/bin:$PATH"

# Setup user so we can chown the venv, in case EXTRA_PIP_PACKAGES is set.
ENV HOME=/home/streamlit
RUN useradd --create-home --home-dir $HOME streamlit \
    && mkdir -p $HOME \
    && chown -R streamlit:streamlit $HOME

COPY --from=build /usr/bin/tini /usr/bin/curl /usr/bin/
COPY --from=build --chown=streamlit $_VIRTUAL_ENV $_VIRTUAL_ENV

WORKDIR $HOME
USER streamlit
COPY app.py healthcheck.py entrypoint.sh ./

# Entrypoint
EXPOSE 8501

HEALTHCHECK --retries=5 --interval=10s CMD python healthcheck.py

ENTRYPOINT ["/usr/bin/tini", "-g", "--"]
CMD ["/home/streamlit/entrypoint.sh"]
