import jinja2
import muffin
import pytest

import muffin_jinja2


@pytest.fixture(scope="session")
def app():
    return muffin.Application(name="jinja2", jinja2_template_folders=["tests"])


@pytest.fixture(scope="session")
def jinja(app):
    import muffin_jinja2

    return muffin_jinja2.Plugin(app)


@pytest.fixture(scope="session")
def _setup_web(app, jinja):
    @jinja.add_context
    def global_context():
        return {"global": "done"}

    @jinja.add_global
    def sum(a: int, b: int) -> int:  # noqa: A001
        return a + b

    @jinja.add_global("div")
    def _div_(a, b):
        return a // b

    @jinja.add_filter
    def test(test, a, b=None):
        return a if test else b

    @app.route("/")
    async def index(request):
        return await jinja.render("template.html", **request.url.query)

    @app.route("/unknown")
    async def unknown(request):
        return await jinja.render("unknown.html", **request.url.query)


def test_base(jinja):
    assert jinja
    assert jinja.env
    assert jinja.loader
    assert jinja.cfg.template_folders == ["tests"]


@pytest.mark.usefixtures("_setup_web")
async def test_muffin_jinja2(client, app):
    async with client.lifespan():
        res = await client.get("/", query={"name": "jinja2"})
        assert res.status_code == 200

        text = await res.text()
        assert "<h1>Hello jinja2!</h1>" in text
        assert "<p>8</p>" in text
        assert "<p>3</p>" in text
        assert "<b>done</b>" in text
        assert "<i>yes</i>" in text
        assert "muffin.Application: jinja2" in text

        res = await client.get("/unknown")
        assert res.status_code == 500

        plugin = app.plugins["jinja2"]

        assert await plugin.render(jinja2.Template("OK"))


async def test_receivers(jinja):
    received = []

    def receiver(path, ctx):
        received.append(path)
        ctx["value"] = "done"

    jinja.receivers.append(receiver)
    try:
        assert await jinja.render(jinja2.Template("{{ value }}")) == "done"
    finally:
        jinja.receivers.remove(receiver)

    assert received


def test_setup_returns():
    app = muffin.Application(name="setup")

    plugin = muffin_jinja2.Plugin()
    assert plugin.setup(app) is True
    assert app.plugins["jinja2"] is plugin

    disabled = muffin_jinja2.Plugin()
    assert disabled.setup(app, disabled=True) is False
    assert disabled not in app.plugins.values()


async def test_async_context(jinja):
    async def provider():
        return {"asy": "done"}

    jinja.ctx_providers.append(provider)
    try:
        assert await jinja.render(jinja2.Template("{{ asy }}")) == "done"
    finally:
        jinja.ctx_providers.remove(provider)


async def test_autoescape(tmp_path):
    (tmp_path / "page.html").write_text("{{ value }}")
    (tmp_path / "page.htm").write_text("{{ value }}")

    plugin = muffin_jinja2.Plugin()
    plugin.setup(muffin.Application(name="autoescape"), template_folders=[str(tmp_path)])

    value = "<script>alert(1)</script>"
    escaped = "&lt;script&gt;alert(1)&lt;/script&gt;"
    assert await plugin.render("page.html", value=value) == escaped
    assert await plugin.render("page.htm", value=value) == escaped


async def test_setup_twice(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    (tmp_path / "a" / "x.html").write_text("A")
    (tmp_path / "b" / "x.html").write_text("B")

    app_a = muffin.Application(name="first")
    app_b = muffin.Application(name="second")
    plugin = muffin_jinja2.Plugin()

    plugin.setup(app_a, template_folders=[str(tmp_path / "a")])
    assert await plugin.render("x.html") == "A"

    plugin.setup(app_b, template_folders=[str(tmp_path / "b")])
    assert await plugin.render("x.html") == "B"
    assert plugin.env.globals["app"] is app_b


async def test_custom_loader():
    loader = jinja2.DictLoader({"x.html": "{{ value }}"})

    plugin = muffin_jinja2.Plugin()
    plugin.setup(muffin.Application(name="custom"), loader=loader)

    assert plugin.loader is loader
    assert await plugin.render("x.html", value="ok") == "ok"
