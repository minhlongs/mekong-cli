# Step 17 — Risk and Scenario OS

## Business
| Risk | Signal | Response |
|---|---|---|
| No meaningful user problem | Interviews produce no repeated urgent job | Narrow or change ICP before expanding features |
| Users try once and do not return | Low repeated workflow use | Diagnose first-value and reliability; pause acquisition |
| No willingness to pay | Positive feedback but no paid commitment | Revisit buyer, outcome, or offer; do not invent pricing |
| Delivery costs exceed value | Model, hosting, or support cost rises | Measure per workflow and constrain scope |
| Dependency or provider outage | Failed runs or elevated latency | Offer clear failure handling and tested provider fallbacks |
| Unsafe or incorrect agent action | Verification failure or unintended side effect | Reduce permissions, add human approval, preserve rollback |
| Privacy/legal mismatch | Data flow or provider changes | Stop affected processing; reassess with counsel |

## Agentic
OPS monitors service health and incidents; Engineering owns recovery; Governance tracks data and regulatory changes; the founder decides whether to stop, narrow, or continue a pilot.

## Governance
Use the risk levels and approval paths in docs/autonomy-model.md. Preserve incident evidence, notify affected users when required, and test recovery. Do not present a scenario likelihood as measured probability without a basis.
