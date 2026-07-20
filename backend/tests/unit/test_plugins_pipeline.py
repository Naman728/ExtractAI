"""Plugin and pipeline unit tests."""

from app.normalization.engine import NormalizationEngine
from app.plugins.registry import PluginRegistry
from app.scrapers.cleaner import HtmlCleaner
from app.validation.engine import ValidationEngine


SAMPLE_HTML = """
<html lang="en">
<head>
  <title>Acme Widget</title>
  <meta name="description" content="Buy widgets">
  <meta property="og:title" content="Acme Widget">
  <meta name="twitter:card" content="summary">
  <link rel="canonical" href="https://shop.example.com/widget">
  <script type="application/ld+json">
  {"@type":"Product","name":"Acme Widget","offers":{"@type":"Offer","price":"19.99","priceCurrency":"USD"}}
  </script>
</head>
<body>
  <h1>Acme Widget</h1>
  <p>This is a wonderful widget that solves many problems for everyday users around the world.</p>
  <img src="/img/widget.png" alt="Widget">
  <a href="mailto:sales@example.com">Email us</a>
  <a href="tel:+15551234567">Call</a>
  <a href="/files/spec.pdf">Spec PDF</a>
  <table><tr><th>Size</th><td>Large</td></tr></table>
  <ul><li>One</li><li>Two</li></ul>
  <form action="/buy"><input type="text" name="qty"><button type="submit">Buy</button></form>
  <script>console.log('remove me')</script>
  <style>.x{color:red}</style>
</body>
</html>
"""


def test_cleaner_removes_script_style() -> None:
    clean = HtmlCleaner().clean(SAMPLE_HTML)
    assert "<script" not in clean.lower()
    assert "<style" not in clean.lower()
    assert "Acme Widget" in clean


def test_cleaner_handles_none_attrs() -> None:
    """Agent-fetched HTML can leave Tag.attrs as None; must not crash."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup("<html><body><p>ok</p></body></html>", "lxml")
    for tag in soup.find_all(True):
        tag.attrs = None
    clean = HtmlCleaner().clean(str(soup))
    assert "ok" in clean


def test_plugins_extract_core_sections() -> None:
    registry = PluginRegistry()
    registry.discover()
    out = registry.run_all(
        url="https://shop.example.com/widget",
        final_url="https://shop.example.com/widget",
        html=SAMPLE_HTML,
    )
    payload = out["payload"]
    assert payload["title"] == "Acme Widget"
    assert payload["emails"]
    assert payload["json_ld"]
    assert payload["open_graph"]
    assert payload["products"]
    assert payload["prices"]
    assert payload["downloads"]
    assert len(registry.enabled()) >= 15


def test_normalize_and_validate() -> None:
    registry = PluginRegistry()
    registry.discover()
    raw = registry.run_all(
        url="https://shop.example.com/widget",
        final_url="https://shop.example.com/widget",
        html=SAMPLE_HTML,
    )["payload"]
    normalized = NormalizationEngine().normalize(raw, base_url="https://shop.example.com/widget")
    validated, report = ValidationEngine().validate(normalized)
    assert validated["title"] == "Acme Widget"
    assert "sales@example.com" in validated["emails"]
    assert validated["images"][0]["url"].startswith("https://")
    assert report["overall_confidence"] > 0
