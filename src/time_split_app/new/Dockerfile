ARG PYTHON_BASE=3.13-slim

FROM python:$PYTHON_BASE AS build
RUN apt-get update && \
    apt-get install --no-install-recommends -y \
    curl tini=0.19.* \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip install time-split[app]

# Your dependencies go here. We install s3fs as an example.
RUN pip install s3fs==2025.5.1

FROM python:$PYTHON_BASE AS app

COPY --from=build /usr/bin/tini /usr/bin/curl /usr/bin/
COPY --from=build /usr/local/bin/streamlit /usr/local/bin/
COPY --from=build /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/

ENV HOME=/home/streamlit
RUN useradd --create-home --home-dir $HOME streamlit \
    && mkdir -p $HOME \
    && chown -R streamlit:streamlit $HOME

WORKDIR $HOME
USER streamlit

COPY --chown=streamlit entrypoint.sh my_extensions.py ./

ENV DATASET_LOADER=my_extensions:MyDatasetLoader
ENV SPLIT_SELECT_FN=my_extensions:my_select_fn
ENV PLOT_FN=my_extensions:my_plot_fn
ENV LINK_FN=my_extensions:my_link_fn

# Copy app.py, i.e. the Streamlit entrypoint script.
RUN cp $(python -m time_split app get-path) .

# Naive entrypoint
ENTRYPOINT ["/usr/bin/tini", "-g", "--"]
CMD ["/home/streamlit/entrypoint.sh"]
