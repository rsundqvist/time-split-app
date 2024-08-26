FROM python:3.12-slim AS app

RUN apt-get update && \
    apt-get install --no-install-recommends -y \
    tini=0.19.* \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python -
RUN /root/.local/bin/poetry config virtualenvs.create false

# Install dependencies - these don't change as often.
COPY README.md pyproject.toml poetry.lock /tmp/time-fold-explorer/
RUN /root/.local/bin/poetry install \
    -C /tmp/time-fold-explorer/ --only=main \
    --no-root --no-interaction --no-cache --compile

# Install time-fold-explorer package
COPY src/ /tmp/time-fold-explorer/
RUN pip install /tmp/time-fold-explorer/ --no-deps --no-cache --no-cache-dir && rm -rf /tmp/time-fold-explorer/

ENV HOME /home/streamlit
RUN useradd --create-home --home-dir $HOME streamlit \
    && mkdir -p $HOME \
    && chown -R streamlit:streamlit $HOME

WORKDIR $HOME
USER streamlit
COPY app.py entrypoint.sh ./

# Entrypoint
EXPOSE 8501
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1
ENTRYPOINT ["/usr/bin/tini", "-g", "--", "/home/streamlit/entrypoint.sh"]
