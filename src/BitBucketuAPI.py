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
        if not auth:
            auth = self._auth
        with requests.get(url, auth=auth, headers=self._headers) as req:
            if req.status_code == 200:
                return req.json()
            else:
                req.raise_for_status()

    def _api_call(self, url, max_pages=None):
        count = 0
        while True:
            res = self._perform_get(url)
            for value in res["values"]:
                yield value
            if "next" in res:
                url = res["next"]
            else:
                break
            if max_pages:
                count += 1
                if count >= max_pages:
                    break

    def get_pulls_activity(self, username, reponame, max_pages=None):
        """
        Perform API GET request to bitbucket server
        :param username: repository owner username
        :param reponame: repository name
        :return: dict parsed json api response
        """
        url = "{0}/api/2.0/repositories/{1}/{2}/pullrequests/activity".format(self._endpoint, username, reponame)
        return self._api_call(url, max_pages)

    def get_pulls(self, username, reponame, max_pages=None):
        """
        Perform API GET request to bitbucket server
        :param username: repository owner username
        :param reponame: repository name
        :return: dict parsed json api response
        """
        url = "{0}/api/2.0/repositories/{1}/{2}/pullrequests".format(self._endpoint, username, reponame)
        return self._api_call(url, max_pages)

    def get_pull(self, username, reponame, pull_id, max_pages=None):
        """
        Perform API GET request to bitbucket server
        :param username: repository owner username
        :param reponame: repository name
        :param pull_id: id of the pullrequest
        :return: dict parsed json api response
        """
        url = "{0}/api/2.0/repositories/{1}/{2}/pullrequests/{3}".format(self._endpoint, username, reponame, pull_id)
        return self._api_call(url, max_pages)

    def get_pull_activity(self, username, reponame, pull_id, max_pages=None):
        """
        Perform API GET request to bitbucket server
        :param username: repository owner username
        :param reponame: repository name
        :param pull_id: id of the pullrequest
        :return: dict parsed json api response
        """
        url = "{0}/api/2.0/repositories/{1}/{2}/pullrequests/{3}/activity".format(self._endpoint, username,
                                                                                  reponame, pull_id)
        return self._api_call(url, max_pages)

    def get_repositories(self, username, max_pages=None):
        if username:
            url = "{0}/api/2.0/repositories/{1}/".format(self._endpoint, username)
        else:
            url = "{0}/api/2.0/repositories/".format(self._endpoint)
        return self._api_call(url, max_pages)
