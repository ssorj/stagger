/*
 *
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 *
 */

"use strict";

const gesso = new Gesso();

class Stagger {
    constructor() {
        this.request = {
            path: null,
            query: {}
        };

        this.renderTime = null;
        this.data = null;

        window.addEventListener("statechange", (event) => {
            this.render();
        });

        window.addEventListener("load", (event) => {
            this.request.path = window.location.pathname;

            if (window.location.search) {
                this.request.query = gesso.parseQueryString(window.location.search);
            }

            window.history.replaceState(this.request, "", window.location.href);

            this.fetchDataPeriodically();

            //window.setInterval(() => { this.checkFreshness }, 60 * 1000);
        });

        window.addEventListener("popstate", (event) => {
            this.request = event.state;
            window.dispatchEvent(new Event("statechange"));
        });
    }

    fetchDataPeriodically() {
        gesso.fetchPeriodically("/api/data", (data) => {
            this.data = data;
            window.dispatchEvent(new Event("statechange"));
        });
    }

    createStateChangeLink(parent, href, options) {
        let elem = gesso.createLink(parent, href, options);

        elem.addEventListener("click", (event) => {
            event.preventDefault();

            this.request.path = new URL(event.target.href).pathname;
            this.fetchDataPeriodically();

            window.history.pushState(this.request, "", event.target.href);
            window.dispatchEvent(new Event("statechange"));
        });

        return elem;
    }

    createOptionalLink(parent, href, text, nullValue) {
        if (!text) {
            text = nullValue;
        }

        if (href) {
            return gesso.createLink(parent, href, text);
        } else {
            return gesso.createText(parent, text);
        }
    }

    createCommitLink(parent, href, id, nullValue) {
        if (id && id.length > 8) {
            id = id.substring(0, 7);
        }

        return this.createOptionalLink(parent, href, id, nullValue);
    }

    createField(parent, name, value) {
        let tr = gesso.createElement(parent, "tr");
        let th = gesso.createElement(tr, "th", name);
        let td = gesso.createElement(tr, "td", value);

        return [th, td];
    }

    render() {
        console.log(`Rendering ${this.request.path}`);

        this.renderTime = new Date().getTime();

        let content = gesso.createDiv(null, "#content");
        let prefix = this.request.path.split("/", 2)[1];

        switch(prefix) {
        case "tags":
            this.renderTagView(content);
            break;
        case "artifacts":
            this.renderArtifactView(content);
            break;
        default:
            this.renderMainView(content);
        }

        gesso.replaceElement($("#content"), content);
    }

    renderHeader(parent, title, navLinks) {
        let nav = gesso.createElement(parent, "nav", {"class": "context"});

        for (let [href, title] of navLinks.slice(0, -1)) {
            this.createStateChangeLink(nav, href, title);
            gesso.createText(nav, " \xa0>\xa0 ");
        }

        gesso.createText(nav, navLinks[navLinks.length - 1]);
        gesso.createElement(parent, "h1", title);
    }

    renderFooter(parent) {
        let elem = gesso.createElement(parent, "nav", {"class": "footer"});

        gesso.createLink(elem, "/docs.html", "Documentation");
    }

    renderUrlField(parent, name, url) {
        let [th, td] = this.createField(parent, name);
        gesso.createLink(td, url, url);
    }

    renderCommandField(parent, name, command) {
        let [th, td] = this.createField(parent, name);
        gesso.createElement(td, "code", command);
    }

    renderArtifactCoordinates(parent, data) {
        let coords;

        switch (data["type"]) {
        case "container":
            coords = `${data["repository"]}/${data["image_id"]}`;
            break;
        case "file":
            try {
                coords = new URL(data["url"]).pathname;
                coords = coords.substr(coords.lastIndexOf("/") + 1);
            } catch {
                coords = "-"
            }

            break;
        case "maven":
            coords = `${data["group_id"]}:${data["artifact_id"]}:${data["version"]}`;
            break;
        case "rpm":
            coords = `${data["name"]}-${data["version"]}-${data["release"]}`;
            break;
        default:
            coords = "-";
        }

        gesso.createText(parent, coords);
    }

