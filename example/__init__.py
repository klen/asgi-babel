"""A simple i18n example (en/fr).

To run the example install any ASGI server (uvicorn/hypercorn/etc):

    uvicorn example:app

"""
from asgi_tools import ResponseHTML
from asgi_babel import BabelMiddleware, current_locale, gettext


async def app(scope, receive, send):
    locale = current_locale.get()

    response = ResponseHTML(
        "<link rel='stylesheet' href='https://cdn.jsdelivr.net/npm/bootstrap@4.5.3/dist/css/bootstrap.min.css'>"  # noqa
        "<div class='container p-3'>"
            # Translate text
            f"<h2>{ 'ASGI-Babel Example (only en/fr supported)' }</h2>"
            "<h3>" + gettext('Hello World!') + "</h3>"
            "<h3>" + gettext('Locale information:') + "</h3>"
            "<ul>"
                f"<li>Display name: {locale.display_name}</li>"
                f"<li>Language code: {locale.language}</li>"
                f"<li>Decimal symbols: {locale.number_symbols['decimal'] }</li>"
                f"<li>First week day: {locale.first_week_day }</li>"
                f"<li>Monday names: {locale.days['format']['wide'][1] }</li>"
                f"<li>See babel docs for more</li>"
            "</ul>"
        "</div>"
    )
    await response(scope, receive, send)


app = BabelMiddleware(app, locales_dirs=['example/locales'])
