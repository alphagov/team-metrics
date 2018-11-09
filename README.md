# team-metrics
[Alpha] code to explore how we can collect and report on team metrics

## API Tokens

You can create a Atlassian Personal Access Token at this location:
https://id.atlassian.com/manage/api-tokens

## Environment

create `environment.sh` containing:

```bash
export TM_USER='' # Atlassian username / email address
export TM_PAT='' # Atlassian personal access token
export TM_HOST='' # Jira host (X for X.atlassian.net)
```
