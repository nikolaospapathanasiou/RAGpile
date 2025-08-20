import pytest
from bs4 import BeautifulSoup

from tools.browser import get_text_with_links


@pytest.mark.parametrize(
    "html,result",
    [
        (
            "<script>some script</script><a href='https://www.google.com'>Google</a>",
            "Google (https://www.google.com)",
        ),
        (
            "<body><div>    Hi   </div><div>  Hello  </div></body>",
            "Hi\nHello",
        ),
    ],
)
def test_get_text_with_links(html: str, result: str):
    soup = BeautifulSoup(
        html,
        "html.parser",
    )
    assert get_text_with_links(soup) == result
