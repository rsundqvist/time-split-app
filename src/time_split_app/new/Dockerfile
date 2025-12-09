ARG PYTHON_BASE=3.14-slim

FROM python:$PYTHON_BASE AS build
RUN apt-get update && \
    apt-get install --no-install-recommends -y \
    curl tini=0.19.* \
    git \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# RUN pip install time-split[app]

# TODO remove this - git above
RUN pip install git+https://github.com/rsundqvist/time-split@master
RUN pip install git+https://github.com/rsundqvist/time-split-app.git@feature/custom-splitter-kwargs

# Your dependencies go here. We install s3fs as an example.
RUN pip install s3fs==2025.12.0

FROM python:$PYTHON_BASE AS app

COPY --from=build /usr/bin/tini /usr/bin/curl /usr/bin/
COPY --from=build /usr/local/bin/streamlit /usr/local/bin/
COPY --from=build /usr/local/lib/python3.14/site-packages/ /usr/local/lib/python3.14/site-packages/

ENV HOME=/home/streamlit
RUN useradd --create-home --home-dir $HOME streamlit \
    && mkdir -p $HOME \
    && chown -R streamlit:streamlit $HOME

WORKDIR $HOME
USER streamlit
RUN mkdir "$HOME/extensions"

COPY --chown=streamlit time_split_app/new/entrypoint.sh extensions.env ./
COPY --chown=streamlit time_split_app/new/extensions ./extensions/
COPY --chown=streamlit time_split_app/new/datasets ./datasets/

# Copy the Streamlit entrypoint script.
RUN cp $(python -m time_split app get-path) .

# Naive entrypoint
ENTRYPOINT ["/usr/bin/tini", "-g", "--"]
CMD ["/home/streamlit/entrypoint.sh"]
