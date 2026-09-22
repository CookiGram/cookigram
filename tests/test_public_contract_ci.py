from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_ci_uses_the_immutable_public_contract() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")

    assert "safe_load" not in workflow
    assert "Contrôle YAML de secours" not in workflow
    assert 'CONTRACT_VERSION: "1.0.0"' in workflow
    assert "cookigram-contract.git@${CONTRACT_SHA}" in workflow
    assert "python -m cookigram_contract validate ." in workflow
    assert "b567e88acdcee69302c926caa6f5222508b7a051" in workflow


def test_public_contract_docs_describe_the_pinned_contract() -> None:
    docs = (ROOT / "docs/PUBLIC-CONTRACT.md").read_text(encoding="utf-8")

    assert "CONTRACT_VERSION=1.0.0" in docs
    assert "`v1.0.0`" in docs
    assert "b567e88acdcee69302c926caa6f5222508b7a051" in docs
    assert "CORE_SSH_KEY" in docs
    assert "cookigram_contract validate" in docs
