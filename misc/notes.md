# Continuous delivery

## Source code for downstream artifacts

 - rh-<repo>-dist
   - Jenkinsfile
   - <artifact-type-1>
     - [scripts]
   - <artifact-type-2>
     - [scripts]

 - rh-qpid-dispatch-dist
   - Jenkinsfile
   - rpm
     - Makefile
     - qpid-dispatch.spec.in
     - Output: RPMs tagged under rh-qpid-dispatch-rpm:<master>-tested
   - container
     - Dockerfile
     - Output: Container image tagged under rh-qpid-dispatch-container:<master>-tested

 - rh-qpid-jms-dist
   - Jenkinsfile
   - maven
     - Output: Artifacts tagged under rh-qpid-jms-maven:<branch>-tested
   - maven-repository-zip
     - Output: Files tagged under rh-qpid-jms-maven-repository-zip:<branch>-tested
   - zip
     - Output: Files tagged under rh-qpid-jms-zip:<branch>-tested

## General procedure

 - Each component repo (and each desired branch):
   - Fetches source from rh-<repo>
   - For each artifact type:
     - Installs build dependencies from well-known internal repos using the tagging service
     - Builds the artifact or artifacts
     - Copies the artifacts to a well-known internal repo
     - Tags the artifacts to rh-<component>:<branch>-untested
     - Installs the artifacts in all desired environments
     - Tests the installed artifacts
     - Tags the artifacts to rh-<component>:<branch>-tested

## Todo

 - Change type container-image to just container
