package evidence

import rego.v1

required := {
  "eval.json",
  "model/model.joblib",
  "model/train_meta.json",
  "docs/intended-purpose.md",
  "docs/human-oversight.md",
  "docs/data-governance.md",
  "docs/risk-notes.md",
  "docs/traceability.md",
}

# In CI we also require supply-chain artifacts:
required_ci := {
  "sbom.spdx.json",
  "trivy.sarif",
}

files := {f.path | f := input.files[_]}

deny contains msg if {
  some p in required
  not (p in files)
  msg := sprintf("missing required file: %s", [p])
}

deny contains msg if {
  some p in required_ci
  not (p in files)
  msg := sprintf("missing required CI file: %s", [p])
}

deny contains msg if {
  some f in input.files
  startswith(f.path, "docs/")
  f.bytes < 10
  msg := sprintf("doc too small (likely empty): %s", [f.path])
}