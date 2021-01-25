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

- python >= 3.8

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
    # As alternative: jinja2 = Jinja2(app, **options)
    jinja2 = muffin_jinja2.Plugin()
    jinja2.setup(app, template_folders=['src/templates'])

    # Use it inside your handlers
    @app.route('/')
    async def index(request):
        context = {'var': 42}
        return await jinja2.render('index.html', **context)


Options
-------

Format: Name -- Description (`default value`)

**auto_reload** -- Auto reload changed templates (`False`)

**cache_size** -- Cache templates (`50`)

**extensions** -- Enable Jinja2 Extensions (`None`)

**loader** -- Template loader (`FileSystemLoader`)

**encoding** -- Default encoding for file loader (`utf-8`)

**template_folders** -- List of template folders (`['templates']`)


You are able to provide the options when you are initiliazing the plugin:

.. code-block:: python

    jinja2.init(app, template_folders=['src/templates'], auto_reload=True)


Or setup it inside `Muffin.Application` config using the `jinja2_` prefix:

.. code-block:: python

   JINJA2_AUTO_RELOAD = True

   JINJA2_TEMPLATE_FOLDERS = ['tmpls']

`Muffin.Application` configuration options are case insensetive


Tunning
-------

.. code-block:: python

    # Register custom context processor
    # could be a function/coroutine
    @jinja2.context_processor
    def custom_context():
        return { 'VAR': 'VALUE' }

    # Register a function into global context
    @jinja2.register
    def sum(a, b):
        return a + b

    # Register a function with a different name
    @jinja2.register('div')
    def mod(a, b):
        return a // b

    # Register a filter
    @jinja2.filter
    def test(value, a, b=None):
        return a if value else b

    # Register a filter with a different name
    @jinja2.filter('bool')
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
