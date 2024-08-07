"""Support cookie-encrypted sessions for ASGI applications."""

from __future__ import annotations

import re
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Awaitable, Callable, Optional, Union

from asgi_tools import Request
from asgi_tools.middleware import BaseMiddeware
from babel import Locale, support

if TYPE_CHECKING:
    from asgi_tools.types import TASGIApp, TASGIReceive, TASGIScope, TASGISend


__all__ = (
    "current_locale",
    "BabelMiddleware",
    "get_translations",
    "gettext",
    "ngettext",
    "pgettext",
    "npgettext",
)


current_locale = ContextVar[Optional[Locale]]("locale", default=None)
BABEL = None


class BabelMiddlewareError(RuntimeError):
    """Base class for BabelMiddleware errors."""


async def select_locale_by_request(request: Request) -> Optional[str]:
    """Select a locale by the given request."""
    locale_header = request.headers.get("accept-language")
    if locale_header:
        ulocales = list(parse_accept_header(locale_header))
        if ulocales:
            return ulocales[0][1]

    return None


@dataclass(eq=False, order=False)
class BabelMiddleware(BaseMiddeware):
    """Support i18n."""

    app: TASGIApp
    default_locale: str = "en"
    domain: str = "messages"
    locales_dirs: list[str] = field(default_factory=lambda: ["locales"])
    locale_selector: Callable[[Request], Awaitable[Optional[str]]] = field(
        repr=False,
        default=select_locale_by_request,
    )

    translations: dict[tuple[str, str], support.Translations] = field(
        init=False,
        repr=False,
        default_factory=dict,
    )

    def __post_init__(self):
        global BABEL  # noqa:PLW0603
        BABEL = self

    async def __process__(
        self,
        scope: TASGIScope,
        receive: TASGIReceive,
        send: TASGISend,
    ):
        """Load/save the sessions."""
        if isinstance(scope, Request):
            request = scope
        else:
            request = scope.get("request") or Request(scope, receive, send)

        lang = await self.locale_selector(request) or self.default_locale
        locale = Locale.parse(lang, sep="-")
        current_locale.set(locale)

        return await self.app(scope, receive, send)


def get_translations(
    domain: Optional[str] = None,
    locale: Optional[Locale] = None,
) -> Union[support.Translations, support.NullTranslations]:
    """Load and cache translations."""
    if BABEL is None:
        raise BabelMiddlewareError

    locale = locale or current_locale.get()
    if locale is None:
        return support.NullTranslations()

    domain = domain or BABEL.domain
    if (domain, locale.language) not in BABEL.translations:
        translations = None
        for path in reversed(BABEL.locales_dirs):
            trans = support.Translations.load(path, locales=str(locale), domain=domain)
            if translations:
                translations._catalog.update(trans._catalog)
            else:
                translations = trans

        BABEL.translations[(domain, locale.language)] = translations

    return BABEL.translations[(domain, locale.language)]


def gettext(string: str, domain: Optional[str] = None, **variables):
    """Translate a string with the current locale."""
    t = get_translations(domain)
    return t.ugettext(string) % variables


def ngettext(
    singular: str,
    plural: str,
    num: int,
    domain: Optional[str] = None,
    **variables,
):
    """Translate a string wity the current locale.

    The `num` parameter is used to dispatch between singular and various plural forms of the
    message.

    """
    variables.setdefault("num", num)
    t = get_translations(domain)
    return t.ungettext(singular, plural, num) % variables


def pgettext(context: str, string: str, domain: Optional[str] = None, **variables):
    """Like :meth:`gettext` but with a context."""
    t = get_translations(domain)
    return t.upgettext(context, string) % variables


def npgettext(
    context: str,
    singular: str,
    plural: str,
    num: int,
    domain: Optional[str] = None,
    **variables,
):
    """Like :meth:`ngettext` but with a context."""
    variables.setdefault("num", num)
    t = get_translations(domain)
    return t.unpgettext(context, singular, plural, num) % variables


def parse_accept_header(header: str) -> list[tuple[float, str]]:
    """Parse accept headers."""
    result = []
    for match in accept_re.finditer(header):
        quality = 1.0
        try:
            if match.group(2):
                quality = max(min(float(match.group(2)), 1), 0)
            if match.group(1) == "*":
                continue
        except ValueError:
            continue
        result.append((quality, match.group(1)))

    return sorted(result, reverse=True)


locale_delim_re = re.compile(r"[_-]")
accept_re = re.compile(
    r"""(                         # media-range capturing-parenthesis
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
    """,
    re.VERBOSE,
)
