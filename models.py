from mongokit import Document


class Job(Document):
    __collection__ = "jobs"
    __database__ = "webdota"

    structure = {
        "type": basestring,
        "id": int,
        "attempts": int
    }

    required_fields = ["type", "id"]
    default_values = {"attempts": 0}

    def __repr__(self):
        return "<Job {!r}>".format(self._id)


class Profile(Document):
    __collection__ = "profiles"
    __database__ = "webdota"

    structure = {
        "data": {},
        "id": int,
        "_last_updated": int
    }
    use_dot_notation = True

    def __repr__(self):
        return "<Profile {!r}>".format(self.id)


class Match(Document):
    __collection__ = "matches"
    __database__ = "webdota"

    structure = {
        "data": {},
        "id": int,
        "_last_updated": int
    }
    use_dot_notation = True

    def __repr__(self):
        return "<Match {!r}>".format(self.id)


class User(Document):
    __collection__ = "users"
    __database__ = "webdota"

    structure = {
        "id": long,
        "account_id": int,
        "nickname": basestring
    }
    use_dot_notation = True

    def __repr__(self):
        return "<Match {!r}>".format(self.id)
