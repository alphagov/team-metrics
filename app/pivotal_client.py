# Parts of source extracted from https://github.com/CloudBoltSoftware/pivotalclient
import requests
import logging
import inspect
import sys
from copy import deepcopy


class ApiError(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)


class PivotalClient:
    def __init__(self, api_token, account_id=None, project_id=None, api_root=None):
        self.auth_headers = {'X-TrackerToken': api_token}
        self.account_id = account_id
        self.project_id = project_id

        if not api_root:
            api_root = 'https://www.pivotaltracker.com/services/v5'
        self.api_root = api_root

        self.api_accounts = '{}/accounts'.format(self.api_root)
        if self.account_id:
            self.api_account = '{}/{}'.format(self.api_accounts, self.account_id)

        self.api_projects = '{}/projects'.format(self.api_root)
        if self.project_id:
            self.api_project = '{}/{}'.format(self.api_projects, self.project_id)
            self.api_project_iterations = '{}/{}/iterations'.format(self.api_projects, self.project_id)
            self.api_project_cycle_time_details = '{}/{}/iterations/{}/analytics/cycle_time_details'.format(
                self.api_projects, self.project_id, '{}')
            self.api_project_iteration = '{}/{}/iterations/{}'.format(self.api_projects, self.project_id, '{}')
            self.api_stories = '{}/stories'.format(self.api_project, self.project_id)
            self.api_story = '{}/stories/{}'.format(self.api_project, '{}')
            self.api_story_blockers = '{}/stories/{}/blockers'.format(self.api_project, '{}')
            self.api_activity = '{}/stories/{}/activity'.format(self.api_project, '{}')

        self.api_filter = {'date_format': 'millis', 'filter': None}

    def _get(self, endpoint, querystring=None, with_envelope=False):
        """Issue a GET to Pivotal Tracker.

        Args:
            endpoint: a URL to GET
            querystring: a dict of querystring parameters
        """
        _querystring = querystring.copy() if querystring else {}
        if with_envelope:
            _querystring['envelope'] = 'true'
        headers = self.auth_headers

        resp = requests.get(endpoint, params=_querystring, headers=headers)
        if not resp or not 200 <= resp.status_code < 300:
            raise ApiError('GET {} {} {}'.format(endpoint, resp.status_code, resp.json()))
        return resp.json()

    def _verify_project_id_exists(self):
        if not self.project_id:
            caller_name = 'UNKNOWN'
            try:
                caller_name = sys.getframe(1).f_code.co_name
            except Exception as ex:
                caller_name = inspect.stack()[1][3]
            raise ApiError('Project ID not set on API connection and is required by {}().'.format(caller_name))

    def get_projects(self):
        uri = self.api_projects
        results = self._get(uri)
        return results

    def get_project(self):
        uri = self.api_project
        results = self._get(uri)
        return results

    def get_project_iterations(self):
        uri = self.api_project_iterations
        results = self._get(uri)
        return results

    def get_project_iteration(self, iteration_id):
        uri = self.api_project_iteration.format(iteration_id)
        results = self._get(uri)
        return results

    def get_project_cycle_time_details(self, iteration_id):
        uri = self.api_project_cycle_time_details.format(iteration_id)
        results = self._get(uri)
        return results

    def get_story(self, story_id):
        self._verify_project_id_exists()
        return self._get(self.api_story.format(story_id))

    def get_story_blockers(self, story_id):
        self._verify_project_id_exists()
        return self._get(self.api_story_blockers.format(story_id))

    def get_story_activities(self, story_id):
        self._verify_project_id_exists()
        uri = self.api_activity.format(story_id)
        results = self._get(uri)
        return results
