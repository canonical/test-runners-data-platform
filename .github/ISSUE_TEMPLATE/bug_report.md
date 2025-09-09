---
name: Bug report
about: File a bug report
labels: bug

---

<!-- Thank you for submitting a bug report! All fields are required unless marked optional. -->

## Steps to reproduce
<!-- Please enable debug logging by running `juju model-config logging-config="<root>=INFO;unit=DEBUG"` (if possible) -->
1. 

## Expected behavior


## Actual behavior
<!-- If applicable, add screenshots -->


## Versions
<!-- Model version from `juju status` -->
Juju agent: 

<!-- "Kubernetes" or "machines" -->
Cloud type: 

<!--
For microk8s, run `microk8s version`
For LXD, run `lxd version`
For other clouds, please provide any version information
-->
Cloud: 

<!-- App revision from `juju status` or (advanced) commit hash -->
mysql/mysql-k8s charm revision: 
mysql-router/mysql-router-k8s charm revision: 

## Log output
<!-- Please enable debug logging by running `juju model-config logging-config="<root>=INFO;unit=DEBUG"` (if possible) -->
<!-- Then, run `juju debug-log --replay > log.txt` and upload "log.txt" file here -->
Juju debug log: 

<!-- (Optional) Copy the logs that are relevant to the bug & paste inside triple backticks below -->


## Additional context
<!-- (Optional) Add any additional information here -->
