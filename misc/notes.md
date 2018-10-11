# Continuous delivery

## Source code for downstream artifacts

 - rh-<repo>-<artifact-type>
   - Jenkinsfile
   - [scripts]

 - rh-qpid-dispatch-rpm
   - Jenkinsfile
   - Makefile
   - qpid-dispatch.spec.in
   - Output: RPMs tagged under rh-qpid-dispatch-rpm:<master>-tested

 - rh-qpid-dispatch-container
   - Jenkinsfile
   - Dockerfile
   - Output: Container image tagged under rh-qpid-dispatch-container:<master>-tested

 - rh-qpid-jms-maven
   - Jenkinsfile
   - Output: Artifacts tagged under rh-qpid-jms-maven:<branch>-tested
   - Output: Files tagged under rh-qpid-jms-maven-repository-zip:<branch>-tested

 - rh-qpid-jms-zip
   - Jenkinsfile
   - Output: Files tagged under rh-qpid-jms-zip:<branch>-tested

## Jobs

 - rh-<repo>
   - Build source
   - Run tests

 - rh-<repo>-<artifact-type>
   - Triggered by rh-<repo> success
   - Build artifacts
   - For each target environment:
     - Install artifacts
     - Test the installed artifacts
   - Tag the artifacts

 - rh-qtools
   - Build source
   - Run tests

 - rh-qtools-rpm
   - Build RPMs
   - For each in (el6, el7):
     - Install the RPMs
     - Test the installed RPMs
   - Copy and tag the RPMs

 - rh-qtools-container
   - Build the container
   - Run the container
   - Test inside the container
   - Push and tag the container

## General procedure

Each artifact-type repo (and each desired branch):

 - Fetches source from rh-<repo>
 - Installs dependencies from well-known internal repos using the tagging service
 - Builds the artifact or artifacts
 - Copies the artifacts to a well-known internal repo
 - Tags the artifacts to rh-<repo>-<artifact-type>:<branch>-untested
 - Installs the artifacts in all desired environments
 - Tests the installed artifacts
 - Tags the artifacts to rh-<repo>-<artifact-type>:<branch>-tested
