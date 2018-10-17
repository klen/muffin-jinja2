import muffin
import pytest


@pytest.fixture(scope='session')
def app():
    app = muffin.Application('jinja2', JINJA2_TEMPLATE_FOLDERS='tests')
    jinja2 = app.install('muffin_jinja2')

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

    @app.register('/')
    def index(request):
        return jinja2.render('template.html', **request.query)

    @app.register('/unknown')
    def unknown(request):
        return jinja2.render('unknown.html', **request.query)

    return app


async def test_muffin_jinja2(client):
    async with client.get('/', params={'name': 'jinja2'}) as resp:
        assert resp.status == 200
        text = await resp.text()

    assert '<h1>Hello jinja2!</h1>' in text
    assert '<p>8</p>' in text
    assert '<p>3</p>' in text
    assert '<b>done</b>' in text
    assert '<i>yes</i>' in text
    assert '<Application: jinja2>' in text

    async with client.get('/unknown') as resp:
        assert resp.status == 500
