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

import json as _json
import json.decoder as _json_decoder
import logging as _logging
import os as _os
import starlette.requests as _requests
import starlette.responses as _responses
import starlette.routing as _routing
import starlette.staticfiles as _staticfiles
import uuid as _uuid
import uvicorn as _uvicorn

from .model import BadDataError

_log = _logging.getLogger("httpserver")

class HttpServer:
    def __init__(self, app, host="", port=8080):
        self.app = app
        self.host = host
        self.port = port

        static_dir = _os.path.join(self.app.home, "static")

        routes = [
            _routing.Route("/api/data",
                           endpoint=ModelHandler, methods=["GET", "HEAD"]),
            _routing.Route("/api/repos/{repo_id}",
                           endpoint=RepoHandler, methods=["PUT", "DELETE", "GET", "HEAD"]),
            _routing.Route("/api/repos/{repo_id}/branches/{branch_id}",
                           endpoint=BranchHandler, methods=["PUT", "DELETE", "GET", "HEAD"]),
            _routing.Route("/api/repos/{repo_id}/branches/{branch_id}/tags/{tag_id}",
                           endpoint=TagHandler, methods=["PUT", "DELETE", "GET", "HEAD"]),
            _routing.Route("/api/repos/{repo_id}/branches/{branch_id}/tags/{tag_id}/artifacts/{artifact_id}",
                           endpoint=ArtifactHandler, methods=["PUT", "DELETE", "GET", "HEAD"]),
            _routing.Route("/", endpoint=WebAppHandler, methods=["GET", "HEAD"]),
            _routing.Route("/tags/{repo_id}/{branch_id}/{tag_id}", endpoint=WebAppHandler, methods=["GET", "HEAD"]),
            _routing.Mount("", app=_staticfiles.StaticFiles(directory=static_dir)),
        ]

        self.router = Router(self.app, routes)

    def run(self):
        _uvicorn.run(self.router, host=self.host, port=self.port, log_level="info")

class Router(_routing.Router):
    def __init__(self, app, routes):
        super().__init__(routes)
        self.app = app

    def __call__(self, scope):
        scope["app"] = self.app
        return super().__call__(scope)

class NotFoundResponse(_responses.PlainTextResponse):
    def __init__(self, exception):
        super().__init__(f"Not found: {exception}\n", 404)

class NotModifiedResponse(_responses.PlainTextResponse):
    def __init__(self):
        super().__init__("Not modified\n", 304)

class BadJsonResponse(_responses.PlainTextResponse):
    def __init__(self, exception):
        super().__init__(f"Bad request: Failure decoding JSON: {exception}\n", 400)

class BadDataResponse(_responses.PlainTextResponse):
    def __init__(self, exception):
        super().__init__(f"Bad request: Illegal data: {exception}\n", 400)

class OkResponse(_responses.Response):
    def __init__(self):
        super().__init__("OK\n")

class CompressedJsonResponse(_responses.Response):
    def __init__(self, content):
        super().__init__(content, headers={"Content-Encoding": "gzip"}, media_type="application/json")

class AsgiHandler:
    def __init__(self, scope):
        self.scope = scope

    async def __call__(self, receive, send):
        request = _requests.Request(self.scope, receive)
        request.app = request["app"]
        error = None

        try:
            obj, response = await self.process(request)
        except KeyError as e:
            error = NotFoundResponse(e)
        except BadDataError as e:
            error = BadDataResponse(e)
        except _json_decoder.JSONDecodeError as e:
            error = BadJsonResponse(e)

        if error is not None:
            return await error(receive, send)

        server_etag = self.etag(request, obj)
        client_etag = request.headers.get("If-None-Match")

        if server_etag is not None and client_etag == server_etag:
            response = NotModifiedResponse()
        elif request.method == "HEAD":
            response = _responses.Response("")
        elif response is None:
            response = await self.render(request, obj)

        assert response is not None

        if server_etag is not None:
            response.headers["ETag"] = server_etag

        await response(receive, send)

    async def process(self, request):
        return None, None

    def etag(self, request, obj):
        pass

    async def render(self, request, obj):
        pass

class WebAppHandler(AsgiHandler):
    _etag = f'"{str(_uuid.uuid4())}"'

    def etag(self, request, obj):
        return self._etag

    async def render(self, request, obj):
        return _responses.FileResponse(path=_os.path.join(request.app.home, "static", "index.html"))

class ModelHandler(AsgiHandler):
    def etag(self, request, obj):
        return f'"{str(request.app.model.revision)}"'

    async def render(self, request, obj):
        accept_encoding = request.headers.get("Accept-Encoding")

        if accept_encoding is not None and "gzip" in accept_encoding:
            return CompressedJsonResponse(request.app.model._compressed_data)
        else:
            return _responses.JSONResponse(request.app.model.data())

class ModelObjectHandler(AsgiHandler):
    def etag(self, request, obj):
        if obj is not None:
            return f'"{str(obj._digest)}"'

    async def render(self, request, obj):
        assert obj is not None

        accept_encoding = request.headers.get("Accept-Encoding")

        if accept_encoding is not None and "gzip" in accept_encoding:
            return CompressedJsonResponse(obj._compressed_data)
        else:
            return _responses.JSONResponse(obj.data())

class RepoHandler(ModelObjectHandler):
    async def process(self, request):
        model = request.app.model
        repo_id = request.path_params["repo_id"]

        if request.method == "PUT":
            repo_data = await request.json()
            repo = model.put_repo(repo_id, repo_data)
            return repo, OkResponse()

        if request.method == "DELETE":
            model.delete_repo(repo_id)
            return None, OkResponse()

        return model.repos[repo_id], None

class BranchHandler(ModelObjectHandler):
    async def process(self, request):
        model = request.app.model
        repo_id = request.path_params["repo_id"]
        branch_id = request.path_params["branch_id"]

        if request.method == "PUT":
            branch_data = await request.json()
            branch = model.put_branch(repo_id, branch_id, branch_data)
            return branch, OkResponse()

        if request.method == "DELETE":
            model.delete_branch(repo_id, branch_id)
            return None, OkResponse()

        return model.repos[repo_id].branches[branch_id], None

class TagHandler(ModelObjectHandler):
    async def process(self, request):
        model = request.app.model
        repo_id = request.path_params["repo_id"]
        branch_id = request.path_params["branch_id"]
        tag_id = request.path_params["tag_id"]

        if request.method == "PUT":
            tag_data = await request.json()
            tag = model.put_tag(repo_id, branch_id, tag_id, tag_data)
            return tag, OkResponse()

        if request.method == "DELETE":
            model.delete_tag(repo_id, branch_id, tag_id)
            return None, OkResponse()

        return model.repos[repo_id].branches[branch_id].tags[tag_id], None

class ArtifactHandler(ModelObjectHandler):
    async def process(self, request):
        model = request.app.model
        repo_id = request.path_params["repo_id"]
        branch_id = request.path_params["branch_id"]
        tag_id = request.path_params["tag_id"]
        artifact_id = request.path_params["artifact_id"]

        if request.method == "PUT":
            artifact_data = await request.json()
            artifact = model.put_artifact(repo_id, branch_id, tag_id, artifact_id, artifact_data)
            return artifact, OkResponse()

        if request.method == "DELETE":
            model.delete_artifact(repo_id, branch_id, tag_id, artifact_id)
            return None, OkResponse()

        return model.repos[repo_id].branches[branch_id].tags[tag_id].artifacts[artifact_id], None
