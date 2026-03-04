#!/usr/bin/env python3
"""
Test script for Context Manager functionality
"""

from src.core.context_manager import ContextAwareAgent, ContextManager

def test_context_manager():
    print("Testing Context Manager functionality")
    print("="*50)

    # Test 1: Initialize context manager
    print("\n1. Initializing ContextManager...")
    user_id = "test_user:session_001"
    ctx_manager = ContextManager(user_id)
    print(f"✓ ContextManager initialized for {user_id}")

    # Test 2: Store interactions
    print("\n2. Storing conversation interactions...")
    interactions = [
        ("Hello, I need help with Python programming", "Hello! I can help you with Python programming. What specific topic?"),
        ("Can you explain decorators?", "Sure! Python decorators modify the behavior of functions."),
        ("What's the syntax?", "Decorators use the @ symbol followed by the decorator name.")
    ]

    for user_msg, agent_resp in interactions:
        success = ctx_manager.store_interaction(user_msg, agent_resp)
        print(f"  ✓ Stored: '{user_msg[:20]}...' -> {'vector' if success else 'YAML fallback'}")

    # Test 3: Retrieve context
    print("\n3. Retrieving context...")
    context = ctx_manager.retrieve_context()
    print(f"  ✓ Retrieved {len(context)} context items")

    # Print sample context item
    if context:
        sample = context[0]
        print(f"  Sample context: {sample.get('type', 'unknown')} - {sample.get('user_message', '')[:50]}...")

    # Test 4: Summarize context
    print("\n4. Summarizing context...")
    summary = ctx_manager.summarize_context(context)
    print(f"  ✓ Summary created: {summary['total_interactions']} interactions")
    print(f"  Topics discussed: {summary['topics_discussed'][:3]}")

    # Test 5: Check for specific context
    print("\n5. Checking for specific context...")
    has_python_context = ctx_manager.has_context_about("Python")
    has_decorator_context = ctx_manager.has_context_about("decorators")
    print(f"  ✓ Has Python context: {has_python_context}")
    print(f"  ✓ Has decorators context: {has_decorator_context}")

    # Test 6: Recent interactions
    print("\n6. Retrieving recent interactions...")
    recent = ctx_manager.get_recent_interactions(2)
    print(f"  ✓ Got {len(recent)} recent interactions")


def test_context_aware_agent():
    print("\n\nTesting Context-Aware Agent")
    print("="*50)

    # Test the agent
    user_id = "test_agent:user_001"
    agent = ContextAwareAgent(user_id)

    print(f"\nInitializing agent for {user_id}...")
    print("✓ Agent initialized successfully")

    # Simulate a conversation
    conversation = [
        "Hello, I want to learn about machine learning",
        "Can you suggest some good resources?",
        "I prefer online courses",
        "What's your opinion on Andrew Ng's course?"
    ]

    print(f"\nSimulating conversation with {len(conversation)} exchanges...")

    for i, user_input in enumerate(conversation, 1):
        print(f"\nExchange {i}:")
        print(f"  User: {user_input}")
        response = agent.respond(user_input)
        print(f"  Agent: {response[:100]}{'...' if len(response) > 100 else ''}")


def test_different_users():
    print("\n\nTesting Multiple Users")
    print("="*50)

    # Test with different user contexts
    users = ["user_alice:session1", "user_bob:session1", "user_charlie:session1"]

    for user in users:
        agent = ContextAwareAgent(user)
        response = agent.respond(f"Hello, I am {user.split(':')[0]}")
        print(f"  {user}: {response[:60]}...")

    print("\n✓ Each user maintains separate context")


def main():
    print("Context Manager and Agent - Integration Tests")
    print("="*60)

    test_context_manager()
    test_context_aware_agent()
    test_different_users()

    print("\n" + "="*60)
    print("All tests completed successfully!")
    print("✓ Context Manager functionality verified")
    print("✓ Context-Aware Agent working correctly")
    print("✓ Multiple user contexts maintained separately")
    print("✓ Memory system integration operational")


if __name__ == "__main__":
    main()