ARG PYTHON_BASE=3.14-slim
ARG _VIRTUAL_ENV=/opt/venv

FROM python:$PYTHON_BASE AS build
ARG _VIRTUAL_ENV

COPY --from=ghcr.io/astral-sh/uv:0.13.5 /uv /bin/
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_CACHE=1 \
    UV_PYTHON_DOWNLOADS=0 \
    UV_PROJECT_ENVIRONMENT=$_VIRTUAL_ENV

# Install system dependencies
RUN apt-get update && \
    apt-get install --no-install-recommends -y \
    # Install build tools
    curl git build-essential \
    ssh \
    # Install entrypoint runner
    tini=0.19.* \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Create project env. Use venv (not uv) to keep pip, which the entrypoint needs for EXTRA_PIP_PACKAGES.
RUN python -m venv $_VIRTUAL_ENV
# Install project dependencies (no root). Inexact to keep pip.
COPY README.md LICENSE.md pyproject.toml uv.lock ./
RUN uv sync --locked --no-default-groups --inexact --no-install-project

# Install main project (non-editable, so the venv doesn't point back at src/).
COPY src/ ./src
RUN uv sync --locked --no-default-groups --inexact --no-editable

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
