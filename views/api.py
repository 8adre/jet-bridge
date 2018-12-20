import json

import tornado.web

from version import VERSION


class ApiHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header('Content-Type', 'application/json')
    
    def get(self):
        self.write(json.dumps({
            'version': VERSION
        }))
