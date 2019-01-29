import os
import yaml

from app.errors import NotFound


if os.environ.get('VCAP_SERVICES'):
    # on cloudfoundry, config is a json blob in VCAP_SERVICES - unpack it, and populate
    # standard environment variables from it
    from app.paas_config import extract_paas_config

    extract_paas_config()

# encyption secret/salt
# SECRET_KEY = os.getenv('SECRET_KEY')
# DANGEROUS_SALT = os.getenv('DANGEROUS_SALT')

# DB conection string
SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')

TM_JIRA_USER = os.getenv('TM_JIRA_USER')
TM_JIRA_PAT = os.getenv('TM_JIRA_PAT')
TM_JIRA_HOST = os.getenv('TM_JIRA_HOST')
TM_PIVOTAL_PAT = os.getenv('TM_PIVOTAL_PAT')
TM_TRELLO_PAT = os.getenv('TM_TRELLO_PAT')
TM_TRELLO_TOKEN = os.getenv('TM_TRELLO_TOKEN')
TM_TRELLO_ORG_ID = os.getenv('TM_TRELLO_ORG_ID')
TM_TRELLO_SECRET = os.getenv('TM_TRELLO_SECRET')
TM_GITHUB_PAT = os.getenv('TM_GITHUB_PAT')


def get_team_profile(team_id=None):
    with open('teams.yml') as f:
        teams_yml = yaml.load(f)

    if not team_id:
        return teams_yml['teams']
    else:
        team = [t for t in teams_yml['teams'] if str(t.get('id')) == team_id]

    if not team:
        raise NotFound(f"Team id {team_id} not found in teams.yml")

    return team[0]

TEAM_PROFILES = get_team_profile()
