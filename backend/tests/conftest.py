import os
os.environ["TESTING"] = "1"

import pytest


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """Clear in-memory rate limiter between tests to prevent cross-test pollution."""
    from api.routes import auth
    auth._login_attempts.clear()
    yield
    auth._login_attempts.clear()
