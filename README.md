# team-metrics
[Alpha] code to explore how we can collect and report on team metrics

## API Tokens

You can create a Atlassian Personal Access Token at this location:
https://id.atlassian.com/manage/api-tokens

## Environment

create and source `environment.sh` containing:

```bash
export TM_USER='' # Atlassian username / email address
export TM_PAT='' # Atlassian personal access token
export TM_HOST='' # Jira host (X for X.atlassian.net)

export TM_PIVOTAL_PAT= # pivotal personal access token, created here - https://www.pivotaltracker.com/profile
export TM_PIVOTAL_PROJECT_ID= # pivotal project id, found in URL of project - https://www.pivotaltracker.com/n/projects/<project id>

export TM_TRELLO_PAT= # Get key from https://trello.com/app-key
export TM_TRELLO_TOKEN= # Click Token on page - https://trello.com/app-key
export TM_TRELLO_BOARD_ID= # Get https://trello.com/b/<board id>

export TM_GITHUB_PAT= # Token generated from https://github.com/settings/tokens
```

## Running

`./main.py`

Follow instructions to see team metrics from delivery tools
