import datetime


def unix_strftime(value, fmt="%b %d, %Y %H:%M"):
    return datetime.datetime.utcfromtimestamp(int(value)).strftime(fmt)
