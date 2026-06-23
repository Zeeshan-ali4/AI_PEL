from app.context import fixtures


def test_fixtures_are_labelled_as_demo_enterprise_stand_ins():
    notice = fixtures.DEMO_FIXTURE_NOTICE.lower()
    assert "demo fixtures" in notice
    assert "stand-ins" in notice

    labels = " ".join(fixtures.FIXTURE_SYSTEM_LABELS.values()).lower()
    for system in (
        "iam",
        "crm",
        "fraud",
        "sanctions",
        "payment-history",
        "approval",
        "disclosure-basis",
    ):
        assert system in labels

    assert fixtures.CUSTOMER_FIXTURES
    assert fixtures.PAYMENT_HISTORY_FIXTURES
    assert fixtures.APPROVAL_FIXTURES
    assert fixtures.DISCLOSURE_BASIS_BY_DOMAIN
