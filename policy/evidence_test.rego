# Unit tests for policy/evidence.rego. Run with: conftest verify --policy policy

package evidence_test

import data.evidence

# Full manifest (all required + required_ci, docs with bytes >= 10) must not be denied
test_full_manifest_passes if {
	manifest := {
		"files": [
			{"path": "eval.json", "bytes": 100},
			{"path": "model/model.joblib", "bytes": 200},
			{"path": "model/train_meta.json", "bytes": 300},
			{"path": "docs/intended-purpose.md", "bytes": 50},
			{"path": "docs/human-oversight.md", "bytes": 50},
			{"path": "docs/data-governance.md", "bytes": 50},
			{"path": "docs/risk-notes.md", "bytes": 50},
			{"path": "docs/traceability.md", "bytes": 50},
			{"path": "sbom.spdx.json", "bytes": 100},
			{"path": "trivy.sarif", "bytes": 100},
		],
	}
	count(evidence.deny) == 0 with input as manifest
}

# Missing a required file must produce the expected deny message
test_missing_required_file_denied if {
	manifest := {
		"files": [
			{"path": "eval.json", "bytes": 100},
			{"path": "model/model.joblib", "bytes": 200},
			{"path": "model/train_meta.json", "bytes": 300},
			{"path": "docs/intended-purpose.md", "bytes": 50},
			{"path": "docs/human-oversight.md", "bytes": 50},
			{"path": "docs/data-governance.md", "bytes": 50},
			{"path": "docs/risk-notes.md", "bytes": 50},
			# docs/traceability.md intentionally omitted
			{"path": "sbom.spdx.json", "bytes": 100},
			{"path": "trivy.sarif", "bytes": 100},
		],
	}
	"missing required file: docs/traceability.md" in evidence.deny with input as manifest
}

# Missing a required CI file must produce the expected deny message
test_missing_ci_file_denied if {
	manifest := {
		"files": [
			{"path": "eval.json", "bytes": 100},
			{"path": "model/model.joblib", "bytes": 200},
			{"path": "model/train_meta.json", "bytes": 300},
			{"path": "docs/intended-purpose.md", "bytes": 50},
			{"path": "docs/human-oversight.md", "bytes": 50},
			{"path": "docs/data-governance.md", "bytes": 50},
			{"path": "docs/risk-notes.md", "bytes": 50},
			{"path": "docs/traceability.md", "bytes": 50},
			{"path": "sbom.spdx.json", "bytes": 100},
			# trivy.sarif intentionally omitted
		],
	}
	"missing required CI file: trivy.sarif" in evidence.deny with input as manifest
}

# Doc with bytes < 10 must be denied
test_doc_too_small_denied if {
	manifest := {
		"files": [
			{"path": "eval.json", "bytes": 100},
			{"path": "model/model.joblib", "bytes": 200},
			{"path": "model/train_meta.json", "bytes": 300},
			{"path": "docs/intended-purpose.md", "bytes": 5},
			{"path": "docs/human-oversight.md", "bytes": 50},
			{"path": "docs/data-governance.md", "bytes": 50},
			{"path": "docs/risk-notes.md", "bytes": 50},
			{"path": "docs/traceability.md", "bytes": 50},
			{"path": "sbom.spdx.json", "bytes": 100},
			{"path": "trivy.sarif", "bytes": 100},
		],
	}
	"doc too small (likely empty): docs/intended-purpose.md" in evidence.deny with input as manifest
}
