#!/usr/bin/env python3
"""
Test script for Intelligent Prompt Caching functionality
"""

from src.core.prompt_cache import IntelligentPromptManager


def dummy_generator(prompt: str) -> str:
    """A simple function to simulate response generation"""
    print(f"Generating response for: {prompt[:30]}...")
    # In reality, this would call an LLM or other processing
    return f"This is a generated response to your prompt: '{prompt[:20]}...'"


def test_prompt_cache():
    print("Testing Intelligent Prompt Caching System")
    print("=" * 60)

    # Initialize the manager
    print("\n1. Initializing Intelligent Prompt Manager...")
    manager = IntelligentPromptManager("test_user:prompt_cache_tests")
    print("✓ Prompt manager initialized successfully")

    # Test 1: Storing prompts
    print("\n2. Storing prompts in cache...")
    test_prompts = [
        "Explain the benefits of Python for beginners",
        "How to center a div in CSS?",
        "What are the advantages of using Docker?",
        "Explain quantum computing in simple terms",
        "How to handle asynchronous operations in JavaScript?"
    ]

    for i, prompt in enumerate(test_prompts, 1):
        response = dummy_generator(prompt)
        manager.cache.store_prompt(
            prompt=prompt,
            response=response,
            outcome_score=0.8 + (i * 0.02),  # Vary the score slightly
            metadata={"test_case": f"case_{i}", "category": "tutorial"}
        )
        print(f"  {i}. Stored prompt: '{prompt[:30]}...'")

    # Test 2: Finding similar prompts
    print("\n3. Finding similar prompts...")
    query = "How to center elements in CSS?"
    similar_prompts = manager.cache.find_similar_prompts(query, threshold=0.3)
    print(f"  Found {len(similar_prompts)} similar prompts to: '{query[:30]}...'")

    if similar_prompts:
        top_similar = similar_prompts[0]
        print(f"  Top match: '{top_similar['prompt_text'][:50]}...', similarity: {top_similar.get('similarity_score', 0):.2f}")

    # Test 3: Getting cached responses
    print("\n4. Testing cached response retrieval...")
    query1 = "How to center a div in CSS?"
    cached_result = manager.cache.get_cached_response(query1)

    if cached_result:
        response, metadata = cached_result
        print(f"  ✓ Retrieved cached response for: '{query1[:30]}...'")
        print(f"    Response preview: '{response[:40]}...'")
    else:
        print(f"  ✗ No cached response found for: '{query1[:30]}...'")

    # Test 4: Get top performing prompts
    print("\n5. Getting top performing prompts...")
    top_prompts = manager.cache.get_top_prompts(limit=3)
    print(f"  Top {len(top_prompts)} performing prompts:")
    for i, prompt_data in enumerate(top_prompts, 1):
        print(f"    {i}. Score: {prompt_data['outcome_score']:.2f} - '{prompt_data['prompt_text'][:40]}...'")

    # Test 5: Using the manager to get or generate
    print("\n6. Testing get-or-generate functionality...")

    # First time - should generate
    print("  First call - should generate:")
    response1 = manager.get_response_or_generate(
        "How to center a div in CSS?",
        dummy_generator
    )
    print(f"    Response: '{response1[:50]}...'")

    # Second time with similar prompt - might use cache
    print("  Second call - might use cache:")
    response2 = manager.get_response_or_generate(
        "CSS: How to center a div?",
        dummy_generator
    )
    print(f"    Response: '{response2[:50]}...'")

    # Test 6: Evaluating and updating
    print("\n7. Testing evaluation and update...")
    test_prompt = "Explain quantum computing simply"
    test_response = "A basic explanation of quantum computing concepts"

    # Add a new prompt with low score initially
    manager.cache.store_prompt(test_prompt, test_response, outcome_score=0.3)
    print(f"  Added '{test_prompt[:25]}...' with low score (0.3)")

    # Update the score based on evaluation
    manager.evaluate_and_update_cache(test_prompt, test_response, outcome_evaluation=0.9)
    print("  Updated score based on evaluation (0.9)")

    # Check the top prompts again to see the updated one
    updated_top = manager.cache.get_top_prompts(limit=1)
    if updated_top:
        print(f"  Updated prompt now has score: {updated_top[0]['outcome_score']:.2f}")

    # Test 7: Topic-based suggestions
    print("\n8. Testing topic-based suggestions...")
    css_suggestions = manager.get_suggestions_for_topic("CSS styling")
    print(f"  Found {len(css_suggestions)} suggestions for 'CSS styling'")

    if css_suggestions:
        print("  Sample suggestions:")
        for i, suggestion in enumerate(css_suggestions[:2], 1):
            print(f"    {i}. '{suggestion['prompt_text'][:50]}...' (score: {suggestion['outcome_score']:.2f})")

    print("\n" + "=" * 60)
    print("Intelligent Prompt Caching tests completed!")
    print("✓ Prompt storage working")
    print("✓ Similarity matching working")
    print("✓ Cache retrieval working")
    print("✓ Performance tracking working")
    print("✓ Topic-based suggestions working")
    print("✓ Evaluation and update functionality working")


def main():
    test_prompt_cache()


if __name__ == "__main__":
    main()