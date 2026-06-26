"""Tests for the T25 tamper-evident audit package export."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.audit.store import canonical_json
from app.main import app


def test_audit_package_includes_records_chain_explanation_and_stable_hash(store, write_sample_record):
    first = write_sample_record(store)
    write_sample_record(store)

    package = store.export_audit_package(correlation_id=first.correlation_id)
    repeat = store.export_audit_package(correlation_id=first.correlation_id)

    assert package == repeat
    assert package["selection"]["correlation_id"] == str(first.correlation_id)
    assert package["selection"]["record_count"] == 1
    assert "Demo integrity check" in package["header"]["integrity_model"]
    assert "not production-grade signing" in package["header"]["demo_attestation_notice"]
    assert len(package["package_integrity_hash"]) == 64

    record = package["records"][0]
    link = package["chain_links"][0]
    assert record["record_hash"] == link["record_hash"]
    assert record["prev_hash"] == link["prev_hash"]
    assert "expected_prev_hash" in link
    assert "link_intact" in link

    without_hash = {key: value for key, value in package.items() if key != "package_integrity_hash"}
    assert canonical_json(without_hash)


def test_audit_package_hash_changes_when_selected_record_changes(store, write_sample_record):
    first = write_sample_record(store)
    original_package = store.export_audit_package(correlation_id=first.correlation_id)
    record_id = original_package["records"][0]["id"]

    store.simulate_tampering(record_id)
    changed_package = store.export_audit_package(correlation_id=first.correlation_id)

    assert changed_package["records"][0]["executed"] != original_package["records"][0]["executed"]
    assert changed_package["package_integrity_hash"] != original_package["package_integrity_hash"]


def test_audit_package_route_downloads_json_for_all_or_correlation_id(wired_pipeline, write_sample_record):
    client = TestClient(app)
    record = write_sample_record(wired_pipeline.audit_store)

    all_response = client.get("/audit/export.json")
    assert all_response.status_code == 200
    assert "attachment" in all_response.headers.get("content-disposition", "")
    assert all_response.json()["selection"]["record_count"] >= 1
    assert "package_integrity_hash" in all_response.json()

    scoped_response = client.get(f"/audit/export.json?correlation_id={record.correlation_id}")
    assert scoped_response.status_code == 200
    scoped = scoped_response.json()
    assert scoped["selection"]["correlation_id"] == str(record.correlation_id)
    assert [item["correlation_id"] for item in scoped["records"]] == [str(record.correlation_id)]
