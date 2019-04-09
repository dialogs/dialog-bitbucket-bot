import requests


class BitBucketuAPI(object):
    def __init__(self, endpoint="https://bitbucket.org", auth=None, headers=None):
        super(BitBucketuAPI, self).__init__()
        self._endpoint = endpoint
        self._auth = auth
        if not headers:
            headers = {'Content-Type': 'application/json'}
        self._headers = headers

    def _perform_get(self, url, auth=None):
        with requests.get(url, auth=auth, headers=self._headers) as req:
            if req.status_code == 200:
                return req.json()
            else:
                req.raise_for_status()

    def get_pulls_activity(self, username, reponame):
        """
        Perform API GET request to bitbucket server
        :param username: repository owner username
        :param reponame: repository name
        :return: dict parsed json api response
        """
        url = "{0}/api/2.0/repositories/{1}/{2}/pullrequests/activity".format(self._endpoint, username, reponame)
        return self._perform_get(url, self._auth)

    def get_pulls(self, username, reponame):
        """
        Perform API GET request to bitbucket server
        :param username: repository owner username
        :param reponame: repository name
        :return: dict parsed json api response
        """
        url = "{0}/api/2.0/repositories/{1}/{2}/pullrequests".format(self._endpoint, username, reponame)
        return self._perform_get(url, self._auth)

    def get_pull(self, username, reponame, pull_id):
        """
        Perform API GET request to bitbucket server
        :param username: repository owner username
        :param reponame: repository name
        :param pull_id: id of the pullrequest
        :return: dict parsed json api response
        """
        url = "{0}/api/2.0/repositories/{1}/{2}/pullrequests/{3}".format(self._endpoint, username, reponame, pull_id)
        return self._perform_get(url, self._auth)

    def get_pull_activity(self, username, reponame, pull_id):
        """
        Perform API GET request to bitbucket server
        :param username: repository owner username
        :param reponame: repository name
        :param pull_id: id of the pullrequest
        :return: dict parsed json api response
        """
        url = "{0}/api/2.0/repositories/{1}/{2}/pullrequests/{3}/activity".format(self._endpoint, username,
                                                                                  reponame, pull_id)
        return self._perform_get(url, self._auth)

    def get_repositories(self, username):
        url = "{0}/api/2.0/repositories/{1}/".format(self._endpoint, username)
        return self._perform_get(url, self._auth)
