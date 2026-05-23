from .version import VERSION

__all__ = ["Generala", "VERSION"]


def __getattr__(name):
    if name == "Generala":
        from .pygame_app import Generala

        return Generala
    raise AttributeError(name)
