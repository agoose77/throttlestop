from json import JSONEncoder
from types import SimpleNamespace

_NAMESPACE_KEY = '__types.SimpleNamespace'


class NamespaceEncoder(JSONEncoder):

    def default(self, o):
        if isinstance(o, SimpleNamespace):
            return {**vars(o), _NAMESPACE_KEY: True}
        # Let the base class default method raise the TypeError
        return JSONEncoder.default(self, o)


def namespace_object_hook(o):
    if _NAMESPACE_KEY in o:
        return SimpleNamespace(**o)
    return o
