from __future__ import annotations

import json

import httpx

from forge.api.security import validate_url


async def http_request(
    method: str = "GET",
    url: str = "",
    headers: dict = None,
    body: str = "",
    timeout: int = 30,
) -> str:
    """Send an HTTP request and return the response."""
    # Validate URL to prevent SSRF attacks
    try:
        url = validate_url(url)
    except ValueError as e:
        return json.dumps({"error": f"SSRF protection: {e}"})

    headers = headers or {}

    try:
        async with httpx.AsyncClient(follow_redirects=False, timeout=float(timeout)) as client:
            kwargs = {"headers": headers}

            if method.upper() in ("POST", "PUT", "PATCH") and body:
                try:
                    kwargs["json"] = json.loads(body)
                except (json.JSONDecodeError, TypeError):
                    kwargs["content"] = body

            response = await client.request(method.upper(), url, **kwargs)

            # If redirect, validate the redirect target before following
            if response.is_redirect:
                redirect_url = str(response.headers.get("location", ""))
                try:
                    validate_url(redirect_url)
                except ValueError as e:
                    return json.dumps({"error": f"SSRF protection on redirect: {e}"})
                response = await client.request("GET", redirect_url, **{"headers": headers})

            response_body = response.text[:5000]
            result = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response_body,
            }
            return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)})


def register_tools(registry) -> None:
    registry.register(
        name="http_request",
        func=http_request,
        description="Send an HTTP request and return the response status, headers, and body.",
        parameters={
            "type": "object",
            "properties": {
                "method": {"type": "string", "description": "HTTP method.", "default": "GET", "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"]},
                "url": {"type": "string", "description": "The target URL."},
                "headers": {"type": "object", "description": "Request headers."},
                "body": {"type": "string", "description": "Request body (JSON string for POST/PUT/PATCH).", "default": ""},
                "timeout": {"type": "integer", "description": "Timeout in seconds.", "default": 30},
            },
            "required": ["url"],
        },
    )
