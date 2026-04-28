from uuid import uuid4


def generate_asset_id() -> str:
    return uuid4().hex[:8]


def generate_request_id() -> str:
    return uuid4().hex
