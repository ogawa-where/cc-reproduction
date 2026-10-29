from pipeline import report
from tests.test_aggregate import ROWS


def test_render_sections():
    text = report.render(ROWS)
    assert "## Revenue by region" in text and "- north: 18.00" in text
    assert text.index("## Revenue by region") < text.index("## Units by product")
