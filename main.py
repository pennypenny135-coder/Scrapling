from fastapi import FastAPI, Query, HTTPException
from urllib.request import Request, urlopen
from urllib.parse import urlsplit, urlunsplit, quote, urljoin
from html.parser import HTMLParser

app = FastAPI()


def normalize_url(url: str) -> str:
    parts = urlsplit(url)

    if parts.scheme not in ("http", "https"):
        raise HTTPException(
            status_code=400,
            detail="Only http and https URLs are allowed"
        )

    return urlunsplit((
        parts.scheme,
        parts.netloc,
        quote(parts.path, safe="/%"),
        quote(parts.query, safe="=&/%"),
        quote(parts.fragment, safe="")
    ))


class LinkParser(HTMLParser):
    def __init__(self, base_url: str):
        super().__init__()
        self.base_url = base_url
        self.links = []
        self.current_href = None
        self.current_text = []

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return

        attributes = dict(attrs)
        self.current_href = attributes.get("href")
        self.current_text = []

    def handle_data(self, data):
        if self.current_href is not None:
            self.current_text.append(data)

    def handle_endtag(self, tag):
        if tag != "a" or not self.current_href:
            return

        title = " ".join("".join(self.current_text).split())
        link = urljoin(self.base_url, self.current_href)

        if title:
            self.links.append({
                "title": title,
                "link": link
            })

        self.current_href = None
        self.current_text = []


@app.get("/")
def scrape(url: str = Query(...)):
    safe_url = normalize_url(url)

    request = Request(
        safe_url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "zh-HK,zh;q=0.9,en;q=0.8"
        }
    )

    try:
        with urlopen(request, timeout=20) as response:
            status_code = response.status
            final_url = response.url
            html = response.read().decode("utf-8", errors="ignore")

        parser = LinkParser(final_url)
        parser.feed(html)

        unique_links = []
        seen = set()

        for item in parser.links:
            if item["link"] not in seen:
                seen.add(item["link"])
                unique_links.append(item)

        return {
            "ok": True,
            "source": safe_url,
            "final_url": final_url,
            "http_status": status_code,
            "html_length": len(html),
            "link_count": len(unique_links),
            "data": unique_links[:50]
        }

    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail=str(error)
        )
