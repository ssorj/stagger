<div id="content" markdown="1">

<header>
  <div>
    <nav class="context"><a href="/">Stagger</a> &nbsp;&gt;&nbsp; Documentation</nav>
    <h1>Documentation</h1>
  </div>
</header>

Stagger is a service for tagging software builds and describing the
resulting build artifacts.  A Stagger tag binds a well-known name to a
concrete, installable version of your software.

Stagger helps you connect CI jobs.  It enables two key operations:

* Locating the latest artifacts produced by another CI job
* Triggering CI jobs when a dependency is updated

#### Contents

* [Entity fields and operations](#entity-fields-and-operations)
  * [Build repos](#build-repos)
  * [Build branches](#build-branches)
  * [Build tags](#build-tags)
  * [Build artifacts](#build-artifacts)
* [Using curl to perform operations](#using-curl-to-perform-operations)
  * [Querying entities](#querying-entities)
  * [Creating or updating entities](#creating-or-updating-entities)
  * [Deleting entities](#deleting-entities)
* [Detecting entity updates](#detecting-entity-updates)
  * [Polling for updates with HTTP](#polling-for-updates-with-http)
  * [Listening for updates with AMQP](#listening-for-updates-with-amqp)

## Entity fields and operations

### Build repos

A build repo collects all the builds for a particular source
repository.  It contains a set of named branches.

#### Repo fields

<pre>
{
    "source_url": "&lt;source-url&gt;",
    "job_url": "&lt;job-url&gt;",
    "branches": {
        "&lt;branch-id&gt;": { /* Branch fields */ },
        "&lt;branch-id&gt;": { /* Branch fields */ },
        "&lt;branch-id&gt;": { /* Branch fields */ }
    }
}
</pre>

#### Repo operations

<pre>
<b>GET /api/repos/&lt;repo-id&gt;</b> -&gt; { /* Repo fields */ }
<b>PUT /api/repos/&lt;repo-id&gt;</b> &lt;- { /* Repo fields */ }
<b>DELETE /api/repos/&lt;repo-id&gt;</b>
<b>HEAD /api/repos/&lt;repo-id&gt;</b>

<b>GET /api/repos</b> -&gt;

{
    "&lt;repo-id&gt;": { /* Repo fields */ },
    "&lt;repo-id&gt;": { /* Repo fields */ },
    "&lt;repo-id&gt;": { /* Repo fields */ }
}
</pre>

### Build branches

A build branch represents a stream of builds from a source code
branch.  This is usually the output of a CI job.  A branch contains a
set of named tags.

#### Branch fields

<pre>
{
    "tags": {
        "&lt;tag-id&gt;": { /* Tag fields */ },
        "&lt;tag-id&gt;": { /* Tag fields */ },
        "&lt;tag-id&gt;": { /* Tag fields */ }
    }
}
</pre>

#### Branch operations

<pre>
<b>GET /api/repos/&lt;repo-id&gt;/branches/&lt;branch-id&gt;</b> -&gt; { /* Branch fields */ }
<b>PUT /api/repos/&lt;repo-id&gt;/branches/&lt;branch-id&gt;</b> &lt;- { /* Branch fields */ }
<b>DELETE /api/repos/&lt;repo-id&gt;/branches/&lt;branch-id&gt;</b>
<b>HEAD /api/repos/&lt;repo-id&gt;/branches/&lt;branch-id&gt;</b>

<b>GET /api/repos/&lt;repo-id&gt;/branches</b> ->

{
    "&lt;branch-id&gt;": { /* Branch fields */ },
    "&lt;branch-id&gt;": { /* Branch fields */ },
    "&lt;branch-id&gt;": { /* Branch fields */ }
}
</pre>

### Build tags

A build tag is a stable name representing a build with a particular
status, such as "untested", "tested", or "released".  A tag contains a
set of named artifacts.

#### Tag fields

<pre>
{
    "build_id": "&lt;build-id&gt;", // Required and must not be null
    "build_url": "&lt;build-url&gt;",
    "commit_id": "&lt;commit-id&gt;",
    "commit_url": "&lt;commit-url&gt;",
    "artifacts": {
        "&lt;artifact-id&gt;": { /* Artifact fields */ },
        "&lt;artifact-id&gt;": { /* Artifact fields */ },
        "&lt;artifact-id&gt;": { /* Artifact fields */ }
    }
}
</pre>

#### Tag operations

<pre>
<b>GET /api/repos/&lt;repo-id&gt;/branches/&lt;branch-id&gt;/tags/&lt;tag-id&gt;</b> -&gt; { /* Tag fields */ }
<b>PUT /api/repos/&lt;repo-id&gt;/branches/&lt;branch-id&gt;/tags/&lt;tag-id&gt;</b> &lt;- { /* Tag fields */ }
<b>DELETE /api/repos/&lt;repo-id&gt;/branches/&lt;branch-id&gt;/tags/&lt;tag-id&gt;</b>
<b>HEAD /api/repos/&lt;repo-id&gt;/branches/&lt;branch-id&gt;/tags/&lt;tag-id&gt;</b>

<b>GET /api/repos/&lt;repo-id&gt;/tags</b> ->

{
    "&lt;tag-id&gt;": { /* Tag fields */ },
    "&lt;tag-id&gt;": { /* Tag fields */ },
    "&lt;tag-id&gt;": { /* Tag fields */ }
}
</pre>

### Build artifacts

A build artifact holds the details to required to get and install one
of the build outputs, such as Maven artifacts or container images.
Different artifact types have different fields.

#### Artifact fields

<pre>
<b>GET /api/repos/&lt;repo-id&gt;/branches/&lt;branch-id&gt;/tags/&lt;tag-id&gt;/artifacts/&lt;artifact-id&gt;</b>

{
    "type": "&lt;artifact-type&gt;",
    /* Type-specific fields */
}
</pre>

#### Artifact operations

<pre>
<b>GET /api/repos/&lt;repo-id&gt;/branches/&lt;branch-id&gt;/tags/&lt;tag-id&gt;/artifacts/&lt;artifact-id&gt;</b> -&gt; { /* Artifact fields */}
<b>PUT /api/repos/&lt;repo-id&gt;/branches/&lt;branch-id&gt;/tags/&lt;tag-id&gt;/artifacts/&lt;artifact-id&gt;</b> &lt;- { /* Artifact fields */}
<b>DELETE /api/repos/&lt;repo-id&gt;/branches/&lt;branch-id&gt;/tags/&lt;tag-id&gt;/artifacts/&lt;artifact-id&gt;</b>
<b>HEAD /api/repos/&lt;repo-id&gt;/branches/&lt;branch-id&gt;/tags/&lt;tag-id&gt;/artifacts/&lt;artifact-id&gt;</b>

<b>GET /api/repos/&lt;repo-id&gt;/branches/&lt;branch-id&gt;/tags/&lt;tag-id&gt;/artifacts</b> -&gt;

{
    "&lt;artifact-id&gt;": { /* Artifact fields */ },
    "&lt;artifact-id&gt;": { /* Artifact fields */ },
    "&lt;artifact-id&gt;": { /* Artifact fields */ }
}
</pre>

An artifact is identified by an arbitrary ID.  I suggest some
conventions for these below.

### Arbitrary files

I recommend IDs corresponding to the file name, but without any
unstable version part, as in <code>amq-broker.zip</code>.

<pre>
{
    // All fields are required and must not be null
    "type": "file",
    "url": "&lt;file-url&gt;"
}
</pre>

### Container images

I recommend IDs corresponding to the container image ID.

<pre>
{
    // All fields are required and must not be null
    "type": "container",
    "registry_url": "&lt;container-registry-url&gt;",
    "repository": "&lt;repository-name&gt;",
    "image_id": "&lt;image-id&gt;"
}
</pre>

### Maven artifacts

I recommend IDs corresponding to the Maven artifact ID, as in
<code>qpid-jms-client</code>.

<pre>
{
    // All fields are required and must not be null
    "type": "maven",
    "repository_url": "&lt;maven-repo-url&gt;",
    "group_id": "&lt;maven-group-id&gt;",
    "artifact_id": "&lt;maven-artifact-id&gt;",
    "version": "&lt;maven-version&gt;"
}
</pre>

### RPM packages

I recommend IDs corresponding to the RPM package name, as in
<code>qpid-proton-cpp-devel</code>.

<pre>
{
    // All fields are required and must not be null
    "type": "rpm",
    "repository_url": "&lt;package-repo-url&gt;",
    "name": "&lt;package-name&gt;",
    "version": "&lt;package-version&gt;"
    "release": "&lt;package-release&gt;",
}
</pre>

## Using curl to perform operations

### Querying entities

<pre>
curl --fail &lt;service-url&gt/api/repos/example-repo/branches/master/tags/tested
</pre>

### Creating or updating entities

<pre>
curl --fail -X PUT &lt;service-url&gt/api/repos/example-repo/branches/master/tags/tested -d @- &lt;&lt;EOF
{
    "build_id": "999",
    "artifacts": {
        "example": {
            "type": "maven",
            "repository_url": "https://maven.example.com/",
            "group_id": "org.example",
            "artifact_id": "example",
            "version": "1.0.0-999"
        }
    }
}
EOF
</pre>

### Deleting entities

<pre>
curl --fail -X DELETE &lt;service-url&gt/api/repos/example-repo/branches/master/tags/tested
</pre>

## Detecting entity updates

### Polling for updates with HTTP

All of the HTTP endpoints support lightweight HEAD operations, and all
responses contain an ETag header with a unique digest of the content.
Use curl with an If-None-Match header to periodically test for
changes.

### Listening for updates with AMQP

In addition to HTTP endpoints, Stagger publishes any updates of repos,
branches, tags, or artifacts as AMQP messages.  They are published
under the following addresses:

<pre>
repos/&lt;repo-id&gt; -> { /* Repo fields */ }
repos/&lt;repo-id&gt;/branches/&lt;branch-id&gt; -> { /* Branch fields */ }
repos/&lt;repo-id&gt;/branches/&lt;branch-id&gt;/tags/&lt;tag-id&gt; -> { /* Tag fields */ }
repos/&lt;repo-id&gt;/branches/&lt;branch-id&gt;/tags/&lt;tag-id&gt;/artifacts/&lt;artifact-id&gt; -> { /* Artifact fields */ }
</pre>

</div>
