from fastapi import FastAPI, Query, HTTPException
from urllib.request import Request, urlopen
from urllib.parse import urlsplit, urlunsplit, quote, urljoin
from lxml import html


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


def extract_tables(tree):
    tables = []

    for table in tree.xpath("//table"):
        rows = []

        for tr in table.xpath(".//tr"):
            cells = []

            for cell in tr.xpath("./th | ./td"):
                text = " ".join(
                    cell.text_content().replace("\xa0", " ").split()
                )
                cells.append(text)

            if cells:
                rows.append(cells)

        if rows:
            tables.append(rows)

    return tables


def extract_text(tree):
    body = tree.xpath("//body")

    if not body:
        return ""

    text = body[0].text_content().replace("\xa0", " ")
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())


@app.get("/")
def scrape(
    url: str = Query(...),
    mode: str = Query("links", pattern="^(links|tables|text|all)$")
):
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
            page_html = response.read().decode("utf-8", errors="ignore")

        tree = html.fromstring(page_html)
        result = {
            "ok": True,
            "source": safe_url,
            "final_url": final_url,
            "http_status": status_code,
            "html_length": len(page_html),
            "mode": mode
        }

        if mode in ("links", "all"):
            links = []
            seen = set()

            for element in tree.xpath("//a[@href]"):
                href = element.get("href")
                title = " ".join(
                    element.text_content().replace("\xa0", " ").split()
                )
                link = urljoin(final_url, href)

                if link not in seen:
                    seen.add(link)
                    links.append({
                        "title": title,
                        "link": link
                    })

            result["link_count"] = len(links)
            result["data"] = links[:50]

        if mode in ("tables", "all"):
            tables = extract_tables(tree)
            result["table_count"] = len(tables)
            result["tables"] = tables

        if mode in ("text", "all"):
            result["text"] = extract_text(tree)

        return result

    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail=str(error)
        )
