from asgi_tools import ResponseRedirect, App
from asgi_sessions import SessionMiddleware


app = App()


@app.route('/login')
async def login(request):
    data = await request.form()
    request.session['user'] = data.get('user')
    return ResponseRedirect('/')


@app.route('/logout')
async def logout(request):
    request.session.pop('user', None)
    return ResponseRedirect('/')


@app.route('/')
async def index(request, *args):
    user = request.session.get('user')
    return f"""
    <link rel="stylesheet"
          href="https://cdn.jsdelivr.net/npm/bootstrap@4.5.3/dist/css/bootstrap.min.css">
    <div class="container p-3">
        <p class="lead">
            A simple example to show how <span class="font-weight-bold">ASGI-Sessions</span> works.
            <br/>
            Store/erase an username in the secured cookies session.
        </p>
        <h2>Hello {user or 'anonymous'}</h2>
        <form action="/login" method="post">
            <div class="form-group">
                <label for="user">Login as</label>
                <input name="user" placeholder="username (enter)"
                    value="{ user or '' }" { user and 'disabled' } />
            </div>
            <button type="submit"
                class="btn btn-primary" { user and 'disabled'}>Login</button>
            <button onclick="window.location='/logout'" type="button"
                    class="btn btn-danger" { user or 'disabled="disabled"' }">Logout</button>
        </form>
    </div>
"""

app = SessionMiddleware(app, secret_key='SESSION-SECRET')
