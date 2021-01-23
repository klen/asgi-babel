"""Support cookie-encrypted sessions for ASGI applications."""

__version__ = "0.1.1"
__license__ = "MIT"

import re
import typing as t
from babel import Locale, support  # type: ignore
from asgi_tools import Request
from asgi_tools.middleware import BaseMiddeware
from asgi_tools.types import ASGIApp, Scope, Receive, Send
from dataclasses import dataclass, field
from contextvars import ContextVar


__all__ = 'current_locale', 'BabelMiddleware', 'get_translations', \
    'gettext', 'ngettext', 'pgettext', 'npgettext'


current_locale = ContextVar('locale', default=None)
BABEL = None


def select_locale_by_request(
        request: Request, default: str = 'en', locales: t.Sequence[str] = None) -> str:
    """Select a locale by the given request."""
    locale_header = request.headers.get('accept-language')
    if not locale_header:
        return default

    ulocales = [(q, locale_delim_re.split(v)[0]) for v, q in parse_accept_header(locale_header)]

    if not ulocales:
        return default

    return ulocales[0][1]


@dataclass(eq=False, order=False)
class BabelMiddleware(BaseMiddeware):
    """Support i18n."""

    app: ASGIApp
    default_locale: str = 'en'
    domain: str = 'messages'
    locales_dirs: t.List[str] = field(default_factory=lambda: ['locales'])
    locale_selector_fn: t.Callable = field(repr=False, default=select_locale_by_request)

    translations: t.Dict[t.Tuple[str, str], support.Translations] = field(
        init=False, repr=False, default_factory=lambda: {})

    def __post_init__(self):
        global BABEL
        BABEL = self

    async def __process__(self, scope: Scope, receive: Receive, send: Send):
        """Load/save the sessions."""
        if isinstance(scope, Request):
            request = scope
        else:
            request = scope.get('request') or Request(scope)

        locale = Locale.parse(self.locale_selector_fn(request))
        current_locale.set(locale)

        return await self.app(scope, receive, send)  # type: ignore

    def locale_selector(self, fn: t.Callable[[Request, str], str]) -> t.Callable:
        """Define locale selector."""
        self.locale_selector_fn = fn  # type: ignore
        return fn


def get_translations(domain: str = None, locale: Locale = None) -> support.Translations:
    """Load and cache translations."""
    if BABEL is None:
        raise RuntimeError('BabelMiddleware is not inited.')

    locale = locale or current_locale.get()
    if not locale:
        return support.NullTranslations()

    domain = domain or BABEL.domain
    if (domain, locale.language) not in BABEL.translations:
        translations = None
        for path in reversed(BABEL.locales_dirs):
            trans = support.Translations.load(path, locales=locale, domain=domain)
            if translations:
                translations._catalog.update(trans._catalog)
            else:
                translations = trans

        BABEL.translations[(domain, locale.language)] = translations

    return BABEL.translations[(domain, locale.language)]


def gettext(string, domain=None, **variables):
    """Translate a string with the current locale."""
    t = get_translations(domain)
    return t.ugettext(string) % variables


def ngettext(singular, plural, num, domain=None, **variables):
    """Translate a string wity the current locale.

    The `num` parameter is used to dispatch between singular and various plural forms of the
    message.

    """
    variables.setdefault('num', num)
    t = get_translations(domain)
    return t.ungettext(singular, plural, num) % variables


def pgettext(context, string, domain=None, **variables):
    """Like :meth:`gettext` but with a context."""
    t = get_translations(domain)
    return t.upgettext(context, string) % variables


def npgettext(context, singular, plural, num, domain=None, **variables):
    """Like :meth:`ngettext` but with a context."""
    variables.setdefault('num', num)
    t = get_translations(domain)
    return t.unpgettext(context, singular, plural, num) % variables


def parse_accept_header(header: str) -> t.Iterator[t.Tuple[str, float]]:
    """Parse accept headers."""
    result = []
    for match in accept_re.finditer(header):
        quality = 1.0
        if match.group(2):
            quality = max(min(float(match.group(2)), 1), 0)
        result.append((match.group(1), quality))

    return reversed(sorted(result))


locale_delim_re = re.compile(r'[_-]')
accept_re = re.compile(
    r'''(                         # media-range capturing-parenthesis
            [^\s;,]+              # type/subtype
            (?:[ \t]*;[ \t]*      # ";"
            (?:                   # parameter non-capturing-parenthesis
                [^\s;,q][^\s;,]*  # token that doesn't start with "q"
            |                     # or
                q[^\s;,=][^\s;,]* # token that is more than just "q"
            )
            )*                    # zero or more parameters
        )                         # end of media-range
        (?:[ \t]*;[ \t]*q=        # weight is a "q" parameter
            (\d*(?:\.\d+)?)       # qvalue capturing-parentheses
            [^,]*                 # "extension" accept params: who cares?
        )?                        # accept params are optional
    ''', re.VERBOSE)
