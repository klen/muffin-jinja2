"""Muffin-Jinja2 -- Jinja2 template engine for Muffin framework."""

from __future__ import annotations

from inspect import isawaitable
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    ClassVar,
    Literal,
    Mapping,
    TypeVar,
    cast,
    overload,
)
from warnings import warn

import jinja2
import jinja2.filters
from muffin.plugins import BasePlugin, PluginNotInstalledError

if TYPE_CHECKING:
    from pathlib import Path

    from muffin import Application

TVFn = TypeVar("TVFn", bound=Callable[..., Any])
TEnvParams = Literal["globals", "filters"]
TContext = Mapping[str, Any]
TContextProvider = Callable[[], TContext | Awaitable[TContext]]
TReceiver = Callable[[str | jinja2.Template, dict[str, Any]], Any]


class Plugin(BasePlugin):
    """The class is used to control the jinja2 integration to Muffin application."""

    name: str = "jinja2"
    defaults: ClassVar[Mapping[str, Any]] = {
        "auto_reload": False,
        "cache_size": 400,
        "extensions": (),
        "loader": None,
        "encoding": "utf-8",
        "template_folders": ["templates"],
    }

    Error: ClassVar[type[jinja2.TemplateError]] = jinja2.TemplateError

    def __init__(self, app: Application | None = None, **options: Any) -> None:
        """Initialize the plugin."""
        self.__env__: jinja2.Environment | None = None
        self.ctx_providers: list[TContextProvider] = []
        self.receivers: list[TReceiver] = []

        super().__init__(app, **options)

    @property
    def env(self) -> jinja2.Environment:
        env = self.__env__
        if env is None:
            raise PluginNotInstalledError
        return env

    @property
    def loader(self) -> jinja2.BaseLoader:
        return cast("jinja2.BaseLoader", self.env.loader)

    def setup(self, app: Application, *, name: str | None = None, **options: Any) -> bool:
        """Init the plugin for the given application."""
        initialized = super().setup(app, name=name, **options)
        loader = self.cfg.loader or jinja2.FileSystemLoader(
            self.cfg.template_folders,
            encoding=self.cfg.encoding,
        )

        self.__env__ = jinja2.Environment(
            auto_reload=self.cfg.auto_reload,
            cache_size=self.cfg.cache_size,
            extensions=self.cfg.extensions,
            loader=loader,
            autoescape=jinja2.select_autoescape(),
        )
        # jinja2 does not annotate Environment.globals
        cast("dict[str, Any]", self.__env__.globals)["app"] = app

        @self.add_global
        @jinja2.pass_context
        def debug(ctx: jinja2.runtime.Context, value: Any = None) -> str:
            """Debug current context to template."""
            return jinja2.filters.do_pprint((value is None and ctx) or value)

        return initialized

    @overload
    def __register__(self, obj: TVFn, jtype: TEnvParams = "globals") -> TVFn: ...

    @overload
    def __register__(self, obj: str, jtype: TEnvParams = "globals") -> Callable[[TVFn], TVFn]: ...

    def __register__(
        self, obj: TVFn | str, jtype: TEnvParams = "globals"
    ) -> TVFn | Callable[[TVFn], TVFn]:
        def wrapper(func: TVFn) -> TVFn:
            env_name = obj if isinstance(obj, str) else func.__name__
            ctx = getattr(self.env, jtype)
            ctx[env_name] = func
            return func

        if callable(obj):
            return wrapper(obj)

        return wrapper

    @overload
    def add_global(self, obj: TVFn) -> TVFn: ...

    @overload
    def add_global(self, obj: str) -> Callable[[TVFn], TVFn]: ...

    def add_global(self, obj: TVFn | str) -> TVFn | Callable[[TVFn], TVFn]:
        """Register function to globals.

        ::
            @jinja2.add_global
            def my_global():
                return {...}

        """
        return self.__register__(obj, "globals")

    @overload
    def add_filter(self, obj: TVFn) -> TVFn: ...

    @overload
    def add_filter(self, obj: str) -> Callable[[TVFn], TVFn]: ...

    def add_filter(self, obj: TVFn | str) -> TVFn | Callable[[TVFn], TVFn]:
        """Register function to filters.

        ::
            @jinja2.add_filter
            def my_filter():
                return {...}

        """
        return self.__register__(obj, "filters")

    def add_context(self, func: TVFn) -> TVFn:
        """Decorate a given function to use as a context processor.

        ::
            @jinja2.add_context
            def my_context():
                return {...}
        """
        self.ctx_providers.append(func)
        return func

    def add_template_folder(self, *paths: str | Path) -> None:
        """Append folders to the template search path.

        ::
            jinja.add_template_folder(Path(__file__).parent)
        """
        if not isinstance(self.env.loader, jinja2.FileSystemLoader):
            raise jinja2.TemplateError(
                f"{type(self.env.loader).__name__} doesn't support search paths"
            )
        folder_paths = [str(path) for path in paths]
        self.cfg.template_folders.extend(folder_paths)  # survive env rebuild in setup()
        self.env.loader.searchpath.extend(folder_paths)

    async def get_context(self, **context: Any) -> dict[str, Any]:
        ctx = dict(self.env.globals)
        for provider in self.ctx_providers:
            ctx_ = provider()
            if isawaitable(ctx_):
                ctx_ = await ctx_
            ctx.update(ctx_)
        ctx.update(context)
        return ctx

    async def render(self, path: str | jinja2.Template, **context: Any) -> str:
        """Render a template with the given context.

        :param path: Path to the template or a template object.
        :param context: Context to render the template.

        """
        env = self.env
        template = env.get_template(path)
        ctx = await self.get_context(**context)
        for reciever in self.receivers:
            reciever(path, ctx)

        return template.render(**ctx)

    # Depricated methods and properties

    def register(self, obj: TVFn | str) -> TVFn | Callable[[TVFn], TVFn]:
        """Register function to globals."""
        warn(
            "Use `add_global` instead of `register`",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.__register__(obj, "globals")

    def filter(self, obj: TVFn | str) -> TVFn | Callable[[TVFn], TVFn]:
        """Register function to filters."""
        warn("Use `add_filter` instead of `filter`", DeprecationWarning, stacklevel=2)
        return self.__register__(obj, "filters")

    def context_processor(self, func: TVFn) -> TVFn:
        """Decorate a given function to use as a context processor."""
        warn(
            "Use `add_context` instead of `context_processor`",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.add_context(func)
