"""Used by https://time-split.streamlit.app/."""

import datetime

import numpy as np
import pandas as pd
import streamlit as st

from time_split_app.widgets import DataLoaderWidget

NAME = "Composite wave"

class CustomLoader(DataLoaderWidget):
    def get_title(self) -> str:
        return "🎉 Use custom loader"

    def get_description(self) -> str:
        url = f"https://time-split.readthedocs.io/en/stable/generated/{__name__}.html"
        return f"""Click [here]({url}) to create your own."""

    def load(self, params: bytes | None) -> tuple[pd.DataFrame, dict[str, str], bytes]:
        if params:
            defaults, initial = self.decode_params(params)
        else:
            initial, defaults = None, ((10, 1), (10, 100))

        # Prompt user to get the date range.
        start, end = self.select_range(initial=initial, date_only=True)

        # Generate component waves.
        wave_params = []
        components_waves = []
        for i, (default_amplitude, default_frequency) in enumerate(defaults):
            with st.container(border=True):
                st.subheader(f"Wave {i + 1} configuration", divider=True)

                left, right = st.columns(2)
                amplitude = left.slider("Amplitude", -10, 10, default_amplitude, key=f"amplitude-{i}")
                frequency = right.slider("Frequency", 1, 100, default_frequency, key=f"frequency-{i}")
                wave = self._generate(amplitude, frequency, start, end)
                wave_params.append((amplitude, frequency))

            components_waves.append(wave)

        # Create the composite wave + set index (must be a DatetimeIndex).
        df = sum(components_waves).to_frame(NAME)
        df.index = self._date_range(start, end)

        # Default aggregations for the `📈 Aggregations per fold` view. Users may choose to override.
        aggregations = {
            NAME: "sum",
        }

        # Create permalink param bytes using repr().
        new_params = ((start.isoformat(), end.isoformat()), (*wave_params,))
        repro_params = repr(new_params).encode()

        return df, aggregations, repro_params

    @staticmethod
    def decode_params(params):
        """Process permalink `data` argument."""
        from ast import literal_eval

        string = params.decode()  # e.g. "(('2019-04-11', '2019-05-11'), ((10, 1), (10, 100)))"
        initial, defaults = literal_eval(string)  # Safer than `eval()`.
        initial = (datetime.date.fromisoformat(initial[0]), datetime.date.fromisoformat(initial[1]))
        return defaults, initial

    @classmethod
    @st.cache_data(max_entries=8)
    def _generate(cls, frequency: float, amplitude: float, start: datetime.date, end: datetime.date) -> pd.Series:
        n = len(cls._date_range(start, end))
        wave = amplitude * np.sin(frequency * np.linspace(0, 500, n))
        return pd.Series(wave)

    @classmethod
    @st.cache_resource(max_entries=4)
    def _date_range(cls, start: datetime.date, end: datetime.date) -> pd.DatetimeIndex:
        return pd.date_range(start, end, periods=1337)


def dummy_select_fn():
    st.subheader(f"Using `{dummy_select_fn.__name__}` to select params!", divider=True)
    days = st.slider("Selecty days", 1, 14, 7)
    return {"schedule": f"{days} days"}


def add_random_noise(**kwargs):
    from time_split import plot

    ax = plot(**kwargs)

    color, label = add_guide()

    available = kwargs["available"]
    if hasattr(available, "index"):
        seed = available.sum().sum()
        available = available.index
    else:
        seed = available.asi8.sum()

    seed = abs(int(seed)) + pd.Timestamp.now().dayofyear
    rng = np.random.default_rng(seed)

    r1 = rng.normal(0, 1, len(available))
    y1 = pd.Series(r1, index=available).abs().rolling("1d").mean()

    r2 = rng.normal(0, 1, len(available))
    y2 = pd.Series(r2, index=available).abs().rolling("1d").mean()

    twin = ax.twinx()
    twin.fill_between(
        available,
        y1 * 1000,
        y2 * 500,
        zorder=-10,
        facecolor=(color, 0.2),
        edgecolor=("#123456", 0.5),
        label=label,
    )

    twin.yaxis.tick_right()
    twin.grid(False)
    twin.legend(loc="lower right")
    ax.legend(loc="upper left")

    return ax


def add_guide():
    from time_split_app.config import PLOT_FN, DATASET_LOADER

    left, right = st.columns(2)

    label = "Random noise!"
    color = "green"
    title = f"This app uses a :primary[*custom plot function*] which adds the :{color}[*{label}*] region."
    with left.popover(title, icon="ℹ️", use_container_width=True):
        st.subheader("Customizing the `📊 Folds` plot.", divider=True)

        file = f"/home/streamlit/{__name__}.py"  # Cheat - streamlit.app doesn't use the Docker image.
        env = f"{PLOT_FN=}".replace("'", "")

        text = f"""
        Custom plots may be used by setting the `PLOT_FN` environment variable.
        The new plotting function should provide the same interface as the
        [original](https://time-split.readthedocs.io/en/stable/api/time_split.html#time_split.plot)
        `time_split.plot()` function.
        
        For this example, we've
        * mounted `{file}`, and
        * set `{env}`
        
        when launching the official Docker image {image}. {footer}
        """
        st.write(text)

    base = DataLoaderWidget
    title = f"This app uses a custom :primary[*{base.__name__}*] implementation."
    with right.popover(title, icon="ℹ️", use_container_width=True):
        st.subheader("Custom Data Loader widgets.", divider=True)

        env = f"{DATASET_LOADER=}".replace("'", "")

        text = f"""
        Custom loaders may be used by setting the `DATASET_LOADER` environment variable. The loader should implement the
        `{base.__qualname__}` API."""
        st.write(text)

        text = f"""
        For this example, we've
        * mounted `{file}`, and
        * set `{env}`
        
        when launching the official Docker image {image}. {footer}
        """
        st.write(text)

    return color, label


def dummy_link_fn(**kwargs):
    from time_split.app import create_explorer_link

    st.toast("Dummy link function!")
    return create_explorer_link(**kwargs)

image = "[![Docker Image Size (tag)](https://img.shields.io/docker/image-size/rsundqvist/time-split/latest?logo=docker&label=time-split)](https://hub.docker.com/r/rsundqvist/time-split/)"
footer = (
    "Set `EXTRA_PIP_PACKAGES` to install required packages in the container. "
    "Click [here](https://github.com/rsundqvist/time-split-app/blob/master/app_extensions.py)"
    " to see the `app_extensions.py` file."
)