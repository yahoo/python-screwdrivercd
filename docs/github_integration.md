# Github integration utilites

## SSH initialization

The `screwdrivercd_ssh_setup` utility initializes the ssh configuration sufficiently to start 
[ssh-agent](https://www.ssh.com/ssh/agent).

This utility does not have any settings.

## Deploykey setup

The `screwdrivercd_github_deploykey` setup utility will populate the github deploy key stored in
the `GIT_DEPLOY_KEY` secret into the [ssh-agent](https://www.ssh.com/ssh/agent)

This utility requires that [ssh-agent](https://www.ssh.com/ssh/agent) is already running.

### Secrets

| Secret         | Description                                  |
| -------------- | -------------------------------------------- |
| GIT_DEPLOY_KEY | Base64 encoded github deployment private key |
