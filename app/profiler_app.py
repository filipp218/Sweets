from werkzeug.middleware.profiler import ProfilerMiddleware
from application import app


app.config['PROFILE'] = True
app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[10])
app.run(debug=True)