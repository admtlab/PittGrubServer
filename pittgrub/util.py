import json


def json_esc(data: object, indent: int=2) -> str:
    """JSON encode data with indent"""
    return json.dumps(data, indent=indent).replace("</", "<\\/")


def semver_check(provided: str, supported: str) -> bool:
    """
    Check that the version provided is at least the version supported
    :param provided: Version provided
    :param supported: Minimum version supported
    :return: True if provided >= supported, False otherwise
    """
    p = provided.split('.')
    s = supported.split('.')
    return p[0] > s[0] or (p[0] == s[0] and (p[1] > s[1] or (p[1] == s[1] and p[2] >= s[2])))
