# Time Split App
This is a naive template for building and running the [time-split](https://time-split.readthedocs.io/) application as a
Docker container. See the [extensions file](my_extensions.py) for customizations.

To start the app for development, use the [dev script](start-dev.sh):

```bash
./start-dev.sh
```

## Configuration
Run
```bash
python -m time_split app print-config
```
to show config options. Options are specified using environment variables.

# Docker
To build and start the application using Docker, run:
```bash
image=custom-time-split-app
docker build -t $image .
docker run --rm --name=dev/time-split -p 8501:8501 $image
```
in the terminal. See the [Dockerfile](Dockerfile) for details.

# Resources
* See the [extensions module](https://github.com/rsundqvist/time-split-app/blob/master/app_extensions.py) of the public
  app (https://time-split.streamlit.app) for advanced examples.
* Visit https://github.com/rsundqvist/time-split-app/ for source code.
* Visit the [application API docs](https://time-split.readthedocs.io/en/latest/api/time_split.app.reexport.html) for
  documentation of key functions and classes that are used in the [my_extensions.py](my_extensions.py) file.
