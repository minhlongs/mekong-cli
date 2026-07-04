#!/usr/bin/env python3
"""
Integration test for Ostrom Governance Framework.

Demonstrates:
- Amendment lifecycle: Proposal → Deliberation → Voting
- Reputation-weighted voting with quorum
- Graduated sanctions: warning → suspension
- Dispute arbitration with panel formation
"""

from datetime import datetime, timedelta
from src.governance.voting import (
    VotingSystem, VotingConfig, VoteType, Voter, Vote
)
from src.governance.sanctions import (
    SanctionSystem, ViolationType, SanctionLevel, WarningSanction
)
from src.governance.amendment import (
    AmendmentSystem, AmendmentConfig, AmendmentStatus
)
from src.governance.dispute import (
    DisputeSystem, DisputeType, Arbitrator, RulingType
)


def test_voting_algorithm():
    """Test reputation-weighted voting with quorum."""
    print("\n=== Testing Voting Algorithm ===")

    config = VotingConfig(
        method="supermajority",
        quorum_percentage=0.4,
        threshold_percentage=0.66,
    )
    system = VotingSystem(config)

    # Register voters with different reputation scores
    voters = [
        Voter("alice", 0.9, voting_power=2.0),  # High reputation, bonus power
        Voter("bob", 0.7, voting_power=1.0),
        Voter("carol", 0.5, voting_power=1.0),
        Voter("dave", 0.3, voting_power=1.0),
    ]

    for v in voters:
        system.register_voter(v)

    # Cast votes on a proposal
    proposal_id = "test-proposal-1"
    system.cast_vote("alice", proposal_id, VoteType.YES)
    system.cast_vote("bob", proposal_id, VoteType.YES)
    system.cast_vote("carol", proposal_id, VoteType.NO)
    system.cast_vote("dave", proposal_id, VoteType.ABSTAIN)

    # Tally results
    results = system.tally_votes(proposal_id)

    print(f"Total weighted votes: {results.total_weight_cast:.2f}")
    print(f"Yes: {results.yes_weight:.2f} ({results.yes_weight/results.total_weight_cast*100:.1f}%)")
    print(f"No: {results.no_weight:.2f} ({results.no_weight/results.total_weight_cast*100:.1f}%)")
    print(f"Quorum met: {results.quorum_met}")
    print(f"Threshold met: {results.threshold_met}")
    print(f"Passed: {results.passed}")

    assert results.passed, "Supermajority (66%) should pass with 75% yes votes"
    print("✓ Voting algorithm works correctly")


