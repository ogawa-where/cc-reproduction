from ssg import markdown


def test_heading_and_paragraph():
    assert markdown.to_html("# T\n\nhello `x`\n") == "<h1>T</h1>\n<p>hello <code>x</code></p>\n"


def test_list():
    assert markdown.to_html("- a\n- b\n") == "<ul>\n<li>a</li>\n<li>b</li>\n</ul>\n"
