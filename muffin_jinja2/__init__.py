"""Muffin-Jinja2 -- Jinja2 template engine for Muffin framework."""
from functools import cached_property
from inspect import isawaitable
from typing import Any, Callable, Dict, List, Literal, Optional, TypeVar, Union, cast, overload
from warnings import warn

from muffin import Application
from muffin.plugins import BasePlugin, PluginException

import jinja2

__version__ = "1.6.0"
__project__ = "muffin-jinja2"
__author__ = "Kirill Klenov <horneds@gmail.com>"
__license__ = "MIT"


TVFn = TypeVar("TVFn", bound=Callable)
TEnvParams = Literal["globals", "filters", "policies", "tests"]


class Plugin(BasePlugin):

    """The class is used to control the jinja2 integration to Muffin application."""

    name: str = "jinja2"
    defaults = {
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
        self.ctx_providers: List[Callable] = []
        self.receivers: List[Callable[[Union[str, jinja2.Template], Dict], Any]] = []

        super().__init__(app, **options)

    @cached_property
    def env(self) -> jinja2.Environment:
        env = self.__env__
        if env is None:
            raise PluginException("The plugin must be installed to application.")
        return env

    @cached_property
    def loader(self) -> jinja2.BaseLoader:
        return cast(jinja2.BaseLoader, self.env.loader)

    def setup(self, app: Application, **options):
        """Init the plugin for the given application."""
        super().setup(app, **options)

        if not self.cfg.loader:
            self.cfg.update(
                loader=jinja2.FileSystemLoader(
                    self.cfg.template_folders, encoding=self.cfg.encoding
                )
            )

        self.__env__ = jinja2.Environment(
            auto_reload=self.cfg.auto_reload,
            cache_size=self.cfg.cache_size,
            extensions=self.cfg.extensions,
            loader=self.cfg.loader,
        )
        self.__env__.globals["app"] = app

        @self.add_global
        @jinja2.pass_context
        def debug(ctx, value=None):
            """Debug current context to template."""
            return jinja2.filters.do_pprint(value is None and ctx or value)

    @overload
    def __register__(self, obj: TVFn, type: TEnvParams) -> TVFn:
        ...

    @overload
    def __register__(self, obj: str, type: TEnvParams) -> Callable[[TVFn], TVFn]:
        ...

    def __register__(self, obj, type: TEnvParams = "globals"):
        def wrapper(func):
            env_name = func.__name__
            if isinstance(obj, str):
                env_name = obj
            ctx = getattr(self.env, type)
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

    async def get_context(self, **context) -> Dict[str, Any]:
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
        warn("Use `add_register` instead of `register`", DeprecationWarning, 2)
        return self.__register__(obj, "globals")

    def filter(self, obj):
        """Register function to filters."""
        warn("Use `add_filter` instead of `filter`", DeprecationWarning, 2)
        return self.__register__(obj, "filters")

    def context_processor(self, func):
        """Decorate a given function to use as a context processor."""
        warn("Use `add_context` instead of `context_processor`", DeprecationWarning, 2)
        return self.add_context(func)
