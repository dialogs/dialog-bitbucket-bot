from BitBucketBaseuAPI import BitBucketBaseuAPI


class BitBucketServeruAPI(BitBucketBaseuAPI):
    def __init__(self, endpoint="https://bitbucket.org", auth=None, headers=None):
        super(BitBucketServeruAPI, self).__init__(endpoint, auth, headers)

    def get_pulls(self, project_key, repo_slug, max_pages=None):
        """
        Perform API GET request to bitbucket server
        :param username: repository owner username
        :param reponame: repository name
        :return: dict parsed json api response
        """
        url = "{0}/rest/api/1.0/projects/{1}/repos/{2}/pull-requests/".format(self._endpoint, project_key, repo_slug)
        return self._api_call(url, max_pages)

    def get_pull(self, project_key, repo_slug, pull_id, max_pages=None):
        """
        Perform API GET request to bitbucket server
        :param username: repository owner username
        :param reponame: repository name
        :return: dict parsed json api response
        """
        url = "{0}/rest/api/1.0/projects/{1}/repos/{2}/pull-requests/{3}".format(self._endpoint, project_key,
                                                                                 repo_slug, pull_id)
        return self._api_call(url, max_pages)

    def format_comment_url(self, project_key, repo_slug, pull_id, comment_id, max_pages=None):
        url = "{0}/projects/{1}/repos/{2}/pull-requests/{3}/overview?commentId={4}".format(self._endpoint, project_key,
                                                                                           repo_slug, pull_id,
                                                                                           comment_id)
        return url

    def get_pulls_activity(self, project_key, repo_slug, pull_id, max_pages=None):
        """
        Perform API GET request to bitbucket server
        :param username: repository owner username
        :param reponame: repository name
        :return: dict parsed json api response
        """
        url = "{0}/rest/api/1.0/projects/{1}/repos/{2}/pull-requests/{3}/activities".format(self._endpoint, project_key,
                                                                                            repo_slug, pull_id)
        return self._api_call(url, max_pages)

    def get_repositories(self, project_key=None, max_pages=None):
        if project_key:
            url = "{0}/rest/api/1.0/projects/{1}/repos/".format(self._endpoint, project_key)
        else:
            url = "{0}/rest/api/1.0/repos".format(self._endpoint)
        # url = "{0}/rest/api/1.0/projects/TEMP/repos/tempa/pull-requests/".format(self._endpoint)
        return self._api_call(url, max_pages)
