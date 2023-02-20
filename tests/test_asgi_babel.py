import asgi_tools as tools
import pytest
from asgi_tools.tests import ASGITestClient


@pytest.fixture
def app():
    from asgi_babel import current_locale

    app = tools.App(debug=True)

    @app.route("/locale")
    async def locale(request):
        return current_locale.get()

    return app


async def test_select_locale_by_request():
    from asgi_babel import select_locale_by_request

    request = tools.Request(
        {
            "headers": [
                (b"accept-language", b"fr-CH, fr;q=0.9, en;q=0.8, de;q=0.7, *;q=0.5")
            ]
        },
        None,
        None,
    )
    lang = await select_locale_by_request(request)
    assert lang == "fr-CH"

    request = tools.Request(
        {"headers": [(b"accept-language", b"en-US,en;q=0.9,ru;q=0.8,ru-RU;q=0.7")]},
        None,
        None,
    )
    lang = await select_locale_by_request(request)
    assert lang == "en-US"


async def test_setup():
    from asgi_babel import BabelMiddleware

    md = BabelMiddleware(None)
    assert md.domain == "messages"
    assert md.default_locale == "en"
    assert md.locales_dirs == ["locales"]
    assert md.locale_selector
    assert md.translations == {}


async def test_middleware(app):
    from asgi_babel import BabelMiddleware, gettext

    @app.route("/hello")
    async def hello(request):
        return gettext("Hello World!")

    babel = BabelMiddleware(app, locales_dirs=["example/locales"])
    client = ASGITestClient(babel)

    res = await client.get("/locale")
    assert await res.text() == "en"

    res = await client.get(
        "/locale",
        headers={"accept-language": "fr-CH, fr;q=0.9, en;q=0.8, de;q=0.7, *;q=0.5"},
    )
    assert await res.text() == "fr_CH"

    res = await client.get("/hello")
    assert await res.text() == "Hello World!"

    res = await client.get(
        "/hello",
        headers={"accept-language": "fr-CH, fr;q=0.9, en;q=0.8, de;q=0.7, *;q=0.5"},
    )
    assert await res.text() == "Bonjour le monde!"


async def test_readme(app):
    from asgi_babel import BabelMiddleware, current_locale, gettext

    async def my_app(scope, receive, send):
        """Get a current locale."""
        locale = current_locale.get().language.encode()
        hello_world = gettext("Hello World!").encode()

        await send({"type": "http.response.start", "status": 200})
        await send(
            {
                "type": "http.response.body",
                "body": b"Current locale is %s\n" % locale,
                "more_body": True,
            }
        )
        await send({"type": "http.response.body", "body": hello_world})

    app = BabelMiddleware(my_app, locales_dirs=["example/locales"])
    client = ASGITestClient(app)

    res = await client.get("/")
    assert await res.text() == "Current locale is en\nHello World!"

    res = await client.get("/", headers={"accept-language": "fr-CH, fr;q=0.9"})
    assert await res.text() == "Current locale is fr\nBonjour le monde!"

    app = tools.App()
    app.middleware(BabelMiddleware.setup(locales_dirs=["example/locales"]))

    @app.route("/")
    async def index(request):
        return gettext("Hello World!")

    @app.route("/locale")
    async def locale(request):
        return current_locale.get().language

    client = ASGITestClient(app)

    res = await client.get("/")
    assert await res.text() == "Hello World!"

    res = await client.get("/", headers={"accept-language": "fr-CH, fr;q=0.9"})
    assert await res.text() == "Bonjour le monde!"
