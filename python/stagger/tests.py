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

from commandant import TestSkipped
from fortworth import *

container_artifact_data = {
    "type": "container",
    "registry_url": "https://registry.example.com/",
    "repository": "example-app",
    "image_id": "1.0.0-999"
}

file_artifact_data = {
    "type": "file",
    "url": "https://files.example.com/example-app/master/999/example-app-1.0.0-999.tar.gz",
}

maven_artifact_data = {
    "type": "maven",
    "group_id": "com.example",
    "artifact_id": "example-app",
    "version": "1.0.0-999",
    "repository_url": "https://files.example.com/example-app/master/999/maven-repo",
}

rpm_artifact_data = {
    "type": "rpm",
    "repository_url": "https://files.example.com/example-app/master/999/yum-repo",
    "name": "example-app",
    "version": "1.0.0",
    "release": "999",
}

tag_data = {
    "build_id": "999",
    "build_url": "https://ci.example.com/example-app-dist/999",
    "commit_id": "f4fe336a8b9a3dc171ae4e023d8cb702ee35ebf7",
    "commit_url": "https://scm.example.com/example-app-dist/f4fe336a8b9a3dc171ae4e023d8cb702ee35ebf7",
    "artifacts": {
        "example-app.tar.gz": file_artifact_data,
        "example-app-maven": maven_artifact_data,
        "example-app-rpm": rpm_artifact_data,
    },
}

branch_data = {
    "tags": {
        "tested": tag_data,
    },
}

repo_data = {
    "example-app-dist": {
        "source_url": "https://scm.example.com/example-app-dist",
        "job_url": "https://ci.exmaple.com/example-app-dist",
        "branches": {
            "master": branch_data,
        },
    },
}

def open_test_session(session):
    enable_logging(level="error")
    session.test_timeout = 10

def test_api_repo(session):
    _test_api_curl(session, "repos/example-app-dist", repo_data)

def test_api_branch(session):
    _test_api_curl(session, "repos/example-app-dist/branches/master", branch_data)

def test_api_tag(session):
    with TestServer() as server:
        stagger_put_tag("example-app-dist", "master", "tested", tag_data, service_url=server.http_url)
        stagger_get_tag("example-app-dist", "master", "tested", service_url=server.http_url)

    _test_api_curl(session, "repos/example-app-dist/branches/master/tags/tested", tag_data)

def test_api_artifact_container(session):
    _test_api_artifact(session, "example-app-dist", "master", "tested", "example-app-container", container_artifact_data)

def test_api_artifact_file(session):
    _test_api_artifact(session, "example-app-dist", "master", "tested", "example-app.tar.gz", file_artifact_data)

def test_api_artifact_maven(session):
    _test_api_artifact(session, "example-app-dist", "master", "tested", "example-app-maven", maven_artifact_data)

def test_api_artifact_rpm(session):
    _test_api_artifact(session, "example-app-dist", "master", "tested", "example-app-rpm", rpm_artifact_data)

def _test_api_curl(session, path, data):
    with TestServer() as server:
        url = f"{server.http_url}/api/{path}"

        try:
            head(url)
            assert False, "Expected this to 404"
        except CalledProcessError:
            pass

        put(url, data)
        get(url)
        head(url)
        delete(url)

def _test_api_artifact(session, repo, branch, tag, artifact, artifact_data):
    with TestServer() as server:
        stagger_put_artifact(repo, branch, tag, artifact, artifact_data, service_url=server.http_url)
        stagger_get_artifact(repo, branch, tag, artifact, service_url=server.http_url)

    _test_api_curl(session, f"repos/{repo}/branches/{branch}/tags/{tag}/artifacts/{artifact}", artifact_data)

def test_events_repo(session):
    _test_events(session, "repos/example-app-dist", repo_data)

def test_events_branch(session):
    _test_events(session, "repos/example-app-dist/branches/master", branch_data)

def test_events_tag(session):
    _test_events(session, "repos/example-app-dist/branches/master/tags/tested", tag_data)

def test_events_artifact_container(session):
    _test_events(session, "repos/example-app-dist/branches/master/tags/tested/artifacts/example-app-container", container_artifact_data)

def test_events_artifact_file(session):
    _test_events(session, "repos/example-app-dist/branches/master/tags/tested/artifacts/example-app.tar.gz", file_artifact_data)

def test_events_artifact_maven(session):
    _test_events(session, "repos/example-app-dist/branches/master/tags/tested/artifacts/example-app-maven", maven_artifact_data)

def test_events_artifact_rpm(session):
    _test_events(session, "repos/example-app-dist/branches/master/tags/tested/artifacts/example-app-rpm", rpm_artifact_data)

def _test_events(session, path, data):
    if which("qreceive") is None:
        raise TestSkipped("qreceive is not available")

    with TestServer() as server:
        events_url = f"{server.amqp_url}/events/{path}"
        api_url = f"{server.http_url}/api/{path}"

        put(api_url, data)

        with receive(events_url, 1) as proc:
            sleep(0.2)
            put(api_url, data)
            check_process(proc)

curl_options = "--fail -o /dev/null -s -w '%{http_code} (%{size_download})\\n' -H 'Content-Type: application/json' -H 'Expect:'"

def put(url, data):
    with temp_file() as data_file:
        write_json(data_file, data)
        print(f"PUT {url} -> ", end="", flush=True)
        call("curl -X PUT {} --data @{} {}", url, data_file, curl_options)

def get(url):
    print(f"GET {url} -> ", end="", flush=True)
    call("curl {} {}", url, curl_options)

def head(url):
    print(f"HEAD {url} -> ", end="", flush=True)
    call("curl --head {} {}", url, curl_options)

def delete(url):
    print(f"DELETE {url} -> ", end="", flush=True)
    call("curl -X DELETE {} {}", url, curl_options)

def receive(url, count):
    return start_process("qreceive --count {} {}", count, url)

class TestServer(object):
    def __init__(self):
        http_port = random_port()
        amqp_port = random_port()
        data_dir = make_temp_dir()

        with working_env(STAGGER_HTTP_PORT_=http_port, STAGGER_AMQP_PORT_=amqp_port, STAGGER_DATA_DIR=data_dir):
            self.proc = start_process("stagger")

        self.proc.http_url = f"http://localhost:{http_port}"
        self.proc.amqp_url = f"amqp://127.0.0.1:{amqp_port}"

    def __enter__(self):
        sleep(0.2);
        return self.proc

    def __exit__(self, exc_type, exc_value, traceback):
        stop_process(self.proc)