    renderJsonData(parent, data) {
        let json = JSON.stringify(data, null, 4);
        let pre = gesso.createElement(parent, "pre", {"text": json, "class": "json"});

        if (hljs) {
            hljs.highlightBlock(pre);
        }
    }

    renderMainView(parent) {
        let repos = this.data["repos"];

        gesso.createElement(parent, "h1", "Stagger");

        let table = gesso.createElement(parent, "table");
        let thead = gesso.createElement(table, "thead");
        let tbody = gesso.createElement(table, "tbody");

        let tr = gesso.createElement(thead, "tr");
        let th;

        th = gesso.createElement(tr, "th", "Tag");
        th = gesso.createElement(tr, "th", "Build");
        th = gesso.createElement(tr, "th", "Commit");
        th = gesso.createElement(tr, "th", "Updated");

        for (let repoId of Object.keys(repos)) {
            let repo = repos[repoId];

            for (let branchId of Object.keys(repo["branches"])) {
                let branch = repo["branches"][branchId];

                for (let tagId of Object.keys(branch["tags"])) {
                    let tag = `${repoId}/${branchId}/${tagId}`
                    let tagData = this.data["repos"][repoId]["branches"][branchId]["tags"][tagId];
                    let tagViewPath = `/tags/${repoId}/${branchId}/${tagId}`

                    let tr = gesso.createElement(tbody, "tr");

                    let td = gesso.createElement(tr, "td");
                    this.createStateChangeLink(td, tagViewPath, tag);

                    td = gesso.createElement(tr, "td");
                    this.createOptionalLink(td, tagData["build_url"], tagData["build_id"], "-");

                    td = gesso.createElement(tr, "td");
                    this.createCommitLink(td, tagData["commit_url"], tagData["commit_id"], "-");

                    td = gesso.createElement(tr, "td", "-");
                }
            }
        }

        this.renderFooter(parent);
    }

    renderTagView(parent) {
        let [repoId, branchId, tagId] = this.request.path.split("/", 5).slice(2);
        let tag = `${repoId}/${branchId}/${tagId}`
        let data = this.data["repos"][repoId]["branches"][branchId]["tags"][tagId];

        this.renderHeader(parent, tag, [["/", "Stagger"], `Tag ${tag}`]);

        let url = new URL(window.location.href);
        let apiPath = `api/repos/${repoId}/branches/${branchId}/tags/${tagId}`
        let apiUrl = `${url.origin}/${apiPath}`
        let eventPath = `events/${repoId}/${branchId}/${tagId}`
        let eventUrl = `amqp://${url.hostname}:5672/${eventPath}`

        gesso.createElement(parent, "h2", "Properties");

        let props = gesso.createElement(parent, "table", {"class": "fields"});

        this.renderUrlField(props, "API URL", apiUrl);
        this.renderUrlField(props, "Event URL", eventUrl);

        let [th, td] = this.createField(props, "Build");
        this.createOptionalLink(td, data["build_url"], data["build_id"], "-");

        [th, td] = this.createField(props, "Commit");
        this.createOptionalLink(td, data["commit_url"], data["commit_id"], "-");

        this.createField(props, "Updated", "-");

        gesso.createElement(parent, "h2", "Artifacts");

        let table = gesso.createElement(parent, "table");
        let thead = gesso.createElement(table, "thead");
        let tbody = gesso.createElement(table, "tbody");

        let tr = gesso.createElement(thead, "tr");

        th = gesso.createElement(tr, "th", "Artifact");
        th = gesso.createElement(tr, "th", "Type");
        th = gesso.createElement(tr, "th", "Coordinates");

        for (let artifactId of Object.keys(data["artifacts"])) {
            let artifact = data["artifacts"][artifactId];

            tr = gesso.createElement(tbody, "tr");

            td = gesso.createElement(tr, "td");
            this.createStateChangeLink(td, `/artifacts/${tag}/${artifactId}`, artifactId);

            gesso.createElement(tr, "td", artifact["type"]);

            td = gesso.createElement(tr, "td");
            this.renderArtifactCoordinates(td, artifact);
        }

        gesso.createElement(parent, "h2", "Example commands");

        let commands = gesso.createElement(parent, "table", {"class": "fields"});

        this.renderCommandField(commands, "Get data", `curl ${apiUrl}`)
        this.renderCommandField(commands, "Create or update", `curl -X PUT ${apiUrl} -d @data.json`);
        this.renderCommandField(commands, "Delete", `curl -X DELETE ${apiUrl}`)
        this.renderCommandField(commands, "Check for updates", `curl --head -H 'If-None-Match: <etag>' ${apiUrl}`);
        this.renderCommandField(commands, "Listen for events", `qreceive ${eventUrl}`)

        gesso.createElement(parent, "h2", "Data");

        this.renderJsonData(parent, data);

        this.renderFooter(parent);
    }

