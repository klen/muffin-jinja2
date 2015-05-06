Muffin-Jinja2
#############

.. _description:

Muffin-Jinja2 -- Jinja2 template engine for Muffin framework.

.. _badges:

.. image:: http://img.shields.io/travis/klen/muffin-jinja2.svg?style=flat-square
    :target: http://travis-ci.org/klen/muffin-jinja2
    :alt: Build Status

.. image:: http://img.shields.io/pypi/v/muffin-jinja2.svg?style=flat-square
    :target: https://pypi.python.org/pypi/muffin-jinja2

.. image:: http://img.shields.io/pypi/dm/muffin-jinja2.svg?style=flat-square
    :target: https://pypi.python.org/pypi/muffin-jinja2

.. image:: http://img.shields.io/gratipay/klen.svg?style=flat-square
    :target: https://www.gratipay.com/klen/
    :alt: Donate

.. _contents:

.. contents::

.. _requirements:

Requirements
=============

- python >= 3.3

.. _installation:

Installation
=============

**Muffin-Jinja2** should be installed using pip: ::

    pip install muffin-jinja2

.. _usage:

Usage
=====

Add **muffin_jinja2** to **PLUGINS** in your Muffin Application configuration.

Options
-------

**JINJA2_AUTO_RELOAD** -- Auto reload changed templates (False)

**JINJA2_CACHE_SIZE** -- Cache templates (50)

**JINJA2_EXTENSIONS** -- Enable Jinja2 Extensions (None)

**JINJA2_LOADER** -- Template loader (FileSystemLoader)

**JINJA2_ENCODING** -- Default encoding for file loader

**JINJA2_TEMPLATE_FOLDERS** -- List of template folders (['templates'])

Views
-----

::

    # Register custom context processor
    # could be a function/coroutine
    @app.ps.jinja2.context_processor
    def custom_context():
        return { 'VAR': 'VALUE' }

    # Register a function into global context
    @app.ps.jinja2.register
    def sum(a, b):
        return a + b

    # Register a function with a different name
    @app.ps.jinja2.register('div')
    def mod(a, b):
        return a // b

    # Register a filter
    @app.ps.jinja2.filter
    def test(value, a, b=None):
        return a if value else b

    # Register a filter with a different name
    @app.ps.jinja2.filter('bool')
    def boolean(value):
        return bool(value)

    @app.register('/')
    def index(request):
        """ Check for user is admin. """
        local_context = {'key': 'value'}
        return app.ps.jinja2.render('index.html', **local_context)


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
=======

Licensed under a `MIT license`_.

.. _links:


.. _klen: https://github.com/klen

.. _MIT license: http://opensource.org/licenses/MIT
