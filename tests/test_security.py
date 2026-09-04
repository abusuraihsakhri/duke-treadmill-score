"""
Tests for security features: PHI guard and audit trail.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import os
from agents.base import PHIGuard, AuditTrail, AuditLogger, SecurityException


class TestPHIGuard:
    def test_ssn_detection(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Patient SSN: 123-45-6789")

    def test_mrn_detection(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("MRN-12345678")

    def test_phone_detection(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Call 555-123-4567")

    def test_email_detection(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Email: patient@example.com")

    def test_clean_text_passes(self):
        PHIGuard.assert_no_phi("Analytical assay specimen KEY-001 optimal")
        PHIGuard.assert_no_phi("")
        PHIGuard.assert_no_phi(None)

    def test_redact_phi(self):
        result = PHIGuard.redact_phi("Patient MRN-12345678 is here")
        assert "REDACTED_IDENTIFIER" in result
        assert "MRN-12345678" not in result


class TestAuditTrail:
    def test_auto_generated_key(self):
        """AuditTrail should auto-generate a key when none provided."""
        trail = AuditTrail()
        assert len(trail.secret_key) > 0

    def test_custom_key(self):
        """AuditTrail should use provided key."""
        trail = AuditTrail(secret_key="my-custom-key")
        assert trail.secret_key == b"my-custom-key"

    def test_env_key(self):
        """AuditTrail should use key from environment variable."""
        os.environ["AUDIT_SECRET_KEY"] = "env-key-123"
        trail = AuditTrail()
        assert trail.secret_key == b"env-key-123"
        del os.environ["AUDIT_SECRET_KEY"]

    def test_log_creates_entry(self):
        trail = AuditTrail()
        entry = trail.log("test_actor", "test_tier", "TEST_EVENT", {"key": "value"})
        assert entry["audit_id"].startswith("AUDIT-")
        assert entry["actor"] == "test_actor"
        assert entry["event_type"] == "TEST_EVENT"
        assert entry["prev_hash"] == "GENESIS_BLOCK_0000000000000000"

    def test_chain_integrity(self):
        trail = AuditTrail()
        trail.log("actor1", "tier1", "EVENT1", {"a": 1})
        trail.log("actor2", "tier2", "EVENT2", {"b": 2})
        trail.log("actor3", "tier3", "EVENT3", {"c": 3})
        assert trail.verify_integrity() is True

    def test_tamper_detection(self):
        trail = AuditTrail()
        trail.log("actor1", "tier1", "EVENT1", {"a": 1})
        trail.log("actor2", "tier2", "EVENT2", {"b": 2})
        # Tamper with the chain
        trail.logs[0]["current_hash"] = "TAMPERED_HASH"
        assert trail.verify_integrity() is False

    def test_phi_blocked_in_audit(self):
        """Audit trail should reject PHI-containing payloads."""
        trail = AuditTrail()
        with pytest.raises(SecurityException):
            trail.log("actor", "tier", "EVENT", {"patient": "MRN-12345678"})

    def test_get_trail(self):
        trail = AuditTrail()
        trail.log("actor1", "tier1", "EVENT1", {"a": 1})
        assert len(trail.get_trail()) == 1
