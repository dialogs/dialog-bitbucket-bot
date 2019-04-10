import requests


class BitBucketBaseuAPI(object):
    def __init__(self, endpoint="https://bitbucket.org", auth=None, headers=None):
        super(BitBucketBaseuAPI, self).__init__()
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
