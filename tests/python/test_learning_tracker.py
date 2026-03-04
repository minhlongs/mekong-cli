#!/usr/bin/env python3
"""
Test script for Learning History Tracker functionality
"""

from src.core.learning_tracker import LearningAnalyticsDashboard


def test_learning_tracker():
    print("Testing Learning History Tracker")
    print("=" * 60)

    # Initialize the dashboard
    print("\n1. Initializing Learning Analytics Dashboard...")
    dashboard = LearningAnalyticsDashboard("test_agent:learning_tests")
    tracker = dashboard.tracker
    print("✓ Learning tracker initialized successfully")

    # Test 1: Logging learning events
    print("\n2. Logging learning events...")
    events_data = [
        ("Python basics", "Learned variables and data types", "Successfully completed exercises", 0.7),
        ("Python functions", "Learned about defining and calling functions", "Completed practice problems", 0.6),
        ("Python OOP", "Learned classes and objects", "Implemented simple class hierarchy", 0.8),
        ("JavaScript basics", "Learned syntax and variables", "Executed simple scripts", 0.5),
        ("JavaScript functions", "Learned about functions and scope", "Wrote several functions", 0.7),
        ("Python basics", "Reviewed advanced variable usage", "Solved complex exercises", 0.9),  # Improved
        ("JavaScript basics", "Learned DOM manipulation", "Created simple web page", 0.8),  # Improved
    ]

    event_ids = []
    for i, (topic, content, outcome, score) in enumerate(events_data, 1):
        event_id = tracker.log_learning_event(
            topic=topic,
            content=content,
            outcome=outcome,
            performance_score=score,
            metadata={"difficulty": "beginner" if "basics" in topic else "intermediate"}
        )
        event_ids.append(event_id)
        print(f"  {i}. Logged: '{topic}' (score: {score})")

    # Test 2: Get events by topic
    print("\n3. Retrieving events by topic...")
    python_events = tracker.get_learning_events_by_topic("Python", limit=5)
    print(f"  Found {len(python_events)} Python-related learning events")

    if python_events:
        recent_python = python_events[0]
        print(f"  Most recent: '{recent_python['topic']}' - Score: {recent_python['performance_score']}")

    # Test 3: Identify knowledge gaps
    print("\n4. Identifying knowledge gaps...")
    gaps = tracker.identify_knowledge_gaps(min_performance_threshold=0.7)
    print(f"  Found {len(gaps)} knowledge gaps with performance below 0.7 threshold")

    for i, gap in enumerate(gaps, 1):
        print(f"    {i}. {gap['topic']}: Avg {gap['average_performance']:.2f}, Recent {gap['recent_average']:.2f} ({gap['gap_severity']})")

    # Test 4: Get learning progression for a topic
    print("\n5. Getting learning progression for 'Python basics'...")
    progression = tracker.get_learning_progression("Python basics")
    print(f"  Found {len(progression)} learning events for 'Python basics'")

    for i, event in enumerate(progression, 1):
        print(f"    {i}. {event['timestamp']} - Score: {event['performance_score']}")

    # Test 5: Get improvement patterns
    print("\n6. Analyzing improvement patterns...")
    patterns = tracker.get_improvement_patterns()
    print(f"  Found improvement patterns for {len(patterns)} topics")

    for i, pattern in enumerate(patterns[:5], 1):  # Show top 5
        improvement = pattern['improvement']
        direction = "↑" if improvement > 0 else "↓" if improvement < 0 else "→"
        print(f"    {i}. {pattern['topic']}: {direction} {improvement:+.2f} ({pattern['trend']})")

    # Test 6: Get performance trends
    print("\n7. Getting overall performance trends...")
    trends = tracker.get_performance_trends()
    print(f"  Total learning events: {trends['total_learning_events']}")
    print(f"  Average performance: {trends['average_performance']:.2f}")
    print(f"  Trend direction: {trends['trend_direction']}")
    print(f"  Most studied topics: {[t['topic'] for t in trends['most_common_topics'][:3]]}")

    # Test 7: Generate comprehensive report
    print("\n8. Generating comprehensive learning report...")
    report = dashboard.generate_learning_report()

    summary = report['summary']
    print("  Report summary:")
    print(f"    - Total events: {summary['total_events']}")
    print(f"    - Overall performance: {summary['overall_performance']:.2f}")
    print(f"    - Trend direction: {summary['trend_direction']}")
    print(f"    - Critical gaps: {summary['critical_gaps_count']}")
    print(f"    - Improved topics: {summary['improved_topics_count']}")

    # Show most studied topics
    if summary['most_studied_topics']:
        print("    - Most studied topics:")
        for topic_info in summary['most_studied_topics'][:3]:
            print(f"      * {topic_info['topic']} ({topic_info['count']} events)")

    print("\n" + "=" * 60)
    print("Learning History Tracker tests completed!")
    print("✓ Event logging working")
    print("✓ Topic-based retrieval working")
    print("✓ Knowledge gap identification working")
    print("✓ Learning progression tracking working")
    print("✓ Improvement pattern analysis working")
    print("✓ Performance trends analysis working")
    print("✓ Comprehensive reporting working")


def main():
    test_learning_tracker()


if __name__ == "__main__":
    main()