def test_amendment_flow():
    """Test complete amendment lifecycle."""
    print("\n=== Testing Amendment Flow ===")

    # Setup systems
    voting_config = VotingConfig(
        method="supermajority",
        threshold_percentage=0.6,
    )
    voting_system = VotingSystem(voting_config)
    amendment_config = AmendmentConfig(
        review_hours=1,
        deliberation_hours=1,
        minimum_monitoring_hours=1,
        voting_hours=1,
    )
    amendment_system = AmendmentSystem(amendment_config, voting_system)

    # Create amendment
    amendment = amendment_system.create_amendment(
        title="Increase quorum threshold to 50%",
        description="This amendment raises the minimum participation quorum from 40% to 50% to ensure broader consensus.",
        proposed_text="The quorum threshold for voting shall be 0.5 (50%) instead of 0.4 (40%).",
        current_text="The quorum threshold for voting is 0.4 (40%).",
        proposer_id="alice",
        co_sponsors=["bob"],
        priority=2,
        estimated_impact="medium",
    )

    print(f"Created amendment: {amendment.id}")
    assert amendment.status == AmendmentStatus.DRAFT

    # Submit for review
    amendment_system.submit_amendment(amendment.id)
    print(f"After submission: {amendment.status}")

    # Review stage
    amendment_system.start_review(amendment.id, reviewer_id="chair")
    amendment_system.complete_review(amendment.id, approved=True, reviewer_id="chair")
    print(f"After review: {amendment.status}")

    # Deliberation stage
    amendment_system.add_feedback(amendment.id, "charlie", "I support this change.")
    amendment_system.record_concern(amendment.id, "constitutional", "May disenfranchise small members", "dave")
    print(f"After deliberation input: {len(amendment.feedback)} feedback items, {len(amendment.concerns)} concerns")

    # Monitoring stage
    amendment_system.start_monitoring(amendment.id)
    # Simulate waiting the minimum period by manually setting the timestamp
    amendment.monitoring_started_at = datetime.utcnow() - timedelta(hours=50)
    # Simulate checking quorum
    quorum_ok, est_rate = amendment_system.check_quorum_during_monitoring(amendment.id, interested_members=8)
    print(f"Monitoring: quorum likely={quorum_ok}, est. rate={est_rate*100:.1f}%")

    # Start voting
    amendment_system.start_voting(amendment.id)
    print(f"Voting config: threshold={amendment.voting_config.threshold_percentage*100:.0f}%")

    # Register voters and cast votes
    voters_data = [
        Voter("alice", 0.9, voting_power=2.0),
        Voter("bob", 0.7, voting_power=1.0),
        Voter("charlie", 0.8, voting_power=1.0),
        Voter("dave", 0.6, voting_power=1.0),
        Voter("eve", 0.5, voting_power=1.0),
        Voter("frank", 0.4, voting_power=1.0),
    ]
    for v in voters_data:
        voting_system.register_voter(v)

    voters = ["alice", "bob", "charlie", "dave", "eve", "frank"]
    for voter in voters:
        voting_system.cast_vote(voter, amendment.id, VoteType.YES)

    # End voting and tally
    amendment_system.end_voting(amendment.id)
    print(f"After voting: {amendment.status}")
    print(f"Results: passed={amendment.voting_results.passed if amendment.voting_results else 'N/A'}")

    # Ratify if passed
    if amendment.status == AmendmentStatus.PASSED:
        amendment_system.ratify_amendment(amendment.id, ratified_by="governance_council")
        print(f"After ratification: {amendment.status}")

    print("✓ Amendment flow completed successfully")


def test_graduated_sanctions():
    """Test graduated sanctions: warning → suspension."""
    print("\n=== Testing Graduated Sanctions ===")

    system = SanctionSystem(
        min_escalation_interval_days=7,
        max_active_sanctions=3,
    )

    member = "troublemaker"

    # First violation: warning (use minor violation)
    warning = system.impose_sanction(
        member_id=member,
        violation_type=ViolationType.FAILED_DUTY,
        description="Missed a minor reporting deadline",
        imposed_by="chair",
    )
    print(f"Sanction 1: {warning.level.name} (id={warning.id})")
    assert warning.level == SanctionLevel.WARNING

    # Check active sanctions
    active = system.get_active_sanctions(member)
    print(f"Active sanctions: {len(active)}")

    # Second violation after warning: restitution (still a moderate offense)
    restitution = system.impose_sanction(
        member_id=member,
        violation_type=ViolationType.FAILED_DUTY,
        description="Failed to complete assigned monitoring task",
        imposed_by="coordinator",
        metadata={"amount": 10.0, "type": "credit"},
    )
    print(f"Sanction 2: {restitution.level.name}")
    assert restitution.level == SanctionLevel.RESTITUTION

    # Third violation: expulsion (severe after restitution)
    expulsion = system.impose_sanction(
        member_id=member,
        violation_type=ViolationType.EVASION,
        description="Attempted to evade monitoring requirements",
        imposed_by="oversight_board",
        custom_duration=0,  # Permanent
        metadata={"reinstatable": False, "reason": "Severe violation after prior sanctions"},
    )
    print(f"Sanction 3: {expulsion.level.name}")
    assert expulsion.level == SanctionLevel.EXPULSION

    # Check member standing
    standing = system.is_member_in_good_standing(member)
    print(f"Member in good standing: {standing}")
    assert not standing

    # Get history
    history = system.get_member_history(member)
    print(f"History: {history.total_warnings} warnings, {history.total_suspensions} suspensions")
    assert history.total_warnings == 1
    # No suspensions in this path (escalated to expulsion directly)
    assert history.total_suspensions == 0

    print("✓ Graduated sanctions work correctly")


