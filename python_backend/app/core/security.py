# Security modules (authentication, authorization, encryption helpers)

def verify_local_request(host: str) -> bool:
    """Ensure that incoming requests are strictly local."""
    return host == "127.0.0.1" or host == "localhost"
