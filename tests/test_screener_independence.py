from pathlib import Path


def test_screener_never_mentions_the_answer_key():
    for path in Path("screener").glob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        assert "answer_key" not in text, f"{path} mentions the answer key"
        assert "evaluation" not in text, f"{path} imports from evaluation"