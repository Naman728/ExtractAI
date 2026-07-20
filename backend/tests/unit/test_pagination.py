"""Unit tests for pagination discovery and payload merge."""

from app.scrapers.pagination import (
    discover_next_url,
    merge_plugin_payloads,
    merge_section_confidence,
)


def test_discover_rel_next_link() -> None:
    html = """
    <html><head>
      <link rel="next" href="/catalogue/page-2.html">
    </head><body>page 1</body></html>
    """
    next_url = discover_next_url(
        html, "https://books.toscrape.com/catalogue/page-1.html", seen=set()
    )
    assert next_url == "https://books.toscrape.com/catalogue/page-2.html"


def test_discover_next_anchor_text() -> None:
    html = """
    <html><body>
      <ul class="pager">
        <li class="next"><a href="page-3.html">next</a></li>
      </ul>
    </body></html>
    """
    next_url = discover_next_url(
        html, "https://books.toscrape.com/catalogue/page-2.html", seen=set()
    )
    assert next_url == "https://books.toscrape.com/catalogue/page-3.html"


def test_discover_skips_seen_and_offsite() -> None:
    html = """
    <html><body>
      <a rel="next" href="https://evil.example/page-2">next</a>
      <link rel="next" href="/page-2">
    </body></html>
    """
    seen = {"https://example.com/page-2"}
    next_url = discover_next_url(html, "https://example.com/page-1", seen=seen)
    assert next_url is None


def test_bump_query_page_when_no_next_control() -> None:
    html = "<html><body><p>no pager</p></body></html>"
    next_url = discover_next_url(
        html, "https://example.com/items?page=2&sort=asc", seen=set()
    )
    assert next_url == "https://example.com/items?page=3&sort=asc"


def test_merge_plugin_payloads_concat_lists() -> None:
    base = {"title": "Page 1", "products": [{"name": "A"}], "links": [{"url": "/a"}]}
    extra = {"title": "Page 2", "products": [{"name": "B"}], "emails": ["a@b.com"]}
    merged = merge_plugin_payloads(base, extra)
    assert merged["title"] == "Page 1"
    assert merged["products"] == [{"name": "A"}, {"name": "B"}]
    assert merged["emails"] == ["a@b.com"]
    assert merged["links"] == [{"url": "/a"}]


def test_merge_section_confidence_takes_max() -> None:
    out = merge_section_confidence({"products": 0.5, "links": 0.9}, {"products": 0.8})
    assert out["products"] == 0.8
    assert out["links"] == 0.9
