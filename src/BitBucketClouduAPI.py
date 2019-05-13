from BitBucketBaseuAPI import BitBucketBaseuAPI


class BitBucketClouduAPI(BitBucketBaseuAPI):
    def __init__(self, endpoint="https://bitbucket.org", auth=None, headers=None):
        super(BitBucketClouduAPI, self).__init__(endpoint, auth, headers)

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
