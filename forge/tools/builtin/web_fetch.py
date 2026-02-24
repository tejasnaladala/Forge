from __future__ import annotations

from html.parser import HTMLParser

import httpx


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._text: list[str] = []
        self._skip = False
        self._skip_tags = {"script", "style", "nav", "footer", "header"}

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in self._skip_tags:
            self._skip = True

    def handle_endtag(self, tag: str) -> None:
        if tag in self._skip_tags:
            self._skip = False

    def handle_data(self, data: str) -> None:
        if not self._skip:
            stripped = data.strip()
            if stripped:
                self._text.append(stripped)

    def get_text(self) -> str:
        return "\n".join(self._text)


async def fetch(url: str, max_length: int = 10000) -> str:
    """Fetch a URL and return its extracted text content."""
    # Validate URL to prevent SSRF attacks
    from forge.api.security import validate_url
    try:
        url = validate_url(url)
    except ValueError as e:
        return f"SSRF protection: {e}"

    try:
        async with httpx.AsyncClient(follow_redirects=False, timeout=30.0) as client:
            response = await client.get(url)

            # Validate redirect targets
            if response.is_redirect:
                redirect_url = str(response.headers.get("location", ""))
                try:
                    validate_url(redirect_url)
                except ValueError as e:
                    return f"SSRF protection on redirect: {e}"
                response = await client.get(redirect_url)
            content_type = response.headers.get("content-type", "")

            if "html" in content_type:
                extractor = _TextExtractor()
                extractor.feed(response.text)
                text = extractor.get_text()
            else:
                text = response.text

            return text[:max_length]
    except Exception as e:
        return f"Error fetching {url}: {e}"


def register_tools(registry) -> None:
    registry.register(
        name="web_fetch",
        func=fetch,
        description="Fetch a URL and return its extracted text content. HTML tags are stripped for readability.",
        parameters={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The URL to fetch."},
                "max_length": {"type": "integer", "description": "Maximum characters to return.", "default": 10000},
            },
            "required": ["url"],
        },
    )
