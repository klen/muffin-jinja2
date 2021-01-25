""" Muffin-Jinja2 -- Jinja2 template engine for Muffin framework. """
import typing as t
import jinja2
from json import dumps

import muffin
from muffin.plugin import BasePlugin, PluginException
from muffin.utils import to_awaitable


__version__ = "0.6.3"
__project__ = "muffin-jinja2"
__author__ = "Kirill Klenov <horneds@gmail.com>"
__license__ = "MIT"


F = t.TypeVar('F', bound=t.Callable[..., t.Any])


class Plugin(BasePlugin):

    """ The class is used to control the jinja2 integration to Muffin application. """

    name: str = 'jinja2'
    defaults = {
        'auto_reload': False,
        'cache_size': 50,
        'extensions': (),
        'loader': None,
        'encoding': 'utf-8',
        'template_folders': ['templates'],
    }

    def __init__(self, app: muffin.Application = None, **options):
        """ Initialize the plugin. """
        self.env: t.Optional[jinja2.Environment] = None
        self.providers: t.List[t.Callable[[], t.Awaitable]] = []
        self.receivers: t.List[t.Callable[[t.Union[str, jinja2.Template], t.Dict], t.Any]] = []

        super().__init__(app, **options)

    def setup(self, app: muffin.Application, **options):
        """Init the plugin for the given application."""
        super().setup(app, **options)

        if not self.cfg.loader:
            self.cfg.update(loader=jinja2.FileSystemLoader(
                self.cfg.template_folders, encoding=self.cfg.encoding))

        self.env = jinja2.Environment(
            auto_reload=self.cfg.auto_reload,
            cache_size=self.cfg.cache_size,
            extensions=self.cfg.extensions,
            loader=self.cfg.loader,
        )
        self.env.globals['app'] = app

        @self.register
        @jinja2.contextfunction
        def debug(ctx, value=None):
            """ Debug current context to template. """
            return jinja2.filters.do_pprint(value is None and ctx or value)

        @self.filter
        def jsonify(obj):
            return dumps(obj)

    def context_processor(self, func: F) -> F:
        """ Decorate a given function to use as a context processor.

        ::
            @jinja2.context_processor
            def my_context():
                return {...}
        """
        self.providers.append(to_awaitable(func))
        return func

    def register(self, name: t.Union[F, str]) -> t.Callable[[F], F]:
        """ Register function to globals. """
        if self.env is None:
            raise PluginException('The plugin must be installed to application.')

        def wrapper(func):
            env_name = func.__name__
            if isinstance(name, str):
                env_name = name
            if callable(func):
                self.env.globals[env_name] = func
            return func

        if callable(name):
            return wrapper(name)

        return wrapper

    def filter(self, name: t.Union[F, str]) -> t.Callable[[F], F]:
        """ Register function to filters. """
        if self.env is None:
            raise PluginException('The plugin must be installed to application.')

        def wrapper(func):
            env_name = func.__name__
            if isinstance(name, str):
                env_name = name
            if callable(func):
                self.env.filters[env_name] = func
            return func

        if callable(name):
            return wrapper(name)

        return wrapper

    async def render(self, path: t.Union[str, jinja2.Template], **context) -> str:
        """ Render a template with context. """
        if self.env is None:
            raise PluginException('Initialize the plugin first.')

        template = self.env.get_template(path)
        ctx = dict(self.env.globals)
        for provider in self.providers:
            ctx_ = await provider()
            ctx.update(ctx_)
        ctx.update(context)

        for reciever in self.receivers:
            reciever(path, ctx)

        return template.render(**ctx)
