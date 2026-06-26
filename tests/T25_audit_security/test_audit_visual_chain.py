"""Tests for the T25 visual chain affordances in the audit UI."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.web.routes import _build_audit_rows


def test_audit_log_shows_green_links_and_package_download(wired_pipeline, write_sample_record):
    client = TestClient(app)
    write_sample_record(wired_pipeline.audit_store)

    page = client.get("/audit").text
    assert "Download audit package" in page
    assert "/audit/export.json" in page
    assert "Green link" in page
    assert "prev matches genesis" in page
    assert "Demo integrity check only" in page


def test_audit_log_shows_broken_link_mismatch_after_tampering(wired_pipeline, write_sample_record):
    client = TestClient(app)
    record = write_sample_record(wired_pipeline.audit_store)

    tamper_response = client.post("/audit/simulate-tampering", data={"record_id": record.id}, follow_redirects=True)
    assert tamper_response.status_code == 200
    page = tamper_response.text

    assert "Chain broken" in page
    assert "Broken link" in page or "record_hash mismatch" in page
    assert "expected" in page or "mismatch" in page


def test_record_view_links_case_level_audit_package(wired_pipeline, write_sample_record):
    client = TestClient(app)
    record = write_sample_record(wired_pipeline.audit_store)

    page = client.get(f"/records/{record.record_hash}").text
    assert "Download audit package for this case" in page
    assert f"/audit/export.json?correlation_id={record.correlation_id}" in page
    assert "production would use signed attestation" in page


def test_audit_log_record_hash_mismatch_exposes_stored_and_recomputed_hashes(wired_pipeline, write_sample_record):
    client = TestClient(app)
    record = write_sample_record(wired_pipeline.audit_store)

    tamper_response = client.post("/audit/simulate-tampering", data={"record_id": record.id}, follow_redirects=True)
    assert tamper_response.status_code == 200
    page = tamper_response.text
    tampered_row = _build_audit_rows(wired_pipeline.audit_store.read_records())[0]

    assert "Record hash mismatch" in page
    assert "stored record_hash" in page
    assert "recomputed expected" in page
    assert record.record_hash in page
    assert tampered_row["recomputed_record_hash"] in page
    assert tampered_row["recomputed_record_hash"] != record.record_hash
