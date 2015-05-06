""" Muffin-Jinja2 -- Jinja2 template engine for Muffin framework. """
import asyncio

import jinja2
from muffin.plugins import BasePlugin, PluginException
from muffin.utils import to_coroutine


__version__ = "0.0.6"
__project__ = "muffin-jinja2"
__author__ = "Kirill Klenov <horneds@gmail.com>"
__license__ = "MIT"


class Plugin(BasePlugin):

    """ The class is used to control the jinja2 integration to Muffin application. """

    name = 'jinja2'
    defaults = dict(
        auto_reload=False,
        cache_size=50,
        extensions=(),
        loader=None,
        encoding='utf-8',
        template_folders=('templates',),
    )

    def __init__(self, **options):
        """ Initialize the plugin. """
        super().__init__(**options)

        self.env = None
        self.providers = []
        self.functions = {}

    def setup(self, app):
        """ Setup the plugin from an application. """
        super().setup(app)

        if isinstance(self.options.template_folders, str):
            self.options.template_folders = [self.options.template_folders]

        self.options.template_folders = list(self.options.template_folders)
        if not self.options.loader:
            self.options.loader = FileSystemLoader(
                self.options.template_folders, encoding=self.options.encoding)

        self.context_processor(lambda: {'app': self.app})
        self.env = jinja2.Environment(
            auto_reload=self.options.auto_reload,
            cache_size=self.options.cache_size,
            extensions=self.options.extensions,
            loader=self.options.loader,
        )

        @self.register
        @jinja2.contextfunction
        def debug(ctx):
            """ Debug current context to template. """
            return jinja2.filters.do_pprint(ctx)

    def context_processor(self, func):
        """ Decorator for adding a context provider.

        ::
            @app.ps.jinja2.context_processor
            def my_context():
                return {...}
        """
        func = to_coroutine(func)
        self.providers.append(func)
        return func

    def register(self, value):
        """ Register function to globals. """
        if self.env is None:
            raise PluginException('The plugin must be installed to application.')

        def wrapper(func):
            name = func.__name__
            if isinstance(value, str):
                name = value
            if callable(func):
                self.env.globals[name] = func
            return func

        if callable(value):
            return wrapper(value)

        return wrapper

    def filter(self, value):
        """ Register function to filters. """
        if self.env is None:
            raise PluginException('The plugin must be installed to application.')

        def wrapper(func):
            name = func.__name__
            if isinstance(value, str):
                name = value
            if callable(func):
                self.env.filters[name] = func
            return func

        if callable(value):
            return wrapper(value)

        return wrapper

    @asyncio.coroutine
    def render(self, path, **context):
        """ Render a template with context. """
        template = self.env.get_template(path)

        ctx = dict()
        for provider in self.providers:
            _ctx = yield from provider()
            ctx.update(_ctx)
        ctx.update(context)

        return template.render(**ctx)


class FileSystemLoader(jinja2.FileSystemLoader):

    """ Save searchpath by link. """

    def __init__(self, searchpath, encoding='utf-8'):
        """ Doesnt copy searchpath. """
        if isinstance(searchpath, str):
            searchpath = [searchpath]
        self.searchpath = searchpath
        self.encoding = encoding
