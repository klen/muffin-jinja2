import muffin
import pytest


@pytest.fixture(scope='session')
def app(loop):
    app = muffin.Application(
        'jinja2', loop=loop,

        JINJA2_TEMPLATE_FOLDERS='tests',
        PLUGINS=['muffin_jinja2'])

    @app.ps.jinja2.context_processor
    def global_context():
        return {'global': 'done'}

    @app.ps.jinja2.register
    def sum(a, b):
        return a + b

    @app.ps.jinja2.filter
    def test(test, a, b=None):
        return a if test else b

    @app.register('/')
    def index(request):
        return app.ps.jinja2.render('template.html', **request.GET)

    @app.register('/unknown')
    def unknown(request):
        return app.ps.jinja2.render('unknown.html', **request.GET)

    return app


def test_muffin_jinja2(app, client):
    response = client.get('/', {'name': 'jinja2'})
    assert '<h1>Hello jinja2!</h1>' in response.text
    assert '<p>8</p>' in response.text
    assert '<b>done</b>' in response.text
    assert '<i>yes</i>' in response.text
    assert '<Application: jinja2>' in response.text

    with pytest.raises(Exception):
        client.get('/unknown')
