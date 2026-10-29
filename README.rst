Muffin-Jinja2
#############

.. _description:

**Muffin-Jinja2** -- Support Jinja2 templates for Muffin_ Framework

.. _badges:

.. image:: https://github.com/klen/muffin-jinja2/workflows/tests/badge.svg
    :target: https://github.com/klen/muffin-jinja2/actions
    :alt: Tests Status

.. image:: https://img.shields.io/pypi/v/muffin-jinja2
    :target: https://pypi.org/project/muffin-jinja2/
    :alt: PYPI Version

.. _contents:

.. contents::

.. _requirements:

Requirements
=============

- python >= 3.11

.. _installation:

Installation
=============

**Muffin-Jinja2** should be installed using pip: ::

    pip install muffin-jinja2

.. _usage:

Usage
=====

.. code-block:: python

    import muffin
    import muffin_jinja2

    # Create Muffin Application
    app = muffin.Application('example')

    # Initialize the plugin
    # As alternative: jinja2 = muffin_jinja2.Plugin(app, **options)
    jinja2 = muffin_jinja2.Plugin()
    jinja2.setup(app, template_folders=['src/templates'])

    # Use it inside your handlers
    @app.route('/')
    async def index(request):
        context = {'var': 42}
        return await jinja2.render('index.html', **context)

With ``src/templates/index.html`` looking like: ::

    <p>{{ var }}</p>


Options
-------

==================== ==================== ====================
Name                 Default value        Description
-------------------- -------------------- --------------------
**auto_reload**      ``False``            Auto reload changed templates
**cache_size**       ``50``               Cache templates
**extensions**       ``()``               Enable Jinja2 Extensions (``list | tuple``)
**loader**           ``None``             Template loader, a ``FileSystemLoader``
                                          for ``template_folders`` is created by default
**encoding**         ``utf-8``            Default encoding for file loader
**template_folders** ``['templates']``    List of template folders
==================== ==================== ====================


You are able to provide the options when you are initiliazing the plugin:

.. code-block:: python

    jinja2.setup(app, template_folders=['src/templates'], auto_reload=True)


Or setup it inside ``Muffin.Application`` config using the `jinja2_` prefix for example:

.. code-block:: python

   JINJA2_AUTO_RELOAD = True

   JINJA2_TEMPLATE_FOLDERS = ['tmpls']

``Muffin.Application`` configuration options are case insensitive


Public API
==========

The plugin instance provides the following members.

``env``
    The ``jinja2.Environment``. It is created by ``setup()``; any access before
    setup raises ``muffin.plugins.PluginNotInstalledError``.

``loader``
    The active template loader -- a ``jinja2.FileSystemLoader`` built from
    ``template_folders`` unless the ``loader`` option is given.

``Error``
    Alias for ``jinja2.TemplateError``.

``add_global(func)``, ``add_filter(func)``
    Decorators to register a function in the environment globals or filters.
    Both accept a name as first argument to register under another name: ::

        @jinja2.add_global('div')
        def mod(a, b):
            return a // b

``add_context(func)``
    Decorator to register a context processor. The function may be
    a coroutine and its result is merged into the context of every rendering.

``async get_context(**context)``
    Build the rendering context: environment globals, then all registered
    context processors, then the given keyword arguments.

``async render(path, **context)``
    Render a template. ``path`` is either a template name or a
    ``jinja2.Template`` object. Returns the rendered string.

``receivers``
    A plain list of callbacks, empty by default. Each callback is called as
    ``reciever(path, ctx)`` right before a template is rendered, where ``path``
    is a template name or a ``jinja2.Template`` object and ``ctx`` is the
    context dict -- mutate it to add values. Callbacks are synchronous and
    their return value is ignored. There is no decorator for them, add them
    manually: ::

        def track(path, ctx):
            ctx['request_path'] = path

        jinja2.receivers.append(track)

Inside templates the application is available as ``app`` and the ``debug``
global dumps the current context (``{{ debug() }}``) or a given value
(``{{ debug(value) }}``).


Deprecated
----------

``register``, ``filter`` and ``context_processor`` are the old names of
``add_global``, ``add_filter`` and ``add_context``. They still work but emit
``DeprecationWarning``.


Tunning
-------

.. code-block:: python

    # Register custom context processor
    # could be a function/coroutine
    @jinja2.add_context
    def custom_context():
        return { 'VAR': 'VALUE' }

    # Register a function into global context
    @jinja2.add_global
    def sum(a, b):
        return a + b

    # Register a function with a different name
    @jinja2.add_global('div')
    def mod(a, b):
        return a // b

    # Register a filter
    @jinja2.add_filter
    def test(value, a, b=None):
        return a if value else b

    # Register a filter with a different name
    @jinja2.add_filter('bool')
    def boolean(value):
        return bool(value)

    @app.route('/')
    async def index(request):
        """ Check for user is admin. """
        local_context = {'key': 'value'}
        return await jinja2.render('index.html', **local_context)


.. _bugtracker:

Bug tracker
===========

If you have any suggestions, bug reports or
annoyances please report them to the issue tracker
at https://github.com/klen/muffin-jinja2/issues

.. _contributing:

Contributing
============

Development of Muffin-Jinja2 happens at: https://github.com/klen/muffin-jinja2


Contributors
=============

* klen_ (Kirill Klenov)

.. _license:

License
========

Licensed under a `MIT license`_.

.. _links:


.. _klen: https://github.com/klen
.. _Muffin: https://github.com/klen/muffin

.. _MIT license: http://opensource.org/licenses/MIT
