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

        if (this.request.path.startsWith("/tags/")) {
            this.renderTagView(content);
        } else {
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

        gesso.createText(nav, navLinks[navLinks.length - 1][1]);

        gesso.createElement(parent, "h1", title);
    }

    renderFooter(parent) {
        let elem = gesso.createElement(parent, "nav", {"class": "footer"});

        gesso.createLink(elem, "/docs.html", "Documentation");
    }

    renderUrlField(parent, name, url) {
        let [th, td] = this.createField(parent, name);
        let code = gesso.createElement(td, "code");
        gesso.createLink(code, url, url);
    }

    renderCommandField(parent, name, command) {
        let [th, td] = this.createField(parent, name);
        gesso.createElement(td, "code", command);
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
                    let td;

                    td = gesso.createElement(tr, "td");
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
        let navLinks = [["/", "Stagger"], [`/tags/${tag}`, `Tag ${tag}`]];
        let data = this.data["repos"][repoId]["branches"][branchId]["tags"][tagId];

        this.renderHeader(parent, tag, navLinks);

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

        gesso.createElement(parent, "h2", "Example commands");

        let commands = gesso.createElement(parent, "table", {"class": "fields"});

        this.renderCommandField(commands, "Get data", `curl ${apiUrl}`)
        this.renderCommandField(commands, "Create or update", `curl -X PUT ${apiUrl} -d @data.json`);
        this.renderCommandField(commands, "Delete", `curl -X DELETE ${apiUrl}`)
        this.renderCommandField(commands, "Check for updates", `curl --head -H 'If-None-Match: <etag>' ${apiUrl}`);
        this.renderCommandField(commands, "Listen for events", `qreceive ${eventUrl}`)

        gesso.createElement(parent, "h2", "Data");

        let json = JSON.stringify(data, null, 4);

        if (hljs) {
            json = hljs.highlight("json", json).value;
        }

        json = json.replace(/"(https?:\/\/.*?)"/g, "\"<a href=\"$1\">$1</a>\"");

        let pre = gesso.createElement(parent, "pre");
        pre.innerHTML = json;

        this.renderFooter(parent);
    }
}
