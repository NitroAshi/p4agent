from infra.news.playwright_google_news import extract_cards_from_html


def test_extract_cards_from_html_parses_links() -> None:
    html = """
    <html><body>
      <a href="./articles/ABC">Headline One</a>
      <a href="https://example.com/two">Headline Two</a>
    </body></html>
    """

    cards = extract_cards_from_html(
        html=html,
        source_url="https://news.ycombinator.com/",
        max_items=10,
    )

    assert len(cards) == 2
    assert cards[0]["title"] == "Headline One"
    assert cards[0]["url"].startswith("https://news.ycombinator.com")
