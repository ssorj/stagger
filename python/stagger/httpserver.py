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
import uuid as _uuid

from brbn import *
from .model import BadDataError

_log = _logging.getLogger("httpserver")

class HttpServer(Server):
    def __init__(self, app, host="", port=8080):
        super().__init__(app, host=host, port=port)

        self.add_route("/api/data",
                       endpoint=ModelHandler, methods=["GET", "HEAD"])
        self.add_route("/api/repos/{repo_id}",
                       endpoint=RepoHandler, methods=["PUT", "DELETE", "GET", "HEAD"])
        self.add_route("/api/repos/{repo_id}/branches/{branch_id}",
                       endpoint=BranchHandler, methods=["PUT", "DELETE", "GET", "HEAD"])
        self.add_route("/api/repos/{repo_id}/branches/{branch_id}/tags/{tag_id}",
                       endpoint=TagHandler, methods=["PUT", "DELETE", "GET", "HEAD"])
        self.add_route("/api/repos/{repo_id}/branches/{branch_id}/tags/{tag_id}/artifacts/{artifact_id}",
                       endpoint=ArtifactHandler, methods=["PUT", "DELETE", "GET", "HEAD"])
        self.add_route("/",
                       endpoint=WebAppHandler, methods=["GET", "HEAD"])
        self.add_route("/tags/{repo_id}/{branch_id}/{tag_id}",
                       endpoint=WebAppHandler, methods=["GET", "HEAD"])
        self.add_route("/artifacts/{repo_id}/{branch_id}/{tag_id}/{artifact_id}",
                       endpoint=WebAppHandler, methods=["GET", "HEAD"])

        self.add_static_files("", _os.path.join(app.home, "static"))

class BadDataResponse(PlainTextResponse):
    def __init__(self, exception):
        super().__init__(f"Bad request: Illegal data: {exception}\n", 400)

class WebAppHandler(Handler):
    _etag = str(_uuid.uuid4())

    def etag(self, request, obj):
        return self._etag

    async def render(self, request, obj):
        return FileResponse(path=_os.path.join(request.app.home, "static", "index.html"))

class ModelHandler(Handler):
    def etag(self, request, obj):
        return str(request.app.model.revision)

    async def __call__(self, receive, send):
        try:
            return await super().__call__(receive, send)
        except KeyError as e:
            return await NotFoundResponse(e)
        except BadDataError as e:
            return await BadDataResponse(e)

    async def render(self, request, obj):
        accept_encoding = request.headers.get("Accept-Encoding")

        if accept_encoding is not None \
           and "gzip" in accept_encoding \
           and request.app.model._compressed_data is not None:
            return CompressedJsonResponse(request.app.model._compressed_data)
        else:
            return JsonResponse(request.app.model.data())

class ModelObjectHandler(Handler):
    def etag(self, request, obj):
        if obj is not None:
            return str(obj._digest)

    async def render(self, request, obj):
        if request.method in ("PUT", "DELETE"):
            return OkResponse()

        assert obj is not None

        accept_encoding = request.headers.get("Accept-Encoding")

        if accept_encoding is not None \
           and "gzip" in accept_encoding \
           and obj._compressed_data is not None:
            return CompressedJsonResponse(obj._compressed_data)
        else:
            return JsonResponse(obj.data())

class RepoHandler(ModelObjectHandler):
    async def process(self, request):
        model = request.app.model
        repo_id = request.path_params["repo_id"]

        if request.method == "PUT":
            repo_data = await request.json()
            repo = model.put_repo(repo_id, repo_data)
            return repo

        if request.method == "DELETE":
            model.delete_repo(repo_id)
            return

        return model.repos[repo_id]

class BranchHandler(ModelObjectHandler):
    async def process(self, request):
        model = request.app.model
        repo_id = request.path_params["repo_id"]
        branch_id = request.path_params["branch_id"]

        if request.method == "PUT":
            branch_data = await request.json()
            branch = model.put_branch(repo_id, branch_id, branch_data)
            return branch

        if request.method == "DELETE":
            model.delete_branch(repo_id, branch_id)
            return

        return model.repos[repo_id].branches[branch_id]

class TagHandler(ModelObjectHandler):
    async def process(self, request):
        model = request.app.model
        repo_id = request.path_params["repo_id"]
        branch_id = request.path_params["branch_id"]
        tag_id = request.path_params["tag_id"]

        if request.method == "PUT":
            tag_data = await request.json()
            tag = model.put_tag(repo_id, branch_id, tag_id, tag_data)
            return tag

        if request.method == "DELETE":
            model.delete_tag(repo_id, branch_id, tag_id)
            return

        return model.repos[repo_id].branches[branch_id].tags[tag_id]

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
            return artifact

        if request.method == "DELETE":
            model.delete_artifact(repo_id, branch_id, tag_id, artifact_id)
            return

        return model.repos[repo_id].branches[branch_id].tags[tag_id].artifacts[artifact_id]
