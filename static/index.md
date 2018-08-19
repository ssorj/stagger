# Stagger

A service for tagging software builds and describing the resulting
build artifacts.

## Build tags

A build tag is a stable name representing a component build with a
particular status, such as "untested", "tested", or "released".

A tag is identified by an arbitrary ID.  The tag ID is meant for use
in the context of multiple components and branches, so it is important
to qualify it.  I recommend IDs of the form
<code>&lt;repository&gt;:&lt;branch&gt;:&lt;status&gt;</code>.

A tag contains a set of named artifacts.

<pre>
<b>GET /api/tags/&lt;tag-id&gt;</b>
<b>PUT /api/tags/&lt;tag-id&gt;</b>

{
    "repository": "&lt;source-repo-name&gt;",
    "repository_url": "&lt;source-repo-url&gt;",
    "branch": "&lt;branch-name&gt;",
    "commit": "&lt;commit-id&gt;",
    "artifacts": {
        "&lt;artifact-id&gt;": { /* Artifact fields */ },
        "&lt;artifact-id&gt;": { /* Artifact fields */ },
        "&lt;artifact-id&gt;": { /* Artifact fields */ }
    }
}
</pre>

<pre>
<b>GET /api/tags</b>

{
    "&lt;tag-id&gt;": { /* Tag fields */ },
    "&lt;tag-id&gt;": { /* Tag fields */ },
    "&lt;tag-id&gt;": { /* Tag fields */ }
}
</pre>

<pre>
<b>DELETE /api/tags/&lt;tag-id&gt;</b>
</pre>

## Build artifacts

A build artifact holds the details to required to get and install one
of the build outputs, such as Maven artifacts or container images.
Different artifact types have different fields.

<pre>
<b>GET /api/tags/&lt;tag-id&gt;/artifacts/&lt;artifact-id&gt;</b>

{
    "type": "&lt;artifact-type&gt;",
    /* Type-specific fields */
}
</pre>

<pre>
<b>GET /api/tags/&lt;tag-id&gt;/artifacts</b>

{
    "&lt;artifact-id&gt;": { /* Artifact fields */ },
    "&lt;artifact-id&gt;": { /* Artifact fields */ },
    "&lt;artifact-id&gt;": { /* Artifact fields */ }
}
</pre>

An artifact is identified by an arbitrary ID.  I suggest some
conventions for these below.

### Arbitrary files

I recommend IDs of the form
<code>&lt;file-name&gt;-&lt;file-type&gt;</code>, as in
<code>amq-broker-zip</code>.

<pre>
{
    "type": "file",
    "url": "&lt;file-url&gt;"
}
</pre>

### Container images

I recommend IDs of the form
<code>&lt;repository-name&gt;-container</code>, as in
<code>amq-interconnect-container</code>.

<pre>
{
    "type": "container-image",
    "registry_url": "&lt;container-registry-url&gt;",
    "repository": "&lt;repository-name&gt;",
    "image-id": "&lt;image-id&gt;"
}
</pre>

### Maven artifacts

I recommend IDs of the form
<code>&lt;maven-artifact-id&gt;-maven</code>, as in
<code>qpid-jms-client-maven</code>.

<pre>
{
    "type": "maven",
    "repository_url": "&lt;maven-repo-url&gt;",
    "group-id": "&lt;maven-group-id&gt;",
    "artifact-id": "&lt;maven-artifact-id&gt;",
    "version": "&lt;maven-version&gt;"
}
</pre>

### RPM packages

I recommend IDs of the form
<code>&lt;package-name&gt;-rpm</code>, as in
<code>qpid-proton-cpp-devel-rpm</code>.

<pre>
{
    "type": "rpm",
    "repository_url": "&lt;package-repo-url&gt;",
    "name": "&lt;package-name&gt;",
    "version": "&lt;package-version&gt;"
    "release": "&lt;package-release&gt;",
}
</pre>
