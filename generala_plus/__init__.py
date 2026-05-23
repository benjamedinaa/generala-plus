__all__ = ["Generala"]


def __getattr__(name):
    if name == "Generala":
        from .pygame_app import Generala

        return Generala
    raise AttributeError(name)
