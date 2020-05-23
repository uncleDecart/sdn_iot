import os

from webob.static import DirectoryApp

from ryu.app.wsgi import ControllerBase, WSGIApplication, route
from ryu.base import app_manager

import mysql.connector

from rest import Dispatcher
import bottle
from bottle import response

class EnableCors(object):
  name = 'enable_cors'
  api = 2

  def apply(self, fn, context):
    def _enable_cors(*args, **kwargs):
      # set CORS headers
      response.headers['Access-Control-Allow-Origin'] = '*'
      response.headers['Access-Control-Allow-Methods'] = 'GET, POST, DELETE, PUT, OPTIONS'
      response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'

      if bottle.request.method != 'OPTIONS':
        # actual request; reply with the actual response
        return fn(*args, **kwargs)

    return _enable_cors

root = Dispatcher()
root.install(EnableCors())
bottle.debug(True)
bottle.install(EnableCors())
bottle.run(app=root, host='0.0.0.0', port=5556)

