# Time Split App
This is a naive template for building and running the [time-split](https://time-split.readthedocs.io/) application as a
Docker container. See the [extensions file](my_extensions.py) for customizations.

To build and start the application, run:
```bash
image=custom-time-split-app
docker build -t $image .
docker run --rm --name=time-split -p 8501:8501 $image
```
in the terminal.

# Resources
* See the [extensions module](https://github.com/rsundqvist/time-split-app/blob/master/app_extensions.py) of the public
  app (https://time-split.streamlit.app) for advanced examples.
* Visit https://github.com/rsundqvist/time-split-app/ for source code.
