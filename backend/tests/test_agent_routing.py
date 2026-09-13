import pytest

from app.rag.agent import route_question


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        ("How many leaves do I have left?", "employee"),
        ("What is the maternity leave policy?", "policy"),
        ("What is the next holiday in Bengaluru?", "holiday"),
        ("Am I eligible under the policy based on my leave balance?", "hybrid"),
    ],
)
def test_route_question(question: str, expected: str) -> None:
    assert route_question(question) == expected
