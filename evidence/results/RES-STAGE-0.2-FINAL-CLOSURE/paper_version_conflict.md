# Paper version conflict — read-only

Documented Intent: AI_CONTEXT/06_DECISIONS.md approves exponential rho, full-window denominator, vehicle equal weighting and bounded missingness. Latest dated PDF paper/历史记录/20261010_YYS.pdf specifies the longitudinal proxy hierarchy and postpones the mapping/aggregation to Protocol Lock.

Actual Implementation: formal_risk_measurement.v2 implements the approved design; the historical linear metric remains isolated. paper/主论文/main.tex:378-405 still describes linear threshold risk, observed-time denominator and summation over vehicles.

Evidence: latest PDF SHA in audit/provenance, readonly extracts; git-tracked main.tex:378-405.

Affected Files: paper/主论文/main.tex; paper/历史记录/20261010_YYS.pdf; AI_CONTEXT/06_DECISIONS.md.

Conflict: current TeX and latest PDF/design are not synchronized. The latest PDF leaves mapping to the lock, rather than contradicting the agreed exponential design. The paper term 'not equivalent to zero risk' refers to indicators/states; whether a reliably out-of-region or reliably not-applicable state contributes zero is governed by the approved contribution rule.

Status: Awaiting Researcher Decision. Researcher identifies the canonical manuscript/version and resolves text later; no manuscript modified, no measurement definition changed. This is not a computational failure of Stage 0.2.
