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

import logging as _logging

from data import *
from starlette import *
from starlette.routing import *

_log = _logging.getLogger("data")

_data = None
_not_found = Response("Not found", 404, media_type="text/plain")

@asgi_application
async def serve_tag_index(request):
    return JSONResponse(_data.tags)

@asgi_application
async def serve_tag(request):
    tag_id = request["kwargs"]["tag_id"]

    if request.method == "GET":
        try:
            tag = _data.tags[tag_id]
        except KeyError:
            return _not_found

        return JSONResponse(tag)

    if request.method == "PUT":
        try:
            tag = Tag(**await request.json())
        except DataError as e:
            return Response(f"Bad request: {e}", 400, media_type="text/plain")

        _data.put_tag(tag)

        return Response("")

    if request.method == "DELETE":
        try:
            _data.delete_tag(tag_id)
        except KeyError:
            return _not_found

        return Response("")

@asgi_application
async def serve_artifact_index(request):
    tag_id = request["kwargs"]["tag_id"]

    try:
        content = _data.tags[tag_id]["artifacts"]
    except KeyError:
        return _not_found

    return JSONResponse(content)

@asgi_application
async def serve_artifact(request):
    tag_id = request["kwargs"]["tag_id"]
    artifact_name = request["kwargs"]["artifact_name"]

    try:
        content = _data.tags[tag_id]["artifacts"][artifact_name]
    except KeyError:
        return _not_found

    return JSONResponse(content)

if __name__ == "__main__":
    router = Router([
        Path("/api/tags", app=serve_tag_index, methods=["GET"]),
        Path("/api/tags/{tag_id}", app=serve_tag, methods=["PUT", "GET", "DELETE"]),
        Path("/api/tags/{tag_id}/artifacts", app=serve_artifact_index, methods=["GET"]),
        Path("/api/tags/{tag_id}/artifacts/{artifact_name}", app=serve_artifact, methods=["GET"]),
    ])

    _data = Data("data.json")
    _data.load()
    _data.save_thread.start()

    import uvicorn
    uvicorn.run(router, "0.0.0.0", 8080, log_level="warning")
