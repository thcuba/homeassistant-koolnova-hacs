# -*- coding: utf-8 -*-
"""Session manager for the Koolnova REST API in order to maintain authentication token between calls."""

import logging
import time
from typing import Optional
from urllib.parse import quote_plus

from requests import Response
from requests import Session
from requests.exceptions import ConnectionError
from requests.exceptions import Timeout
from requests.exceptions import HTTPError

from .const import KOOLNOVA_API_URL, KOOLNOVA_AUTH_URL, COMMON_HEADERS, FULL_USER_AGENT

_LOGGER = logging.getLogger(__name__)

# Retry policy constants
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_BACKOFF = 1.0  # base delay in seconds
DEFAULT_RETRY_MAX_BACKOFF = 30.0  # max delay in seconds

# Per-request timeout. Without one, a hung request blocks a polling cycle forever.
# 50s is the minimum recommended by Kool support; never go below it.
REQUEST_TIMEOUT = 50
# Hard floor: requests to the Koolnova servers never time out below this value.
MIN_REQUEST_TIMEOUT = 50

# Session keepalive: refresh token if last request was longer ago than this
SESSION_HEARTBEAT_INTERVAL = 2400  # 40 minutes (before token at 50 min expires)


class KoolnovaClientSession(Session):
    """HTTP session manager for the Koolnova API.

    This session object manages authentication using a bearer token
    and provides robust request handling.

    Features:
    - Retry policy with exponential backoff for resilience.
    - Automatic session refresh on 401 (Unauthorized) errors.
    - Session heartbeat to prevent token expiration.
    """

    host: str = KOOLNOVA_API_URL

    def __init__(self, username: str, password: str, email: Optional[str] = None,
                 max_retries: int = DEFAULT_MAX_RETRIES,
                 retry_backoff: float = DEFAULT_RETRY_BACKOFF,
                 request_timeout: float = REQUEST_TIMEOUT) -> None:
        """Initialize and authenticate.

        Args:
            username: the koolnova registered user
            password: the koolnova user's password
            email: optional email associated to the account
            max_retries: number of retry attempts for rest_request
            retry_backoff: base delay for exponential backoff
            request_timeout: per-request timeout in seconds for auth and API calls
        """
        Session.__init__(self)
        self.username = username
        self.password = password
        self.email = email
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
        self.request_timeout = request_timeout if request_timeout is not None else REQUEST_TIMEOUT

        _LOGGER.debug("Starting authentication for username '%s' (email: %s)", username, email)

        # Build payload: prefer explicit email param; if not provided but username
        # looks like an email address, send it as 'email' as well.
        if email:
            payload = {"email": email, "password": password}
        elif username and "@" in username:
            payload = {"email": username, "password": password}
        else:
            payload = {"username": username or "", "password": password}

        _LOGGER.debug("Auth payload: %s", {k: "***" if k == "password" else v for k, v in payload.items()})

        # Browser-like headers: since May 2026 the API returns 404 without the
        # sec-ch-ua / sec-fetch-* headers and a modern Chrome UA (issue #4).
        headers_token = COMMON_HEADERS.copy()
        headers_token["content-type"] = "application/json"

        # Improved retry logic with exponential backoff for rate limiting
        response = None
        auth_max_attempts = 5
        auth_base_delay = 2.0
        auth_max_delay = 60.0

        for attempt in range(auth_max_attempts):
            try:
                auth_timeout = max(float(self.request_timeout), MIN_REQUEST_TIMEOUT)
                response = super().request("POST", KOOLNOVA_AUTH_URL, json=payload, headers=headers_token, timeout=auth_timeout)
            except Exception as e:
                _LOGGER.exception("Exception when calling auth endpoint (attempt %d/%d): %s", attempt + 1, auth_max_attempts, e)
                response = None

            if response is None:
                # Network error - use exponential backoff
                if attempt < auth_max_attempts - 1:
                    delay = min(auth_base_delay * (2 ** attempt), auth_max_delay)
                    _LOGGER.debug("Network error, retrying in %.1f seconds (attempt %d/%d)", delay, attempt + 1, auth_max_attempts)
                    time.sleep(delay)
                continue

            _LOGGER.debug("Auth response status: %s", response.status_code)

            if response.status_code == 429:
                # Rate limiting - extract retry-after if available
                retry_after = response.headers.get('Retry-After')
                if retry_after:
                    try:
                        delay = min(float(retry_after), auth_max_delay)
                    except ValueError:
                        delay = min(auth_base_delay * (2 ** attempt), auth_max_delay)
                else:
                    # API says "Expected available in 32 seconds" - use that as base
                    delay = min(32.0 + (attempt * 5), auth_max_delay)

                if attempt < auth_max_attempts - 1:
                    _LOGGER.warning("Rate limited (429), retrying in %.1f seconds (attempt %d/%d)", delay, attempt + 1, auth_max_attempts)
                    time.sleep(delay)
                    continue
                else:
                    _LOGGER.error("Rate limit persisted after %d attempts", auth_max_attempts)
                    break
            elif response.status_code >= 500:
                # Server errors - use shorter backoff
                if attempt < auth_max_attempts - 1:
                    delay = min(auth_base_delay * (2 ** attempt), 30.0)
                    _LOGGER.debug("Server error (%d), retrying in %.1f seconds (attempt %d/%d)",
                                response.status_code, delay, attempt + 1, auth_max_attempts)
                    time.sleep(delay)
                    continue
            else:
                # Success or client error - break
                break

        if response is None:
            raise RuntimeError(f"Authentication request failed after {auth_max_attempts} attempts (no response)")

        # Log body for easier debugging when failing
        try:
            body = response.text
        except Exception:
            body = "<unable to read response body>"

        _LOGGER.debug("Auth response body: %s", body)

        try:
            response.raise_for_status()
        except Exception as exc:
            raise RuntimeError(f"Authentication failed: {exc} - {body}") from exc

        data = response.json()
        # Support common token field names
        token = data.get("access_token") or data.get("token") or data.get("accessToken")
        if not token:
            raise RuntimeError(f"Authentication response did not contain a token: {data}")

        self.bearerToken = str(token)
        self.token_created = time.time()  # Track when token was created
        self.last_request_time = time.time()  # Track last API call time
        _LOGGER.debug("BearerToken of authentication : %s", "***")

    def refresh_token(self) -> None:
        """Re-authenticate and replace the bearer token.

        Used when the API answers 401 (expired/invalid token) mid-session.
        Only renews the token; the requests.Session itself is left untouched.
        """
        _LOGGER.info("Refreshing session token...")
        try:
            self.__init__(self.username, self.password, self.email,
                         self.max_retries, self.retry_backoff, self.request_timeout)
            _LOGGER.info("Session token refreshed successfully")
        except Exception as e:
            _LOGGER.error("Failed to refresh session: %s", e)
            self.bearerToken = None
            self.token_created = 0.0
            raise RuntimeError(f"Failed to refresh session: {e}") from e

    def _refresh_session(self) -> None:
        """Re-authenticate and get a new token."""
        self.refresh_token()

    def _should_refresh_session(self) -> bool:
        """Check if session needs refresh based on age and heartbeat interval."""
        if not hasattr(self, 'token_created') or not hasattr(self, 'last_request_time'):
            return False
        elapsed_since_request = time.time() - self.last_request_time
        elapsed_since_creation = time.time() - self.token_created
        # Refresh if more than heartbeat interval since last request, or token near expiry
        if elapsed_since_request > SESSION_HEARTBEAT_INTERVAL:
            _LOGGER.debug("Session heartbeat: %.0f seconds since last request", elapsed_since_request)
            return True
        if elapsed_since_creation > 2700:  # 45 min, token is 50 min
            _LOGGER.debug("Session token nearing expiry: %.0f seconds old", elapsed_since_creation)
            return True
        return False

    def rest_request(self, method: str, path: str, max_retries: Optional[int] = None,
                     retry_backoff: Optional[float] = None, **kwargs) -> Response:
        """
        Make a request using token authentication, with retry and auto-refresh.

        Args:
            method: HTTP method (e.g., "GET", "POST", "PATCH").
            path: Path of the REST API endpoint.
            max_retries: Override default retry count.
            retry_backoff: Override default backoff delay.
            **kwargs: Additional arguments for the request (e.g., headers, json, data).

        Returns:
            The Response object corresponding to the result of the API request.
        """
        retries = max_retries if max_retries is not None else self.max_retries
        backoff = retry_backoff if retry_backoff is not None else self.retry_backoff

        # Check if session needs refresh (heartbeat)
        if self._should_refresh_session():
            self._refresh_session()

        # Ensure token exists
        if not getattr(self, 'bearerToken', None):
            _LOGGER.debug("No active session, creating new one...")
            self._refresh_session()

        token = self.bearerToken if isinstance(self.bearerToken, str) else ""

        # Without an explicit timeout a hung request blocks the polling cycle.
        # Enforce a hard floor so requests to the Koolnova servers never time
        # out below MIN_REQUEST_TIMEOUT, regardless of what was configured.
        timeout = kwargs.get("timeout")
        if timeout is None:
            timeout = self.request_timeout
        timeout = max(float(timeout), MIN_REQUEST_TIMEOUT)
        kwargs["timeout"] = timeout

        headers_auth = {
            "Authorization": "Bearer " + token,
            "Cache-Control": "no-cache",
            "User-Agent": FULL_USER_AGENT,
        }
        # Merge headers passed as argument
        headers = kwargs.pop("headers", {})
        headers_auth.update(headers)

        url = f"{self.host}/{path}"

        for attempt in range(retries + 1):
            try:
                response = super().request(method, url, headers=headers_auth, **kwargs)
                self.last_request_time = time.time()

                # Handle 401: token expired or invalid -> refresh and retry
                if response.status_code == 401:
                    _LOGGER.warning("Received 401 on attempt %d/%d, refreshing session", attempt + 1, retries + 1)
                    if attempt < retries:
                        self._refresh_session()
                        # Retry with new token
                        new_token = self.bearerToken if isinstance(self.bearerToken, str) else ""
                        headers_auth["Authorization"] = "Bearer " + new_token
                        continue
                    else:
                        _LOGGER.error("401 persisted after session refresh")
                        response.raise_for_status()

                # Handle 429: rate limited
                if response.status_code == 429:
                    retry_after = response.headers.get('Retry-After')
                    delay = float(retry_after) if retry_after else min(backoff * (2 ** attempt), DEFAULT_RETRY_MAX_BACKOFF)
                    if attempt < retries:
                        _LOGGER.warning("Rate limited (429), retrying in %.1f seconds", delay)
                        time.sleep(delay)
                        continue
                    else:
                        _LOGGER.error("Rate limit persisted after %d attempts", retries + 1)

                # Handle 5xx: server errors
                if response.status_code >= 500 and attempt < retries:
                    delay = min(backoff * (2 ** attempt), DEFAULT_RETRY_MAX_BACKOFF)
                    _LOGGER.warning("Server error %d on attempt %d/%d, retrying in %.1f seconds",
                                  response.status_code, attempt + 1, retries + 1, delay)
                    time.sleep(delay)
                    continue

                response.raise_for_status()
                return response

            except (ConnectionError, Timeout) as e:
                if attempt < retries:
                    delay = min(backoff * (2 ** attempt), DEFAULT_RETRY_MAX_BACKOFF)
                    _LOGGER.warning("Connection error on attempt %d/%d: %s, retrying in %.1f seconds",
                                  attempt + 1, retries + 1, e, delay)
                    time.sleep(delay)
                    continue
                else:
                    _LOGGER.error("Connection error persisted after %d attempts: %s", retries + 1, e)
                    raise

            except HTTPError as e:
                # If raise_for_status hasn't been called yet (5xx already handled above)
                if response is not None and response.status_code >= 500 and attempt < retries:
                    delay = min(backoff * (2 ** attempt), DEFAULT_RETRY_MAX_BACKOFF)
                    _LOGGER.warning("HTTP error %d on attempt %d/%d, retrying in %.1f seconds",
                                  response.status_code, attempt + 1, retries + 1, delay)
                    time.sleep(delay)
                    continue
                raise

        # If we get here, all retries exhausted
        _LOGGER.error("All %d retry attempts exhausted for %s %s", retries + 1, method, url)
        raise RuntimeError(f"All retry attempts exhausted for {method} {url}")
