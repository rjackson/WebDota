import datetime
import pprint


def unix_strftime(value, fmt="%b %d, %Y %H:%M"):
    return datetime.datetime.utcfromtimestamp(int(value)).strftime(fmt)


def prettyprint(data):
    return pprint.pformat(data, indent=4)
