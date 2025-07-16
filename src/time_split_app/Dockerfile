ARG PYTHON_BASE=3.13-slim

FROM python:$PYTHON_BASE AS build
RUN apt-get update && \
    apt-get install --no-install-recommends -y \
    curl tini=0.19.* \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip install time-split[app]

FROM python:$PYTHON_BASE AS app
COPY --from=build /usr/bin/tini /usr/bin/curl /usr/bin/
COPY --from=build $_VIRTUAL_ENV $_VIRTUAL_ENV

ENV HOME=/home/streamlit
RUN useradd --create-home --home-dir $HOME streamlit \
    && mkdir -p $HOME \
    && chown -R streamlit:streamlit $HOME

WORKDIR $HOME
USER streamlit

RUN printf """
#!/usr/bin/env bash
set -eux
app=$(python -m time_split app get-path)
exec streamlit run $app --server.address=0.0.0.0
""" > entrypoint.sh
RUN chmod +x entrypoint.sh

EXPOSE 8501
HEALTHCHECK --retries=5 --interval=10s  CMD [ "curl", "--fail", "http://localhost:8501/healthz" ]

# Naive entrypoint
ENTRYPOINT ["/usr/bin/tini", "-g", "--"]
CMD ["/home/streamlit/entrypoint.sh"]
