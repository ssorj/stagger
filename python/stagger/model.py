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
                repo = Repo(self, repo_id, None, **repo_data)
                self.repos[repo_id] = repo

            self.revision = data["revision"]

    def start(self):
        self._save_thread.start()

    def mark_modified(self):
        self.revision += 1
        self._modified.set()

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
            assert isinstance(repo, Repo), repo
            repos[repo_id] = repo.data()

        return {
            "repos": repos,
            "revision": self.revision,
        }

    def json(self):
        return _json.dumps(self.data(), sort_keys=True)

    def put_repo(self, repo_id, repo_data):
        with self._lock:
            repo = Repo(self, repo_id, None, **repo_data)
            self.repos[repo_id] = repo
            repo.mark_modified()

    def delete_repo(self, repo_id):
        with self._lock:
            del self.repos[repo_id]
            self.mark_modified()

    def put_branch(self, repo_id, branch_id, branch_data):
        with self._lock:
            repo = self.repos.get(repo_id)

            if repo is None:
                repo = Repo(self, repo_id, None)
                self.repos[repo_id] = repo

            branch = Branch(self, branch_id, repo, **branch_data)
            repo.branches[branch_id] = branch

            branch.mark_modified()

    def delete_branch(self, repo_id, branch_id):
        with self._lock:
            repo = self.repos[repo_id]
            del repo.branches[branch_id]
            repo.mark_modified()

    def put_tag(self, repo_id, branch_id, tag_id, tag_data):
        with self._lock:
            repo = self.repos.get(repo_id)

            if repo is None:
                repo = Repo(self, repo_id, None)
                self.repos[repo_id] = repo

            branch = repo.branches.get(branch_id)

            if branch is None:
                branch = Branch(self, branch_id, repo)
                repo.branches[branch_id] = branch

            tag = Tag(self, tag_id, branch, **tag_data)
            branch.tags[tag_id] = tag

            tag.mark_modified()

    def delete_tag(self, repo_id, branch_id, tag_id):
        with self._lock:
            repo = self.repos[repo_id]
            branch = repo.branches[branch_id]

            del branch.tags[tag_id]

            branch.mark_modified()

    def put_artifact(self, repo_id, branch_id, tag_id, artifact_id, artifact_data):
        with self._lock:
            repo = self.repos.get(repo_id)

            if repo is None:
                repo = Repo(self, repo_id, None)
                self.repos[repo_id] = repos

            branch = repo.branches.get(branch_id)

            if branch is None:
                branch = Branch(self, branch_id)
                self.branches[branch_id] = branch

            tag = branch.tags.get(tag_id)

            if tag is None:
                tag = Tag(self, tag_id, repo)
                branch.tags[tag_id] = tag

            artifact = Artifact.create(self, artifact_id, tag, **artifact_data)
            tag.artifacts[artifact_id] = artifact

            artifact.mark_modified()

    def delete_artifact(self, repo_id, branch_id, tag_id, artifact_id):
        with self._lock:
            repo = self.repos[repo_id]
            branch = repo.branches[branch_id]
            tag = branch.tags[tag_id]

            del tag.artifacts[artifact_id]

            tag.mark_modified()

class BadDataError(Exception):
    pass

class ModelObject:
    _fields = []
    _required_fields = []
    _child_fields = []

    def __init__(self, model, id, parent, **fields):
        self._model = model
        self._id = id
        self._parent = parent
        self._digest = None

        missing = list()

        for name in self._required_fields:
            if name not in fields or fields[name] is None:
                missing.append(name)

        if missing:
            raise BadDataError(f"{self} is missing required values: {', '.join(missing)}")

        for name in self._fields:
            if name in self._child_fields:
                continue

            setattr(self, name, fields.get(name, None))

        self._init_children(**fields)
        self._compute_digest()

    def _init_children(self, **fields):
        pass

    def __repr__(self):
        return f"{self.__class__.__name__}({self.path})"

    @property
    def path(self):
        return self._path_template.format(parent_path=self._parent.path, id=self._id)

    def data(self):
        fields = dict()

        for name, value in vars(self).items():
            if name.startswith("_"):
                continue

            if name in self._child_fields:
                value = self._child_data(value)

            fields[name] = value

        return fields

    def _child_data(self, children):
        data = dict()

        for child_id, child in children.items():
            data[child_id] = child.data()

        return data

    def json(self):
        return _json.dumps(self.data(), sort_keys=True)

    def mark_modified(self):
        self._mark_modified()
        self._model.mark_modified()

    def _mark_modified(self):
        self._compute_digest()
        self._model.app.amqp_server.fire_object_update(self)

        if self._parent is not None:
            self._parent._mark_modified()

    def _compute_digest(self):
        self._digest = _binascii.crc32(self.json().encode("utf-8"))

class Repo(ModelObject):
    _fields = ["source_url", "job_url", "branches"]
    _child_fields = ["branches"]

    def _init_children(self, **fields):
        self.branches = dict()

        for branch_id, branch_data in fields.get("branches", {}).items():
            branch = Branch(self._model, branch_id, self, **branch_data)
            self.branches[branch_id] = branch

    @property
    def path(self):
        return f"repos/{self._id}"

class Branch(ModelObject):
    _path_template = "{parent_path}/branches/{id}"
    _fields = ["tags"]
    _child_fields = ["tags"]

    def _init_children(self, **fields):
        self.tags = dict()

        for tag_id, tag_data in fields.get("tags", {}).items():
            tag = Tag(self._model, tag_id, self, **tag_data)
            self.tags[tag_id] = tag

class Tag(ModelObject):
    _path_template = "{parent_path}/tags/{id}"
    _fields = ["build_id", "build_url", "commit_id", "commit_url", "artifacts"]
    _required_fields = ["build_id"]
    _child_fields = ["artifacts"]

    def _init_children(self, **fields):
        self.artifacts = dict()

        for artifact_id, artifact_data in fields.get("artifacts", {}).items():
            artifact = Artifact.create(self._model, artifact_id, self, **artifact_data)
            self.artifacts[artifact_id] = artifact

class Artifact(ModelObject):
    _path_template = "{parent_path}/artifacts/{id}"

    @staticmethod
    def create(model, id, parent, **artifact_data):
        try:
            type = artifact_data["type"]
        except KeyError:
            raise BadDataError("Artifact data has no type field")

        cls = Artifact._subclasses_by_type[type]
        obj = cls(model, id, parent, **artifact_data)

        return obj

class ContainerArtifact(Artifact):
    _fields = ["type", "registry_url", "repository", "image_id"]
    _required_fields = _fields

class MavenArtifact(Artifact):
    _fields = ["type", "repository_url", "group_id", "artifact_id", "version"]
    _required_fields = _fields

class FileArtifact(Artifact):
    _fields = ["type", "url"]
    _required_fields = _fields

class RpmArtifact(Artifact):
    _fields = ["type", "repository_url", "name", "version", "release"]
    _required_fields = _fields

Artifact._subclasses_by_type = {
    "container": ContainerArtifact,
    "maven": MavenArtifact,
    "file": FileArtifact,
    "rpm": RpmArtifact,
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
            except KeyboardInterrupt:
                raise
            except Exception:
                _traceback.print_exc()
            finally:
                self.model._modified.clear()
