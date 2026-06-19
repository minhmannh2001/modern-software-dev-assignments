from mcp.server.fastmcp import FastMCP

from .auth import BearerTokenMiddleware, make_auth_router, make_metadata_router
from .config import Config
from .tools.weather import get_current_weather, get_forecast, get_weather_by_city


def create_app(config=None):
    if config is None:
        config = Config()

    mcp = FastMCP("Weather Server")
    mcp.tool()(get_current_weather)
    mcp.tool()(get_forecast)
    mcp.tool()(get_weather_by_city)

    # FastMCP's Starlette app exposes /mcp
    app = mcp.streamable_http_app()

    # Prepend OAuth routes so they match before /mcp
    metadata_routes = make_metadata_router(config)
    oauth_routes = make_auth_router(config)
    app.router.routes = metadata_routes + oauth_routes + list(app.router.routes)

    app.add_middleware(BearerTokenMiddleware, server_url=config.server_url)

    return app


class _LazyApp:
    """Defers Config() until first request so the module is importable without env vars."""
    def __init__(self):
        self._app = None

    async def __call__(self, scope, receive, send):
        if self._app is None:
            self._app = create_app()
        await self._app(scope, receive, send)


app = _LazyApp()
