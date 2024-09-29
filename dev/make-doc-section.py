import abc
import sys

TEMPLATE = """
{title}
The {name} application
(available {public_link})
is designed to help evaluate the effects of different
{link_to_parameters}.
To start it locally using
{shield}
Docker, run
{run_command}
in the terminal. You may use
{create_explorer_link}
to build application URLs with preselected splitting parameters.
"""


def make(converter: "Converter") -> str:
    from time_split.support import create_explorer_link

    host = "https://time-split.streamlit.app/"
    limits = ("2019-04-11 00:35:00", "2019-05-11 21:30:00")
    public_link = create_explorer_link(host, limits, schedule="0 0 * * MON,FRI", n_splits=2, step=2)

    image = "rsundqvist/time-split"
    shield = converter.shield(
        shield=f"https://img.shields.io/docker/image-size/{image}/latest?logo=docker&label=time-split",
        url=f"https://hub.docker.com/r/{image}/",
        alt="Docker Image Size (tag)",
    )

    result = TEMPLATE.format(
        title=converter.title("Experimenting with parameters"),
        name=converter.bold("Time Fold Explorer"),
        public_link=converter.link("here", url=public_link),
        link_to_parameters=converter.parameters(),
        shield=shield,
        run_command=converter.command(f"docker run -p 8501:8501 {image}"),
        create_explorer_link=converter.create_explorer_link(),
    ).strip()

    return result + converter.make_tail()


class Converter(abc.ABC):
    @abc.abstractmethod
    def title(self, text: str) -> str: ...

    @abc.abstractmethod
    def bold(self, text: str) -> str: ...

    @abc.abstractmethod
    def link(self, text: str, url: str) -> str: ...

    @abc.abstractmethod
    def parameters(self) -> str: ...

    @abc.abstractmethod
    def shield(self, shield: str, url: str, alt: str) -> str: ...

    @abc.abstractmethod
    def command(self, text: str) -> str: ...

    @abc.abstractmethod
    def create_explorer_link(self) -> str: ...

    def make_tail(self) -> str:
        return ""


class Markdown(Converter):
    DOCS = "https://time-split.readthedocs.io/en/stable"

    def title(self, text: str) -> str:
        return f"## {text}"

    def bold(self, text: str) -> str:
        return f"**{text}**"

    def link(self, text: str, url: str) -> str:
        return f"[{text}]({url})"

    def parameters(self) -> str:
        return self.link("parameters", f"{self.DOCS}/#parameter-overview")

    def shield(self, shield: str, url: str, alt: str) -> str:
        inner = self.link(alt, shield)
        outer = self.link("!" + inner, url)
        return outer

    def command(self, text: str) -> str:
        return f"```sh\n{text}\n```"

    def create_explorer_link(self) -> str:
        path = "generated/time_split.support.html#time_split.support.create_explorer_link"
        return self.link("`create_explorer_link()`", f"{self.DOCS}/{path}")


class Rst(Converter):
    def __init__(self) -> None:
        self._shields: dict[str, tuple[str, str, str]] = {}

    def title(self, text: str) -> str:
        return f"{text}\n{'-' * len(text)}"

    def bold(self, text: str) -> str:
        return f"**{text}**"

    def link(self, text: str, url: str) -> str:
        return f"`{text} <{url}>`_"

    def parameters(self) -> str:
        return ":ref:`parameters <Parameter overview>`"

    def shield(self, shield: str, url: str, alt: str) -> str:
        key = f"shield-{len(self._shields)}"
        self._shields[key] = (shield, url, alt)
        return f"|{key}|"

    def command(self, text: str) -> str:
        return f"\n.. code-block::\n\n    {text}\n"

    def create_explorer_link(self) -> str:
        return ":func:`~time_split.support.create_explorer_link`"

    def make_tail(self) -> str:
        template = """
.. |{key}| image:: {shield}
                  :target: {url}
                  :alt: {alt}
"""

        rows = ["\n"]
        for key, (shield, url, alt) in self._shields.items():
            rows.append(template.format(key=key, shield=shield, url=url, alt=alt))

        return "\n".join(rows)


if __name__ == "__main__":
    assert len(sys.argv) == 2
    result = make(Markdown() if sys.argv[1].lower().startswith("m") else Rst())
    print(result)
