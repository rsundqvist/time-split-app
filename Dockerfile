FROM python:3.12-slim AS build
COPY README.md pyproject.toml poetry.lock src/ ./
RUN pip install --no-cache --compile .

FROM python:3.12-slim AS app
RUN apt-get update && \
    apt-get install --no-install-recommends -y \
    tini=0.19.* \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY --from=build /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=build /usr/local/bin/streamlit /usr/local/bin/streamlit

ENV HOME=/home/streamlit
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
