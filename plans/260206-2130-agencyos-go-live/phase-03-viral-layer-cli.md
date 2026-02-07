# Phase 3: Viral Layer (CLI)

## Context
The Mekong CLI is the developer interface. It must be robust, helpful, and correctly execute recipes.

## Verification Checklist

### 1. Installation & Init
- [ ] Install locally: `pip install -e .`.
- [ ] Run `mekong --help`: Verify Typer help text appears.
- [ ] Run `mekong init`:
    - Verify `.mekong/` directory is created.
    - Verify `recipes/` directory is created.

### 2. Recipe Management
- [ ] Run `mekong list`: Should show empty list or default recipes.
- [ ] Create `recipes/test-recipe.md`:
    ```markdown
    # Test Recipe
    Description: A simple test.

    ## Steps
    1. Echo Hello
       echo "Hello World"
    ```
- [ ] Run `mekong list`: Verify "Test Recipe" appears.

### 3. Execution Engine
- [ ] Run `mekong run recipes/test-recipe.md`.
- [ ] Verify output:
    - "🚀 Running: Test Recipe"
    - "Step 1: Echo Hello"
    - "Output: Hello World"
    - "✨ Recipe 'Test Recipe' completed successfully!"

### 4. Interactive UI
- [ ] Run `mekong ui`.
- [ ] Verify Rich-based UI loads.
- [ ] Navigate menu options (1. LeadHunter, 2. ContentWriter).
- [ ] Verify input prompts work.
