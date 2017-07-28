""" Muffin-Jinja2 -- Jinja2 template engine for Muffin framework. """
import asyncio
import pprint

import jinja2
from muffin.plugins import BasePlugin, PluginException
from muffin.utils import to_coroutine
from ujson import dumps


__version__ = "0.1.1"
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
        enable_async=False,
    )

    def __init__(self, app=None, **options):
        """ Initialize the plugin. """
        self.env = None
        self.providers = []
        self.receivers = []
        self.functions = {}

        super().__init__(app, **options)

    def setup(self, app):
        """ Setup the plugin from an application. """
        super().setup(app)

        if isinstance(self.cfg.template_folders, str):
            self.cfg.template_folders = [self.cfg.template_folders]

        self.cfg.template_folders = list(self.cfg.template_folders)
        if not self.cfg.loader:
            self.cfg.loader = FileSystemLoader(
                self.cfg.template_folders, encoding=self.cfg.encoding)

        self.context_processor(lambda: {'app': self.app})
        self.env = jinja2.Environment(
            auto_reload=self.cfg.auto_reload,
            cache_size=self.cfg.cache_size,
            extensions=self.cfg.extensions,
            loader=self.cfg.loader,
            enable_async=self.cfg.enable_async,
        )

        @self.register
        @jinja2.contextfunction
        def debug(ctx, value=None):
            """ Debug current context to template. """
            return jinja2.filters.do_pprint(value is None and ctx or value)

        @self.filter
        def jsonify(obj):
            return dumps(obj, ensure_ascii=False, encode_html_chars=True)

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

    def update_receivers(self, context):
        for receivers in self.receivers:
            receivers(path, context)

    @asyncio.coroutine
    def get_updated_context(self, context):
        updated_context = {**context}

        provider_contexts = yield from asyncio.gather(*[
            provider() for provider in self.providers
        ])

        for provider_context in provider_contexts:
            updated_context.update(provider_context)

        return updated_context

    @asyncio.coroutine
    def render(self, path, **context):
        """ Render a template with context. """
        template = self.env.get_template(path)
        updated_context = yield from self.get_updated_context(context)
        self.update_receivers(updated_context)

        return template.render(**updated_context)

    @asyncio.coroutine
    def render_async(self, path, **context):
        """ Async render a template with context. """
        template = self.env.get_template(path)
        updated_context = yield from self.get_updated_context(context)
        self.update_receivers(updated_context)

        return (yield from template.render_async(**updated_context))


class FileSystemLoader(jinja2.FileSystemLoader):

    """ Save searchpath by link. """

    def __init__(self, searchpath, encoding='utf-8'):
        """ Doesnt copy searchpath. """
        if isinstance(searchpath, str):
            searchpath = [searchpath]
        self.searchpath = searchpath
        self.encoding = encoding


try:
    import muffin_debugtoolbar as md

    class DebugPanel(md.panels.DebugPanel):

        """ Integration to debug panel. """

        name = 'Jinja2'
        template = jinja2.Template("""
            {% for path, context in templates %}
                <div class="panel panel-default">
                        <div class="panel-heading"
                            style="cursor:pointer"
                            data-toggle="collapse" data-target="#template-{{loop.index}}">
                                <a href="#template-{{loop.index}}">{{path}}</a></div>
                    <div class="panel-body collapse" id="template-{{loop.index}}">
                        <pre>{{ context|escape }}</pre>
                    </div>
                </div>
            {% endfor %}
        """)

        def __init__(self, app, request=None):
            """ Initialize the plugin. """
            super(DebugPanel, self).__init__(app, request)
            self.templates = []

        def wrap_handler(self, handler, context_switcher):
            """ Wrap handler. """
            def render(path, context):
                self.templates.append(
                    (path, pprint.pformat(context, indent=2, width=120, depth=5)))

            context_switcher.add_context_in(
                lambda: self.app.ps.jinja2.receivers.append(render))

            context_switcher.add_context_out(
                lambda: self.app.ps.jinja2.receivers.remove(render))

            return handler

        @property
        def has_content(self):
            """ Mark the panel has content. """
            return self.templates

        def render_vars(self):
            """ Get template variables. """
            return {
                'templates': self.templates
            }

except ImportError:
    pass
