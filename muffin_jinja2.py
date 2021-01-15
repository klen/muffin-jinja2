""" Muffin-Jinja2 -- Jinja2 template engine for Muffin framework. """
import jinja2
from json import dumps

from muffin.plugin import BasePlugin, PluginException
from muffin.utils import to_awaitable


__version__ = "0.3.1"
__project__ = "muffin-jinja2"
__author__ = "Kirill Klenov <horneds@gmail.com>"
__license__ = "MIT"


class Plugin(BasePlugin):

    """ The class is used to control the jinja2 integration to Muffin application. """

    name = 'jinja2'
    defaults = {
        'auto_reload': False,
        'cache_size': 50,
        'extensions': (),
        'loader': None,
        'encoding': 'utf-8',
        'template_folders': ['templates'],
    }

    def __init__(self, app=None, **options):
        """ Initialize the plugin. """
        self.env = None
        self.providers = []
        self.receivers = []
        self.functions = {}

        super().__init__(app, **options)

    def init(self, app, **options):
        """Init the plugin from an application."""
        super().init(app, **options)

        if isinstance(self.cfg.template_folders, str):
            self.cfg.template_folders = [self.cfg.template_folders]

        self.cfg.template_folders = list(self.cfg.template_folders)
        if not self.cfg.loader:
            self.cfg.loader = FileSystemLoader(
                self.cfg.template_folders, encoding=self.cfg.encoding)

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

    def context_processor(self, func):
        """ Decorate a given function to use as a context processor.

        ::
            @jinja2.context_processor
            def my_context():
                return {...}
        """
        func = to_awaitable(func)
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

    async def render(self, path, **context):
        """ Render a template with context. """
        template = self.env.get_template(path)

        ctx = dict()
        for provider in self.providers:
            ctx_ = await provider()
            ctx.update(ctx_)
        ctx.update(context)

        for reciever in self.receivers:
            reciever(path, ctx)

        return template.render(**ctx)


class FileSystemLoader(jinja2.FileSystemLoader):

    """ Save searchpath by link. """

    def __init__(self, searchpath, encoding='utf-8'):
        """ Doesnt copy searchpath. """
        if isinstance(searchpath, str):
            searchpath = [searchpath]
        self.searchpath = searchpath
        self.encoding = encoding