    renderArtifactView(parent) {
        let [repoId, branchId, tagId, artifactId] = this.request.path.split("/", 6).slice(2);
        let tag = `${repoId}/${branchId}/${tagId}`
        let data = this.data["repos"][repoId]["branches"][branchId]["tags"][tagId]["artifacts"][artifactId];

        this.renderHeader(parent, artifactId, [["/", "Stagger"], [`/tags/${tag}`, `Tag ${tag}`], `Artifact ${artifactId}`]);

        let url = new URL(window.location.href);
        let apiPath = `api/repos/${repoId}/branches/${branchId}/tags/${tagId}/artifacts/${artifactId}`
        let apiUrl = `${url.origin}/${apiPath}`
        let eventPath = `events/${repoId}/${branchId}/${tagId}/${artifactId}`
        let eventUrl = `amqp://${url.hostname}:5672/${eventPath}`

        gesso.createElement(parent, "h2", "Properties");

        let props = gesso.createElement(parent, "table", {"class": "fields"});

        this.renderUrlField(props, "API URL", apiUrl);
        this.renderUrlField(props, "Event URL", eventUrl);

        this.createField(props, "Type", data["type"]);

        switch (data["type"]) {
        case "container":
            this.renderUrlField(props, "Registry URL", data["registry_url"]);
            this.createField(props, "Repository", data["repository"]);
            this.createField(props, "Image", data["image_id"]);
            break;
        case "file":
            this.renderUrlField(props, "URL", data["url"]);
            break;
        case "maven":
            this.renderUrlField(props, "Repository URL", data["repository_url"]);
            this.createField(props, "Group", data["group_id"]);
            this.createField(props, "Artifact", data["artifact_id"]);
            this.createField(props, "Version", data["version"]);
            break;
        case "rpm":
            this.renderUrlField(props, "Repository URL", data["repository_url"]);
            this.createField(props, "Name", data["name"]);
            this.createField(props, "Version", data["version"]);
            this.createField(props, "Release", data["release"]);
            break;
        }

        this.createField(props, "Updated", "-");

        gesso.createElement(parent, "h2", "Example commands");

        let commands = gesso.createElement(parent, "table", {"class": "fields"});

        this.renderCommandField(commands, "Get data", `curl ${apiUrl}`)
        this.renderCommandField(commands, "Create or update", `curl -X PUT ${apiUrl} -d @data.json`);
        this.renderCommandField(commands, "Delete", `curl -X DELETE ${apiUrl}`)
        this.renderCommandField(commands, "Check for updates", `curl --head -H 'If-None-Match: <etag>' ${apiUrl}`);
        this.renderCommandField(commands, "Listen for events", `qreceive ${eventUrl}`)

        gesso.createElement(parent, "h2", "Data");

        this.renderJsonData(parent, data);

        this.renderFooter(parent);
    }
}
