from fastapi import FastAPI, Query, HTTPException
from urllib.request import Request, urlopen
from urllib.parse import urlparse, urljoin
from html.parser import HTMLParser

app = FastAPI()


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.current_href = None
        self.current_text = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            attributes = dict(attrs)
            self.current_href = attributes.get("href")
            self.current_text = []

    def handle_data(self, data):
        if self.current_href is not None:
            self.current_text.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self.current_href:
            title = " ".join("".join(self.current_text).split())

            if title:
                self.links.append({
                    "title": title,
                    "link": self.current_href
                })

            self.current_href = None
            self.current_text = []


@app.get("/")
def scrape(url: str = Query(...)):
    parsed_url = urlparse(url)

    if parsed_url.scheme not in ("http", "https"):
        raise HTTPException(
            status_code=400,
            detail="Only http and https URLs are allowed"
        )

    request = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/131 Safari/537.36"
            )
        }
    )

    try:
        with urlopen(request, timeout=8) as response:
            html = response.read().decode(
                "utf-8",
                errors="ignore"
            )

        parser = LinkParser()
        parser.feed(html)

        results = []

        for item in parser.links[:50]:
            results.append({
                "title": item["title"],
                "link": urljoin(url, item["link"])
            })

        return {
            "ok": True,
            "source": url,
            "count": len(results),
            "data": results
        }

    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail=str(error)
        )
