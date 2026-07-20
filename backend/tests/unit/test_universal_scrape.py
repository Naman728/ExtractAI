"""Site profile + universal helper unit tests."""

from app.scrapers.site_profiles import build_search_url, resolve_site_profile
from app.plugins.builtin import ProductPlugin
from app.plugins.base import PluginContext
from bs4 import BeautifulSoup


def test_resolve_amazon_profile() -> None:
    p = resolve_site_profile("https://www.amazon.com/s?k=headphones")
    assert p.id == "amazon"
    assert "requests_http" in p.engines
    url = build_search_url(p, "wireless headphones")
    assert url and "amazon.com/s?k=" in url


def test_amazon_asin_cards_extracted() -> None:
    html = """
    <html><body>
      <div data-asin="B0TESTASIN" data-component-type="s-search-result">
        <h2><a href="/dp/B0TESTASIN"><span>Test Headphones Pro</span></a></h2>
        <img class="s-image" src="https://example.com/h.jpg"/>
        <span class="a-price"><span class="a-offscreen">$29.99</span></span>
      </div>
    </body></html>
    """
    soup = BeautifulSoup(html, "lxml")
    ctx = PluginContext(
        url="https://www.amazon.com/s?k=x",
        final_url="https://www.amazon.com/s?k=x",
        html=html,
        soup=soup,
    )
    out = ProductPlugin().extract(ctx)
    assert any(p.get("name") == "Test Headphones Pro" for p in out.data)
    assert any(p.get("sku") == "B0TESTASIN" for p in out.data)
