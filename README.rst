ASGI-Babel
###########

.. _description:

**asgi-babel** -- Adds internationalization (i18n) support to ASGI applications (Asyncio_ / Trio_ / Curio_)

.. _badges:

.. image:: https://github.com/klen/asgi-babel/workflows/tests/badge.svg
    :target: https://github.com/klen/asgi-babel/actions
    :alt: Tests Status

.. image:: https://img.shields.io/pypi/v/asgi-babel
    :target: https://pypi.org/project/asgi-babel/
    :alt: PYPI Version

.. image:: https://img.shields.io/pypi/pyversions/asgi-babel
    :target: https://pypi.org/project/asgi-babel/
    :alt: Python Versions

.. _contents:

.. contents::

.. _requirements:

Requirements
=============

- python >= 3.7

.. _installation:

Installation
=============

**asgi-babel** should be installed using pip: ::

    pip install asgi-babel


Usage
=====

Common ASGI applications:

.. code:: python

    from asgi_babel import BabelMiddleware, current_locale, gettext

    async def my_app(scope, receive, send):
        """Get a current locale."""
        locale = current_locale.get().language.encode()
        hello_world = gettext('Hello World!').encode()

        await send({"type": "http.response.start", "status": 200})
        await send({"type": "http.response.body", "body": b"Current locale is %s\n" % locale})
        await send({"type": "http.response.body", "body": hello_world})

    app = BabelMiddleware(my_app, locales_dirs=['tests/locales'])

    # http GET /
    # 
    # Current_locale is en
    # Hello World!

    # http GET / "accept-language: ft-CH, fr;q-0.9"
    # 
    # Current_locale is fr
    # Bonjour le monde!

As `ASGI-Tools`_ Internal middleware

.. code:: python

    from asgi_tools import App
    from asgi_babel import BabelMiddleware, gettext

    app = App()
    app.middleware(BabelMiddleware.setup(locales_dirs=['tests/locales']))

    @app.route('/')
    async def index(request):
        return gettext('Hello World!')

    @app.route('/locale')
    async def locale(request):
        return current_locale.get().language


Usage with Curio async library
------------------------------

The `asgi-babel` uses context variable to set current locale.  To enable the
context variables with curio you have to run Curio_ with ``contextvars``
support: 

.. code-block:: python

   from curio.task import ContextTask

   curio.run(main, taskcls=ContextTask)


Options
========

The middleware's options with default values:

.. code:: python

   from asgi_babel import BabelMiddleware

   app = BabelMiddleware(

        # Your ASGI application
        app,

        # Default locale
        default_locale='en',

        # A path to find translations
        locales_dirs=['locales']

        # A function with type: typing.Callable[[asgi_tools.Request], t.Awaitable[t.Optional[str]]]
        # which takes a request and default locale and return current locale
        locale_selector=asgi_babel.select_locale_by_request,

   )
 

How to extract & compile locales:
=================================

http://babel.pocoo.org/en/latest/messages.html

http://babel.pocoo.org/en/latest/cmdline.html

.. _bugtracker:

Bug tracker
===========

If you have any suggestions, bug reports or
annoyances please report them to the issue tracker
at https://github.com/klen/asgi-babel/issues

.. _contributing:

Contributing
============

Development of the project happens at: https://github.com/klen/asgi-babel

.. _license:

License
========

Licensed under a `MIT license`_.


.. _links:

.. _ASGI-Tools: https://github.com/klen/asgi-tools
.. _Asyncio: https://docs.python.org/3/library/asyncio.html
.. _Curio: https://curio.readthedocs.io/en/latest/
.. _MIT license: http://opensource.org/licenses/MIT
.. _Trio: https://trio.readthedocs.io/en/stable/
.. _klen: https://github.com/klen

