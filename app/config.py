import os
import yaml

from app.errors import NotFound


if os.environ.get('VCAP_SERVICES'):
    # on cloudfoundry, config is a json blob in VCAP_SERVICES - unpack it, and populate
    # standard environment variables from it
    from app.paas_config import extract_paas_config

    extract_paas_config()


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


def get_org_structure():
    with open('org-structure.yml') as f:
        org_structure = yaml.load(f)
    return [org_structure]


class Config:
    # encyption secret/salt
    SECRET_KEY = os.getenv('SECRET_KEY')
    DANGEROUS_SALT = os.getenv('DANGEROUS_SALT')

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

TEAM_PROFILES = get_team_profile()
ORG_STRUCTURE = get_org_structure()

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI', 'http://localhost:5000/oauth2callback')
AUTH_URI = 'https://accounts.google.com/o/oauth2/auth'
TOKEN_URI = 'https://accounts.google.com/o/oauth2/token'
REVOKE_URI = 'https://accounts.google.com/o/oauth2/revoke'
USER_INFO = 'https://www.googleapis.com/userinfo/v2/me'
SCOPE = ['profile', 'email']
OAUTHLIB_INSECURE_TRANSPORT = os.getenv('OAUTHLIB_INSECURE_TRANSPORT')
