# Muffin-Jinja2

Jinja2 template support for the [Muffin](https://github.com/klen/muffin) framework.

[![Tests](https://github.com/klen/muffin-jinja2/workflows/tests/badge.svg)](https://github.com/klen/muffin-jinja2/actions)
[![PyPI](https://img.shields.io/pypi/v/muffin-jinja2)](https://pypi.org/project/muffin-jinja2/)
[![Python versions](https://img.shields.io/pypi/pyversions/muffin-jinja2)](https://pypi.org/project/muffin-jinja2/)

## Requirements

- Python >= 3.11

## Installation

```console
$ pip install muffin-jinja2
```

## Usage

```python
import muffin
import muffin_jinja2

# Create Muffin Application
app = muffin.Application("example")

# Initialize the plugin
# As alternative: jinja2 = muffin_jinja2.Plugin(app, **options)
jinja2 = muffin_jinja2.Plugin()
jinja2.setup(app, template_folders=["src/templates"])


# Use it inside your handlers
@app.route("/")
async def index(request):
    context = {"var": 42}
    return await jinja2.render("index.html", **context)
```

With `src/templates/index.html` looking like this:

```html
<p>{{ var }}</p>
```

### Options

| Name                 | Default value        | Description                                                                                      |
| -------------------- | -------------------- | ------------------------------------------------------------------------------------------------ |
| **auto_reload**      | `False`              | Auto reload changed templates                                                                     |
| **cache_size**       | `400`                | Cache templates                                                                                   |
| **extensions**       | `()`                 | Enable Jinja2 extensions (`list \| tuple`)                                                        |
| **loader**           | `None`               | Template loader; a `FileSystemLoader` for `template_folders` is created by default                |
| **encoding**         | `utf-8`              | Default encoding for the file loader                                                              |
| **template_folders** | `["templates"]`      | List of template folders                                                                          |

You can provide the options when initializing the plugin:

```python
jinja2.setup(app, template_folders=["src/templates"], auto_reload=True)
```

Or set them in the `Muffin.Application` config with the `JINJA2_` prefix:

```python
JINJA2_AUTO_RELOAD = True

JINJA2_TEMPLATE_FOLDERS = ["tmpls"]
```

Application configuration options are case insensitive.

## Public API

- **`env`**: the `jinja2.Environment`. It is created by `setup()`; any access before setup raises
  `muffin.plugins.PluginNotInstalledError`.
- **`loader`**: the active template loader, a `jinja2.FileSystemLoader` built from
  `template_folders` unless the `loader` option is given.
- **`Error`**: alias for `jinja2.TemplateError`.
- **`add_global(func)`**, **`add_filter(func)`**: decorators to register a function in the
  environment globals or filters. Both accept a name as the first argument to register under
  another name:

  ```python
  @jinja2.add_global("div")
  def mod(a, b):
      return a // b
  ```

- **`add_context(func)`**: decorator to register a context processor. The function may be a
  coroutine; its result is merged into the context of every rendering.
- **`async get_context(**context)`**: build the rendering context: environment globals, then all
  registered context processors, then the given keyword arguments.
- **`async render(path, **context)`**: render a template. `path` is either a template name or a
  `jinja2.Template` object. Returns the rendered string.
- **`receivers`**: a plain list of callbacks, empty by default. Each callback is called as
  `receiver(path, ctx)` right before a template is rendered, where `path` is a template name or a
  `jinja2.Template` object and `ctx` is the context dict; mutate it to add values. Callbacks are
  synchronous and their return value is ignored. There is no decorator for them, add them
  manually:

  ```python
  def track(path, ctx):
      ctx["request_path"] = path


  jinja2.receivers.append(track)
  ```

Inside templates the application is available as `app`, and the `debug` global dumps the current
context (`{{ debug() }}`) or a given value (`{{ debug(value) }}`).

## Deprecated

`register`, `filter` and `context_processor` are the old names of `add_global`, `add_filter` and
`add_context`. They still work but emit `DeprecationWarning`.

## Tuning

```python
# Register a custom context processor
# (could be a function or a coroutine)
@jinja2.add_context
def custom_context():
    return {"VAR": "VALUE"}


# Register a function in the global context
@jinja2.add_global
def sum(a, b):
    return a + b


# Register a function with a different name
@jinja2.add_global("div")
def mod(a, b):
    return a // b


# Register a filter
@jinja2.add_filter
def test(value, a, b=None):
    return a if value else b


# Register a filter with a different name
@jinja2.add_filter("bool")
def boolean(value):
    return bool(value)


@app.route("/")
async def index(request):
    """Check whether the user is an admin."""
    local_context = {"key": "value"}
    return await jinja2.render("index.html", **local_context)
```

## Bug tracker

If you have any suggestions, bug reports or annoyances, please report them to the issue tracker at
https://github.com/klen/muffin-jinja2/issues.

## License

Licensed under the [MIT license](http://opensource.org/licenses/MIT). Development happens at
https://github.com/klen/muffin-jinja2.
