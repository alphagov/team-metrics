# Team Metrics
[Alpha] code to explore how we can collect and report on team metrics, running on PaaS: `https://team-metrics.cloudapps.digital`

## How to see your team metrics

Start by updating the `teams.yml` with your team information and creating a PR for review by the traceability team. 

Example `teams.yml` entry:

```
teams:
- id: 5  # needs to be unique in the teams.yml
  name: support
  # path is how you expect to get to your team page:
  path: gds/delivery-and-support/technology-operations/reliability-engineering/support  
  users:  # who needs to access the team metrics
    john.smith
  source:  # currently only jira, pivotal and trello are supported
    type: pivotal
    id: 112233
  repos:  # not necessary if you don't have any repos in your team
    ruby_repo_1
    infrastructure_repo_2
    python-repo-3
```

Someone from the traceability team will get in contact you to get access to your team delivery tool, e.g. pivotal, and based on your entry they will create the views necessary to show your team metrics.

## Deployment to PaaS

The web app is currently deployed into the `traceability` space in `gds-tech-ops`, if you can't see the space, you will need to be added to the space: 

`cf set-space-role a.developer@gov.uk gds-tech-ops traceability SpaceDeveloper`

### Deployment pre-requisites
#### Secrets

The first time that a deployment is made a user provided service on PaaS containing the credentials will need to be created: 

```
cf cups tm-creds -p '{"TM_JIRA_USER": "somone@gov.uk","TM_JIRA_PAT": "<Jira PAT>","TM_JIRA_HOST": "<Jira host>","TM_JIRA_PROJECT": "CT","TM_PIVOTAL_PAT": "<Pivotal PAT>","TM_PIVOTAL_PROJECT_ID": "<{Pivotal project ID}>","TM_TRELLO_PAT": "<Trello PAT>","TM_TRELLO_TOKEN": "<Trello Token>","TM_TRELLO_BOARD_ID": "<Trello board>","TM_TRELLO_ORG_ID": "<Trello org>","TM_TRELLO_SECRET": "<Trello secret>","TM_GITHUB_PAT": "<Github PAT>"}'
```

#### Setting the the postgres backend

Run this command to add postgres database service to the space:

`cf create-service postgres tiny-unencrypted-10.5 tm-pg-service`

#### Deploying the app

In order to deploy the app:

`cf push`

#### Safelist the app

If the safelist route service has not already been added to the space, then you will need to add it using this command:

`cf cups re-ip-whitelist-service -r https://re-ip-whitelist-service.cloudapps.digital`

You can then bind the route service to the app to ensure that it will only be accessibly within the office or on VPN:

`cf bind-route-service cloudapps.digital re-ip-whitelist-service --hostname team-metrics`

## Running the frontend locally

### API Tokens

In order to get access to the You will create a Personal Access Tokens at these locations:

Jira:       https://id.atlassian.com/manage/api-tokens

Pivotal:    https://www.pivotaltracker.com/profile

Trello:     https://trello.com/app-key

Github:     https://github.com/settings/tokens

### Environment

create and source `environment.sh` containing:

```bash
export TM_USER= # Atlassian username / email address
export TM_PAT= # Atlassian personal access token
export TM_HOST= # Jira host (X for X.atlassian.net)

export TM_PIVOTAL_PAT= # pivotal personal access token
export TM_PIVOTAL_PROJECT_ID= # pivotal project id, found in URL of project - https://www.pivotaltracker.com/n/projects/<project id>

export TM_TRELLO_PAT= # Get key from https://trello.com/app-key
export TM_TRELLO_TOKEN= # Click Token on page - https://trello.com/app-key
export TM_TRELLO_BOARD_ID= # Get https://trello.com/b/<board id>

export TM_GITHUB_PAT= # Token generated from https://github.com/settings/tokens

export SQLALCHEMY_DATABASE_URI= # 'docker' or 'postgres://<host, eg localhost>:<port, eg 5432>/<database name, eg team_metrics>'
```

### Starting the web application

After sourcing the `environment.sh` you can start the web app by running:

`./startup.sh`

### Running the team metrics CLI

`./main.py`

Follow instructions to see team metrics from delivery tools
