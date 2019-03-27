import os
import json
import datetime


# a simple way to persistently store a dict({})
class DictPersistJSON(dict):
    def __init__(self, filename, *args, **kwargs):
        super(DictPersistJSON, self).__init__(*args, **kwargs)
        self.filename = filename  # JSON filename
        self._load()  # Load data from file
        self.update(*args, **kwargs)

    def _default(self, obj):  # json serializer doesn't support datetime out of the box, this is a fix
        if isinstance(obj, datetime.date):
            return {'_isoformat': obj.isoformat()}
        return str(obj)

    def _object_hook(*args):  # see up ^ json deserialize doesn't support datetime out of the box, this is a fix
        obj = args[1]
        _isoformat = obj.get('_isoformat')
        if _isoformat is not None:
            return datetime.datetime.fromisoformat(_isoformat)
        return obj

    def _load(self):  # Load data from json file
        if os.path.isfile(self.filename) and os.path.getsize(self.filename) > 0:
            with open(self.filename, 'r') as fh:
                self.update(json.load(fh, object_hook=self._object_hook))

    def _dump(self):  # Save data to json file
        with open(self.filename, 'w') as fh:
            json.dump(self, fh, default=self._default)

    def __getitem__(self, key):
        return dict.__getitem__(self, key)

    def __setitem__(self, key, val):  # On value update save new dict to json file
        dict.__setitem__(self, key, val)
        self._dump()

    def update(self, *args, **kwargs):  # Fill dict
        for k, v in dict(*args, **kwargs).items():
            self[k] = v
        self._dump()
