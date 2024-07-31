"""Muffin-Jinja2 -- Jinja2 template engine for Muffin framework."""
from __future__ import annotations

from functools import cached_property
from inspect import isawaitable
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Literal,
    Optional,
    TypeVar,
    Union,
    cast,
    overload,
)
from warnings import warn

import jinja2
from muffin.plugins import BasePlugin, PluginNotInstalledError

if TYPE_CHECKING:
    from muffin import Application

TVFn = TypeVar("TVFn", bound=Callable)
TEnvParams = Literal["globals", "filters", "policies", "tests"]


class Plugin(BasePlugin):

    """The class is used to control the jinja2 integration to Muffin application."""

    name: str = "jinja2"
    defaults: ClassVar = {
        "auto_reload": False,
        "cache_size": 50,
        "extensions": (),
        "loader": None,
        "encoding": "utf-8",
        "template_folders": ["templates"],
    }

    Error = jinja2.TemplateError

    def __init__(self, app: Optional[Application] = None, **options):
        """Initialize the plugin."""
        self.__env__: Optional[jinja2.Environment] = None
        self.ctx_providers: list[Callable] = []
        self.receivers: list[Callable[[Union[str, jinja2.Template], dict], Any]] = []

        super().__init__(app, **options)

    @cached_property
    def env(self) -> jinja2.Environment:
        env = self.__env__
        if env is None:
            raise PluginNotInstalledError
        return env

    @cached_property
    def loader(self) -> jinja2.FileSystemLoader:
        return cast(jinja2.FileSystemLoader, self.env.loader)

    def setup(self, app: Application, **options):
        """Init the plugin for the given application."""
        super().setup(app, **options)

        if not self.cfg.loader:
            self.cfg.update(
                loader=jinja2.FileSystemLoader(
                    self.cfg.template_folders,
                    encoding=self.cfg.encoding,
                ),
            )

        self.__env__ = jinja2.Environment(
            auto_reload=self.cfg.auto_reload,
            cache_size=self.cfg.cache_size,
            extensions=self.cfg.extensions,
            loader=self.cfg.loader,
            autoescape=jinja2.select_autoescape(["html", "xml"]),
        )
        self.__env__.globals["app"] = app

        @self.add_global
        @jinja2.pass_context
        def debug(ctx, value=None):
            """Debug current context to template."""
            return jinja2.filters.do_pprint(value is None and ctx or value)

    @overload
    def __register__(self, obj: TVFn, jtype: TEnvParams) -> TVFn:
        ...

    @overload
    def __register__(self, obj: str, jtype: TEnvParams) -> Callable[[TVFn], TVFn]:
        ...

    def __register__(self, obj, jtype: TEnvParams = "globals"):
        def wrapper(func):
            env_name = func.__name__
            if isinstance(obj, str):
                env_name = obj
            ctx = getattr(self.env, jtype)
            ctx[env_name] = func
            return func

        if callable(obj):
            return wrapper(obj)

        return wrapper

    def add_global(self, obj):
        """Register function to globals.

        ::
            @jinja2.add_global
            def my_global():
                return {...}

        """
        return self.__register__(obj, "globals")

    def add_filter(self, obj):
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

    async def get_context(self, **context) -> dict[str, Any]:
        ctx = dict(self.env.globals)
        for provider in self.ctx_providers:
            ctx_ = provider()
            if isawaitable(ctx_):
                ctx_ = await ctx_
            ctx.update(ctx_)
        ctx.update(context)
        return ctx

    async def render(self, path: Union[str, jinja2.Template], **context) -> str:
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

    def register(self, obj):
        """Register function to globals."""
        warn(
            "Use `add_register` instead of `register`",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.__register__(obj, "globals")

    def filter(self, obj):
        """Register function to filters."""
        warn("Use `add_filter` instead of `filter`", DeprecationWarning, stacklevel=2)
        return self.__register__(obj, "filters")

    def context_processor(self, func):
        """Decorate a given function to use as a context processor."""
        warn(
            "Use `add_context` instead of `context_processor`",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.add_context(func)
