"""API Authentication and Twilio Signature Verification middleware."""

from __future__ import annotations

import hmac
import logging

from fastapi import HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from twilio.request_validator import RequestValidator

from src.config import settings

logger = logging.getLogger(__name__)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)


async def verify_api_key(
    request: Request,
    api_key_header_val: str | None = Security(api_key_header),
    auth_credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> str:
    """Verifies internal API requests using an API Key.

    Checks:
    1. 'X-API-Key' header
    2. 'Authorization: Bearer <key>' header

    If settings.API_KEY is unset (empty string), allows unauthenticated access in
    development mode with a debug log.
    If settings.API_KEY is set, rejects invalid or missing credentials with 401.
    """
    configured_key = settings.API_KEY.strip()
    if not configured_key:
        logger.debug("API_KEY not configured. Allowing unauthenticated access.")
        return ""

    provided_key: str | None = None
    if api_key_header_val:
        provided_key = api_key_header_val.strip()
    elif auth_credentials and auth_credentials.credentials:
        provided_key = auth_credentials.credentials.strip()
    else:
        raw_auth = request.headers.get("authorization", "")
        if raw_auth.lower().startswith("bearer "):
            provided_key = raw_auth[7:].strip()

    if not provided_key or not hmac.compare_digest(provided_key, configured_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return provided_key


async def verify_twilio_signature(request: Request) -> bool:
    """Validates incoming Twilio webhooks using Twilio's HMAC-SHA1 RequestValidator.

    Verifies the 'X-Twilio-Signature' against the public callback URL and POST params.
    """
    auth_token = settings.TWILIO_AUTH_TOKEN.strip()
    if not auth_token:
        logger.debug("TWILIO_AUTH_TOKEN not configured; skipping signature verification.")
        return True

    signature = request.headers.get("X-Twilio-Signature")
    if not signature:
        if settings.TWILIO_VALIDATE_SIGNATURE:
            logger.warning("Twilio signature validation failed: missing X-Twilio-Signature header")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Missing Twilio signature header",
            )
        logger.debug("X-Twilio-Signature header missing; skipping verification in dev mode.")
        return True

    # Construct request URL as seen by Twilio
    if settings.PUBLIC_URL:
        base = settings.PUBLIC_URL.strip().rstrip("/")
        url = f"{base}{request.url.path}"
        if request.url.query:
            url = f"{url}?{request.url.query}"
    elif "x-forwarded-host" in request.headers:
        proto = request.headers.get("x-forwarded-proto", "https")
        host = request.headers.get("x-forwarded-host")
        url = f"{proto}://{host}{request.url.path}"
        if request.url.query:
            url = f"{url}?{request.url.query}"
    else:
        url = str(request.url)

    # Read form data safely
    try:
        form_data = await request.form()
        post_data = {k: str(v) for k, v in form_data.items()}
    except Exception:
        post_data = {}

    validator = RequestValidator(auth_token)
    valid = validator.validate(url, post_data, signature)

    # Retry alternate scheme if TLS was terminated by reverse proxy
    if not valid and url.startswith("http://"):
        alt_url = "https://" + url[7:]
        valid = validator.validate(alt_url, post_data, signature)
    elif not valid and url.startswith("https://"):
        alt_url = "http://" + url[8:]
        valid = validator.validate(alt_url, post_data, signature)

    if not valid:
        logger.warning("Twilio signature validation failed for URL %s", url)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Twilio signature",
        )

    return True
