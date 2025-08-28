import pytest

from telegram_bot.application import remove_unclosed_tags


@pytest.mark.parametrize(
    "message,result",
    [
        ("<a></a><b class=''></b>", "<a></a><b class=''></b>"),
        ("<a><b>TEXT</b>", "<b>TEXT</b>"),
        (
            "<a><b>TEXT</b><d></c></d>",
            "<b>TEXT</b><d></d>",
        ),
    ],
)
def test_remove_unclosed_tags(message: str, result: str):
    assert remove_unclosed_tags(message) == result
