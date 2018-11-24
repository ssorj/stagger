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

import binascii as _binascii
import json as _json
import logging as _logging
import os as _os
import threading as _threading
import traceback as _traceback

_log = _logging.getLogger("model")

class Model:
    def __init__(self, app, data_file):
        self.app = app
        self.data_file = data_file

        self.repos = dict()
        self.revision = 0

        self._lock = _threading.Lock()
        self._modified = _threading.Event()
        self._save_thread = _SaveThread(self)

    def load(self):
        if not _os.path.exists(self.data_file):
            return

        with open(self.data_file, "r") as f:
            data = _json.load(f)

            assert "repos" in data, "No repos field in data"
            assert "revision" in data, "No revision field in data"

            for repo_id, repo_data in data["repos"].items():
                _Repo(self, repo_id, **repo_data)

            self.revision = data["revision"]

    def start(self):
        self._save_thread.start()

    def save(self):
        with self._lock:
            temp = f"{self.data_file}.temp"
            data = self.data()

            with open(temp, "w") as f:
                _json.dump(data, f, sort_keys=True)

            _os.rename(temp, self.data_file)

    def data(self):
        repos = dict()

        for repo_id, repo in self.repos.items():
            assert isinstance(repo, _Repo), repo
            repos[repo_id] = repo.data()

        return {
            "repos": repos,
            "revision": self.revision,
        }

    def json(self):
        return _json.dumps(self.data(), sort_keys=True)

    def put_repo(self, repo_id, repo_data):
        with self._lock:
            repo = _Repo(self, repo_id, **repo_data)
            self.repos[repo_id] = repo
            self.revision += 1

        self.app.amqp_server.fire_repo_update(repo)
        self._modified.set()

    def delete_repo(self, repo_id):
        with self._lock:
            del self.repos[repo_id]
            self.revision += 1

        self._modified.set()

    def put_tag(self, repo_id, tag_id, tag_data):
        with self._lock:
            repo = self.repos.get(repo_id)

            if repo is None:
                repo = _Repo(self, repo_id)
                self.repos[repo_id] = repo

            tag = _Tag(self, repo, tag_id, **tag_data)
            repo.tags[tag_id] = tag

            repo._compute_digest()
            self.revision += 1

        self.app.amqp_server.fire_tag_update(tag)
        self.app.amqp_server.fire_repo_update(repo)

        self._modified.set()

    def delete_tag(self, repo_id, tag_id):
        with self._lock:
            repo = self.repos[repo_id]

            del repo.tags[tag_id]

            repo._compute_digest()
            self.revision += 1

        self._modified.set()

    def put_artifact(self, repo_id, tag_id, artifact_id, artifact_data):
        with self._lock:
            repo = self.repos.get(repo_id)

            if repo is None:
                repo = _Repo(self, repo_id)
                self.repos[repo_id] = repos

            tag = repo.tags.get(tag_id)

            if tag is None:
                tag = _Tag(self, repo, tag_id)
                repo.tags[tag_id] = tag

            artifact = _Artifact.create(self, tag, artifact_id, **artifact_data)
            tag.artifacts[artifact_id] = artifact

            tag._compute_digest()
            repo._compute_digest()
            self.revision += 1

        self.app.amqp_server.fire_artifact_update(artifact)
        self.app.amqp_server.fire_tag_update(tag)
        self.app.amqp_server.fire_repo_update(repo)

        self._modified.set()

    def delete_artifact(self, repo_id, tag_id, artifact_id):
        with self._lock:
            repo = self.repos[repo_id]
            tag = repo.tags[tag_id]

            del tag.artifacts[artifact_id]

            tag._compute_digest()
            repo._compute_digest()
            self.revision += 1

        self._modified.set()

class DataError(Exception):
    pass

class _ModelObject:
    def __init__(self, model, id):
        self._model = model
        self._id = id
        self._digest = None

        self.path = None

    def __repr__(self):
        return f"{self.__class__.__name__}({self.path})"

    def data(self, exclude=[]):
        fields = dict()

        for name, value in vars(self).items():
            if name.startswith("_") or name in exclude:
                continue

            fields[name] = value

        return fields

    def json(self):
        return _json.dumps(self.data(), sort_keys=True)

    def _compute_digest(self):
        self._digest = _binascii.crc32(self.json().encode("utf-8"))

