"""Local compatibility shim for the globally installed FastAPI/Starlette pair."""

from __future__ import annotations

from starlette.routing import Router


_router_init = Router.__init__


def _netgenix_router_init(self, *args, **kwargs):
    kwargs.pop("on_startup", None)
    kwargs.pop("on_shutdown", None)
    result = _router_init(self, *args, **kwargs)
    self.on_startup = []
    self.on_shutdown = []
    return result


Router.__init__ = _netgenix_router_init
