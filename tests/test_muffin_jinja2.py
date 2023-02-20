import muffin
import pytest

import jinja2


@pytest.fixture(scope="session")
def app():
    return muffin.Application(name="jinja2", jinja2_template_folders=["tests"])


@pytest.fixture(scope="session")
def jinja(app):
    import muffin_jinja2

    return muffin_jinja2.Plugin(app)


@pytest.fixture(scope="session")
def setup_web(app, jinja):
    @jinja.add_context
    def global_context():
        return {"global": "done"}

    @jinja.add_global
    def sum(a: int, b: int) -> int:
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


async def test_muffin_jinja2(setup_web, client, app):
    async with client.lifespan():

        res = await client.get("/", query={"name": "jinja2"})
        assert res.status_code == 200

        text = await res.text()
        assert "<h1>Hello jinja2!</h1>" in text
        assert "<p>8</p>" in text
        assert "<p>3</p>" in text
        assert "<b>done</b>" in text
        assert "<i>yes</i>" in text
        assert "<muffin.Application: jinja2>" in text

        res = await client.get("/unknown")
        assert res.status_code == 500

        plugin = app.plugins["jinja2"]

        assert await plugin.render(jinja2.Template("OK"))


# pylama:ignore=D