class _Repo(_ModelObject):
    def __init__(self, model, id, path=None, tags={}):
        super().__init__(model, id)

        self.path = path
        self.tags = dict()

        if self.path is None:
            self.path = f"repos/{self._id}"

        for tag_id, tag_data in tags.items():
            tag = _Tag(self._model, self, tag_id, **tag_data)
            self.tags[tag_id] = tag

        self._compute_digest()

    def data(self):
        fields = super().data(exclude=["tags"])
        fields["tags"] = tags = dict()

        for tag_id, tag in self.tags.items():
            tags[tag_id] = tag.data()

        return fields

class _Tag(_ModelObject):
    def __init__(self, model, repo, id,
                 path=None, build_id=None, build_url=None, artifacts={}):
        super().__init__(model, id)

        self.repo = repo
        self.path = path
        self.build_id = build_id
        self.build_url = build_url
        self.artifacts = dict()

        if self.path is None:
            self.path = f"{self.repo.path}/tags/{self._id}"

        for artifact_id, artifact_data in artifacts.items():
            artifact = _Artifact.create(self._model, self, artifact_id, **artifact_data)
            self.artifacts[artifact_id] = artifact

        self._compute_digest()

    def data(self):
        fields = super().data(exclude=["repo", "artifacts"])
        fields["artifacts"] = artifacts = dict()

        for artifact_id, artifact in self.artifacts.items():
            artifacts[artifact_id] = artifact.data()

        return fields

class _Artifact(_ModelObject):
    @staticmethod
    def create(model, tag, id, **artifact_data):
        if "type" not in artifact_data:
            raise DataError("Artifact data has no type field")

        type_ = artifact_data["type"]
        cls = _Artifact._subclasses_by_type[type_]
        obj = cls(model, tag, id, **artifact_data)

        return obj

    def __init__(self, model, type, tag, id, path):
        super().__init__(model, id)

        self.tag = tag
        self.path = path
        self.type = type

        if self.path is None:
            self.path = f"{self.tag.path}/artifacts/{self._id}"

    def data(self):
        return super().data(exclude=["tag"])

class _ContainerArtifact(_Artifact):
    def __init__(self, model, tag, id,
                 type=None, path=None, registry_url=None, repository=None, image_id=None):
        super().__init__(model, type, tag, id, path)

        self.registry_url = registry_url
        self.repository = repository
        self.image_id = image_id

        self._compute_digest()

class _MavenArtifact(_Artifact):
    def __init__(self, model, tag, id,
                 type=None, path=None, repository_url=None, group_id=None, artifact_id=None,
                 version=None):
        super().__init__(model, type, tag, id, path)

        self.repository_url = repository_url
        self.group_id = group_id
        self.artifact_id = artifact_id
        self.version = version

        self._compute_digest()

class _FileArtifact(_Artifact):
    def __init__(self, model, tag, id, type=None, path=None, url=None):
        super().__init__(model, type, tag, id, path)

        self.url = url

        self._compute_digest()

class _RpmArtifact(_Artifact):
    def __init__(self, model, tag, id,
                 type=None, path=None, repository_url=None, name=None, version=None,
                 release=None):
        super().__init__(model, type, tag, id, path)

        self.repository_url = repository_url
        self.name = name
        self.version = version
        self.release = release

        self._compute_digest()

_Artifact._subclasses_by_type = {
    "container": _ContainerArtifact,
    "maven": _MavenArtifact,
    "file": _FileArtifact,
    "rpm": _RpmArtifact,
}

class _SaveThread(_threading.Thread):
    def __init__(self, model):
        super().__init__()

        self.model = model
        self.daemon = True

    def run(self):
        while self.model._modified.wait():
            try:
                self.model.save()
            except keyboardinterrupt:
                raise
            except exception:
                _traceback.print_exc()
            finally:
                self.model._modified.clear()

if __name__ == "__main__":
    model = Model(None, "misc/data.json")
    model.load()
    print(model.json())
