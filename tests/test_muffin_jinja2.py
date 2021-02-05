import muffin
import pytest
import jinja2


@pytest.fixture(scope='session')
def app():
    from muffin_jinja2 import Plugin as Jinja2

    app = muffin.Application('jinja2', jinja2_template_folders=['tests'])
    jinja2 = Jinja2(app)
    assert jinja2.cfg.template_folders == ['tests']

    @jinja2.context_processor
    def global_context():
        return {'global': 'done'}

    @jinja2.register
    def sum(a, b):
        return a + b

    @jinja2.register('div')
    def _div_(a, b):
        return a // b

    @jinja2.filter
    def test(test, a, b=None):
        return a if test else b

    @app.route('/')
    async def index(request):
        return await jinja2.render('template.html', **request.url.query)

    @app.route('/unknown')
    async def unknown(request):
        return await jinja2.render('unknown.html', **request.url.query)

    return app


async def test_muffin_jinja2(app, client):
    res = await client.get('/', query={'name': 'jinja2'})
    assert res.status_code == 200

    text = await res.text()
    assert '<h1>Hello jinja2!</h1>' in text
    assert '<p>8</p>' in text
    assert '<p>3</p>' in text
    assert '<b>done</b>' in text
    assert '<i>yes</i>' in text
    assert '<muffin.Application: jinja2>' in text

    res = await client.get('/unknown')
    assert res.status_code == 500

    plugin = app.plugins['jinja2']

    assert await plugin.render(jinja2.Template('OK'))


# pylama:ignore=D
