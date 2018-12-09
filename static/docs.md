# Stagger

A service for tagging software builds and describing the resulting
build artifacts.  A Stagger tag binds a well-known name to a concrete,
installable version of your software.

## Build repos

A build repo collects all the builds for a particular source
repository.  It contains a set of named branches.

#### Repo fields

<pre>
{
    "source_url": "&lt;source-url&gt;",
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

## Build branches

A build branch represents a stream of builds from a source code
branch.  This is usually the output of a CI job.  A branch contains a
set of named tags.

#### Branch fields

<pre>
{
    "job_url": "&lt;job-url&gt;",
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

## Build tags

A build tag is a stable name representing a build with a particular
status, such as "untested", "tested", or "released".  A tag contains a
set of named artifacts.

#### Tag fields

<pre>
{
    "build_id": "&lt;build-id&gt;",
    "build_url": "&lt;build-url&gt;",
    "commit_id": "&lt;commit-id&gt;",
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

## Build artifacts

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
    "type": "file",
    "url": "&lt;file-url&gt;"
}
</pre>

### Container images

I recommend IDs corresponding to the container image ID.

<pre>
{
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
    "type": "rpm",
    "repository_url": "&lt;package-repo-url&gt;",
    "name": "&lt;package-name&gt;",
    "version": "&lt;package-version&gt;"
    "release": "&lt;package-release&gt;",
}
</pre>

## AMQP events

In addition to HTTP endpoints, Stagger publishes any updates of repos,
branches, tags, or artifacts as AMQP messages.  They are published
under the following addresses:

<pre>
repos/&lt;repo-id&gt; -> { /* Repo fields */ }
repos/&lt;repo-id&gt;/branches/&lt;branch-id&gt; -> { /* Branch fields */ }
repos/&lt;repo-id&gt;/branches/&lt;branch-id&gt;/tags/&lt;tag-id&gt; -> { /* Tag fields */ }
repos/&lt;repo-id&gt;/branches/&lt;branch-id&gt;/tags/&lt;tag-id&gt;/artifacts/&lt;artifact-id&gt; -> { /* Artifact fields */ }
</pre>