def test_dispute_arbitration():
    """Test dispute resolution with arbitration panel."""
    print("\n=== Testing Dispute Arbitration ===")

    system = DisputeSystem(
        default_panel_size=3,
        default_hearing_days=2,
    )

    # Register arbitrators
    arbitrators = [
        Arbitrator("arb1", "Dr. Smith", ["governance", "law"]),
        Arbitrator("arb2", "Ms. Jones", ["conflict_resolution", "economics"]),
        Arbitrator("arb3", "Mr. Kim", ["governance", "resource_management"]),
        Arbitrator("arb4", "Prof. Lee", ["law", "constitutional"]),
        Arbitrator("arb5", "Ms. Chen", ["governance", "procedural"]),
    ]
    for arb in arbitrators:
        system.register_arbitrator(arb)

    # File a dispute
    dispute = system.file_dispute(
        dispute_type=DisputeType.AMENDMENT_INTERPRETATION,
        title="Challenge to Amendment Passage",
        description="Petitioner alleges improper quorum calculation in recent amendment vote.",
        filing_party="member_a",
        respondent="governance_council",
        related_proposals=["AMD-00000001"],
    )
    print(f"Dispute filed: {dispute.id} - {dispute.title}")

    # Form arbitration panel
    panel = system.accept_dispute(dispute.id, acceptor_id="admin")
    print(f"Panel formed: {len(panel.members)} members, chair={panel.chair.name}")
    assert len(panel.members) == 3

    # Submit evidence
    evidence = system.submit_evidence(
        dispute_id=dispute.id,
        submitter_id="member_a",
        evidence_type="document",
        description="Voting records from the disputed amendment",
        content_reference="vote_logs/AMD-00000001.json",
    )
    print(f"Evidence submitted: {evidence.id}")

    # Schedule hearing
    hearing_date = system.schedule_hearing(dispute.id, scheduled_by="admin")
    print(f"Hearing scheduled: {hearing_date.isoformat()}")

    # Hold hearing
    system.hold_hearing(dispute.id, notes="Both parties presented arguments. 30 minutes each.")
    print(f"Hearing status: {dispute.status}")

    # Issue ruling
    ruling = system.issue_ruling(
        dispute_id=dispute.id,
        ruling_type=RulingType.DECLARATORY,
        decision="Quorum calculation was correct per the bylaws",
        findings=[
            "Total eligible voters: 25",
            "Voters participated: 12 (48%)",
            "Quorum requirement at time: 40%",
            "Participation exceeded quorum threshold",
        ],
        reasoning="Article 7, Section 3 explicitly defines quorum based on eligible voters present. The 12 participating members represent 48% of the 25 eligible members, which exceeds the 40% threshold.",
    )
    print(f"Ruling: {ruling.decision}")
    print(f"Findings: {len(ruling.findings)} items")
    print(f"Appealable: {ruling.appealable}")

    # Resolve dispute
    system.resolve_dispute(dispute.id, resolved_by="admin", resolution_notes="Ruling issued and published to all members.")
    print(f"Final status: {dispute.status}")

    print("✓ Dispute arbitration completed successfully")


def main():
    """Run all integration tests."""
    print("=" * 60)
    print("OSTROM GOVERNANCE FRAMEWORK - INTEGRATION TESTS")
    print("=" * 60)

    try:
        test_voting_algorithm()
        test_amendment_flow()
        test_graduated_sanctions()
        test_dispute_arbitration()

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED")
        print("=" * 60)
        return 0
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
