#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#

import json.decoder as _json_decoder
import logging as _logging
import os as _os
import starlette.requests as _requests
import starlette.routing as _routing
import starlette.staticfiles as _staticfiles
import uuid as _uuid
import uvicorn as _uvicorn

from starlette.responses import *

_log = _logging.getLogger("brbn")

class Server:
    def __init__(self, app, host="", port=8080):
        self.app = app
        self.host = host
        self.port = port

        self.router = Router(self.app)

    def add_route(self, *args, **kwargs):
        self.router.add_route(*args, **kwargs)

    def add_static_files(self, path, dir):
        self.router.mount(path, app=_staticfiles.StaticFiles(directory=dir))

    def run(self):
        _uvicorn.run(self.router, host=self.host, port=self.port, log_level="info")

class Router(_routing.Router):
    def __init__(self, app):
        super().__init__()
        self.app = app

    def __call__(self, scope):
        scope["app"] = self.app
        return super().__call__(scope)

class Request(_requests.Request):
    @property
    def app(self):
        return self["app"]

class Handler:
    def __init__(self, scope):
        self.scope = scope

    async def __call__(self, receive, send):
        request = Request(self.scope, receive)

        try:
            obj = await self.process(request)
        except Redirect as e:
            return await RedirectResponse(str(e))
        except _json_decoder.JSONDecodeError as e:
            return await BadJsonResponse(e)
        except Exception as e:
            return await ServerErrorResponse(e)

        server_etag = f'"{self.etag(request, obj)}"'
        client_etag = request.headers.get("If-None-Match")

        if server_etag is not None and client_etag == server_etag:
            response = NotModifiedResponse()
        elif request.method == "HEAD":
            response = Response("")
        else:
            response = await self.render(request, obj)
            assert response is not None

        if server_etag is not None:
            response.headers["ETag"] = server_etag

        await response(receive, send)

    async def process(self, request):
        return None # obj

    def etag(self, request, obj):
        pass

    async def render(self, request, obj):
        pass

class Redirect(Exception):
    pass

class NotFoundResponse(PlainTextResponse):
    def __init__(self, exception):
        super().__init__(f"Not found: {exception}\n", 404)

class NotModifiedResponse(PlainTextResponse):
    def __init__(self):
        super().__init__("Not modified\n", 304)

class ServerErrorResponse(PlainTextResponse):
    def __init__(self, exception):
        super().__init__(f"Internal server error: {exception}\n", 500)

class BadJsonResponse(PlainTextResponse):
    def __init__(self, exception):
        super().__init__(f"Bad request: Failure decoding JSON: {exception}\n", 400)

class OkResponse(Response):
    def __init__(self):
        super().__init__("OK\n")

class JsonResponse(JSONResponse):
    pass

class CompressedJsonResponse(Response):
    def __init__(self, content):
        super().__init__(content, headers={"Content-Encoding": "gzip"}, media_type="application/json")
