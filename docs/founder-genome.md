# Founder Genome

> Capturing the psychological and strategic profile of founders to personalize the ZenOS AI experience

**Last Updated**: 2026-06-18  
**Implementation**: `src/services/genome_service.py`, `src/models/founder_genome.py`  
**CLI Commands**: `mekong genome init`, `mekong genome view`, `mekong genome similar`  
**Related**: [`docs/constitutional-ai.md`](./constitutional-ai.md), [`docs/economic-particles.md`](./economic-particles.md)

---

## Overview

The Founder Genome system captures a founder's psychological profile, decision patterns, and strategic preferences in an encrypted format. This profile:

1. **Personalizes AI behavior** — Tailors agent interactions to founder's communication style
2. **Informs constitutional scoring** — Founder values influence principle weights
3. **Enables matching** — Find complementary co-founders, investors, team members
4. **Guides recommendations** — Growth strategy tailored to risk tolerance

### The Genome Data Structure

```
┌─────────────────────────────────────────────────────────────┐
│                    FOUNDER GENOME                          │
├─────────────────────────────────────────────────────────────┤
│ founder_id: UUID / email                                   │
│ encrypted_data: bytes (AES-256-GCM)                        │
│ encryption_key_id: str (key fingerprint)                  │
│ genome_hash: SHA-256 (deduplication)                      │
│ trait_scores: {trait: 0.0-1.0}                            │
│ cluster_id: int (founder archetype)                       │
│ analysis_summary: str (AI-generated)                      │
│ confidence_score: 0.0-1.0                                 │
│ created_at, updated_at: timestamps                        │
│ raw_genome: Optional[Dict] (decrypted in memory)         │
└─────────────────────────────────────────────────────────────┘
```

---

## The 10 Core Traits

Each trait is scored 0.0 to 1.0 (low to high) based on questionnaire responses and AI analysis.

| Trait | Definition | High Score Means | Low Score Means |
|-------|------------|------------------|-----------------|
| **risk_tolerance** | Willingness to take calculated risks | Bold, experimental | Cautious, risk-averse |
| **execution_speed** | Bias toward rapid iteration vs. careful planning | Fast mover, ship fast | Methodical, thorough |
| **capital_efficiency** | Ability to achieve more with less capital | Bootstrap specialist | Comfortable with burn |
| **vision_clarity** | Clarity and persuasiveness of long-term vision | Big picture, compelling | Grounded, incremental |
| **team_building** | Skill at recruiting, retaining, and elevating talent | People-first leader | Solo operator |
| **customer_obsession** | Depth of customer understanding and empathy | Customer-obsessed | Product-led |
| **adaptability** | Ability to pivot and learn from failure | Pivot master, resilient | Stubborn, consistent |
| **resilience** | Capacity to endure setbacks and pressure | Thick-skinned, persistent | Sensitive to feedback |
| **strategic_thinking** | Ability to see patterns and plan multiple moves ahead | Long-term strategist | Tactical executor |
| **founder_market_fit** | Alignment between founder skills and market needs | Perfect fit, domain expert | Learning on the job |

### Trait Score Interpretation

| Score Range | Interpretation |
|-------------|----------------|
| 0.0 - 0.3 | Very low (potential blind spot) |
| 0.3 - 0.5 | Below average |
| 0.5 - 0.7 | Average (typical range) |
| 0.7 - 0.9 | Above average (strength) |
| 0.9 - 1.0 | Exceptional (superpower) |

---

## Founder Clusters

Based on trait patterns, founders are assigned to one of 6 archetypal clusters:

### 1. Serial Entrepreneur

**Threshold**: `execution_speed > 0.7` AND `resilience > 0.7` AND `multiple_ventures = true`

**Characteristics**:
- Fast iteration, many projects
- High failure tolerance
- Experience-driven decision making
- Comfortable with uncertainty

**Strengths**: Speed, experience, network
**Blind Spots**: May spread too thin, lacks depth

**Ideal Co-founder**: Operator (balance execution with systems)

### 2. Visionary

**Threshold**: `vision_clarity > 0.8` AND `strategic_thinking > 0.7` AND `market_size_focus = true`

**Characteristics**:
- Sees 10-year future clearly
- Inspires others with mission
- Thinks in platforms, not products
- May overlook execution details

**Strengths**: Fundraising, team inspiration, market creation
**Blind Spots**: Day-to-day operations, product-market fit grind

**Ideal Co-founder**: Operator + multiple domain specialists

### 3. Operator

**Threshold**: `capital_efficiency > 0.7` AND `team_building > 0.7` AND `operations_experience = true`

**Characteristics**:
- Systems and processes focused
- Maximizes output with minimal input
- Builds scalable organizations
- Lean, efficient, metric-driven

**Strengths**: Unit economics, team productivity, profitability
**Blind Spots**: May miss big opportunities, too conservative

**Ideal Co-founder**: Visionary (for market vision) or Experimenter (for innovation)

### 4. Experimenter

**Threshold**: `adaptability > 0.8` AND `risk_tolerance` 0.4-0.7 AND `pivots >= 2`

**Characteristics**:
- Rapid experimentation, A/B testing mindset
- Data-driven pivot decisions
- Comfortable with ambiguity
- May lack consistent direction

**Strengths**: Product-market fit search, learning velocity
**Blind Spots**: Can be indecisive, may chase trends

**Ideal Co-founder**: Visionary (for direction) or Specialist (for depth)

### 5. Specialist

**Threshold**: `founder_market_fit > 0.8` AND `domain_experience >= 5 years`

**Characteristics**:
- Deep domain expertise
- Credibility with customers
- Focused, narrow market approach
- May resist expansion

**Strengths**: Domain authority, customer trust, competitive moat
**Blind Spots**: TAM limitations, market shifts

**Ideal Co-founder**: Visionary (for expansion) or Experimenter (for adjacent markets)

### 6. Challenger

**Threshold**: `risk_tolerance > 0.8` AND `resilience > 0.8` AND `competitive_background = true`

**Characteristics**:
- Competitive drive, disruption mindset
- Thrives under pressure
- May have contrarian views
- High stress tolerance

**Strengths**: Market entry against incumbents, fundraising (story)
**Blind Spots**: May pick unnecessary fights, team burnout risk

**Ideal Co-founder**: Operator (for stability) or Specialist (for credibility)

---

## Genome Capture Wizard

### CLI Command

```bash
mekong genome init
```

### Wizard Flow

```
┌─────────────────────────────────────────────────────────────┐
│              FOUNDER GENOME CAPTURE WIZARD                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Step 1/8: Mission Statement                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ What is the primary mission of your company?        │   │
│  │ (1-3 sentences)                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│  > "Empower Vietnamese small businesses with AI tools"    │
│                                                             │
│  AI Analysis: Strong mission clarity (0.85) ✓             │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  Step 2/8: Values Selection                                │
│  Choose 3-5 core values from ZenOS principles:            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ☑ Human Dignity First                               │   │
│  │ ☑ AI as Assistant                                   │   │
│  │ ☐ Transparency Obligation                           │   │
│  │ ☑ Micro-Enterprise First                            │   │
│  │ ☐ Right to Repair                                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  + Custom: "Vietnamese-first technology"                   │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  Step 3/8: Risk Assessment                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 1. Maximum acceptable monthly burn rate?            │   │
│  │    [50M VND]    [100M VND]   [500M VND]   [Unlimited]│   │
│  │                                                     │   │
│  │ 2. If product fails in 12 months, you would:        │   │
│  │    ○ Pivot immediately    ○ Persist 6 more months   │   │
│  │    ○ Shut down gracefully  ○ Double down            │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  Step 4/8: Strengths & Weaknesses                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Top 3 strengths:                                    │   │
│  │ 1. Technical expertise                             │   │
│  │ 2. Customer empathy                                │   │
│  │ 3. Quick learning                                  │   │
│  │                                                     │   │
│  │ Top 3 weaknesses:                                  │   │
│  │ 1. Sales experience                                │   │
│  │ 2. Financial planning                              │   │
│  │ 3. Team management                                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  Step 5/8: Experience Inventory                            │
│  Years in industry: [5]                                    │
│  Previous ventures: [2]                                    │
│  Team size experience: [1→15]                              │
│  Domain expertise: [SaaS, FinTech]                         │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  Step 6/8: AI Analysis (Processing...)                    │
│  ⠋ Analyzing trait patterns...                            │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Trait Scores:                                       │   │
│  │ • Risk Tolerance: 0.72                             │   │
│  │ • Execution Speed: 0.85                            │   │
│  │ • Capital Efficiency: 0.68                         │   │
│  │ • Vision Clarity: 0.79                             │   │
│  │ • Team Building: 0.45                              │   │
│  │                                                     │   │
│  │ Cluster: Serial Entrepreneur (78% confidence)      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  Step 7/8: Review & Edit                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Executive Summary:                                  │   │
│  │ "Founder shows strong execution orientation with    │   │
│  │   moderate risk tolerance. 5+ years domain          │   │
│  │   experience provides market credibility.          │   │
│  │   Team building identified as growth area."         │   │
│  │                                                     │   │
│  │ [Edit summary]  [Regenerate]                       │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  Step 8/8: Encryption & Save                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ✓ Genome will be encrypted with AES-256-GCM        │   │
│  │ ✓ Stored in founder_genomes database               │   │
│  │ ✓ Linked to particle on next creation              │   │
│  │                                                     │   │
│  │ [Save & Encrypt]  [Save Without Encryption]        │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## AI Analysis

The genome wizard uses LLM analysis to extract insights:

### Analysis Prompts

**Full Analysis**:
```python
ANALYSIS_PROMPT = """
You are a founder genome analyst. Analyze the following founder profile data and provide:

1. EXECUTIVE SUMMARY (2-3 paragraphs)
   - Overall founder profile and strengths
   - Key patterns in decision-making
   - Primary growth opportunities

2. TRAIT SCORES (normalized 0-1)
   For each trait, score based on responses:
   - risk_tolerance
   - execution_speed
   - capital_efficiency
   - vision_clarity
   - team_building
   - customer_obsession
   - adaptability
   - resilience
   - strategic_thinking
   - founder_market_fit

3. CLUSTER ASSIGNMENT
   Which founder cluster does this profile match?
   - Serial Entrepreneur
   - Visionary
   - Operator
   - Experimenter
   - Specialist
   - Challenger

4. CONFIDENCE SCORE (0.00-1.00)

5. KEY INSIGHTS
   - 3-5 specific, actionable observations
   - Potential blind spots or risks
   - Recommended focus areas

6. MATCHES AND COMPLEMENTARY TRAITS
   - Which founder types would complement this founder?
   - What co-founder qualities would balance weaknesses?

Respond with JSON.
"""
```

**Quick Traits**:
Extracts just trait scores without full analysis (faster, cheaper).

**Cluster Analysis**:
Determines archetype based on trait thresholds.

**Recommendations**:
Provides specific advice on:
- Co-founder matches
- Investor fit
- Hiring priorities
- Growth strategy
- Risk mitigation

---

## Storage & Encryption

### Encryption Stack

```
┌─────────────────────────────────────────────────────────────┐
│                    ENCRYPTION LAYERS                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Raw Genome JSON                                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ {"risk_tolerance": 0.72, "execution_speed": ...}   │   │
│  │ "fears": ["running out of cash", "losing control"] │   │
│  └─────────────────────────────────────────────────────┘   │
│                    │                                        │
│                    ▼                                        │
│  AES-256-GCM Encryption (or Fernet)                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ nonce(12) + ciphertext + tag(16)                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                    │                                        │
│                    ▼                                        │
│  Database Storage (PostgreSQL bytea)                      │
│  ┌─────────────────────────────────────────────────────┘   │
│  │ encrypted_data: bytes                                 │
│  │ encryption_key_id: str                                │
│  │ genome_hash: SHA-256 (for dedup)                      │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Key Management

Keys stored locally (per-machine):

```
~/.mekong/genomes/
├── .aesgcm_key          (32 bytes, mode 600)
└── data/
    └── founder_genomes.db (encrypted blobs)
```

**Key Rotation**:
```bash
# Rotate encryption key (re-encrypt all genomes)
mekong genome rotate-key

# Confirm: All genomes re-encrypted with new key
# Old key archived with timestamp
```

---

## Similarity Search

Find founders with similar trait profiles:

```bash
mekong genome similar --traits '{"risk_tolerance": 0.8, "execution_speed": 0.9}'
```

### Algorithm

Euclidean distance in trait space with cluster bonus:

```python
def calculate_similarity(target_traits: Dict, candidate_traits: Dict) -> float:
    # All traits (missing = 0.5 default)
    all_traits = set(target_traits) | set(candidate_traits)

    squared_diff = sum(
        (target_traits.get(t, 0.5) - candidate_traits.get(t, 0.5)) ** 2
        for t in all_traits
    )

    max_distance = len(all_traits) ** 0.5  # Max possible distance
    similarity = 1.0 - (squared_diff ** 0.5 / max_distance)

    # Cluster bonus: same cluster = +0.1
    if target_cluster == candidate_cluster:
        similarity = min(1.0, similarity + 0.1)

    return similarity
```

### Similarity Results

```json
{
  "target_founder": "genome_001",
  "matches": [
    {
      "founder_id": "genome_045",
      "similarity_score": 0.89,
      "matching_traits": ["high_risk_tolerance", "fast_execution", "low_team_building"],
      "divergent_traits": ["vision_clarity differs by 0.5"],
      "partnership_insight": "Both rapid executors; may compete on decisions"
    },
    {
      "founder_id": "genome_128",
      "similarity_score": 0.76,
      "matching_traits": ["high_risk", "high_adaptability"],
      "divergent_traits": ["capital_efficiency differs by 0.4"],
      "partnership_insight": "Complementary: risk-taker pairs with capital-efficient"
    }
  ]
}
```

---

## Integration with Particles

### Founder-Particle Link

When a founder creates a particle:

```python
from src.models.particle import EconomicParticle

particle = EconomicParticle(
    key_id="opc_001_abc123",
    name="My Startup",
    founder_id="genome_001",  // Links to FounderGenome
    type="opc",
    mission="Empower Vietnamese SMBs with AI"  // From genome mission
)
```

### Constitutional Personalization

Founder traits can adjust principle weights:

```python
def get_personalized_constitution(founder_id: str) -> Constitution:
    genome = genome_service.load_genome(founder_id)

    weights = ConstitutionalWeights.DEFAULTS.copy()

    # Founders with low team_building get higher human_oversight weight
    if genome.get_trait("team_building") < 0.4:
        weights[HUMAN_OVERSIGHT] = 1.3  # More human review needed

    # Founders with high risk_tolerance get higher safety weight
    if genome.get_trait("risk_tolerance") > 0.8:
        weights[SAFETY] = 1.4  // Caution with risk-takers

    return Constitution(custom_weights=weights)
```

---

## Use Cases

### 1. AI Agent Personalization

```python
from src.core.llm_client import get_client

def generate_response(founder_id: str, query: str) -> str:
    genome = genome_service.load_genome(founder_id)

    # Adjust communication style based on traits
    if genome.get_trait("execution_speed") > 0.8:
        style = "concise, action-oriented, skip preliminaries"
    else:
        style = "thorough, explain reasoning, include context"

    prompt = f"""
    Founder profile:
    - Cluster: {genome.cluster_id}
    - Execution speed: {genome.get_trait('execution_speed')}
    - Risk tolerance: {genome.get_trait('risk_tolerance')}

    Respond in {style} style.
    Query: {query}
    """

    llm = get_client()
    return llm.generate(prompt)
```

### 2. Co-founder Matching

```python
matches = genome_service.find_similar_genomes(
    trait_scores={
        "risk_tolerance": 0.7,
        "execution_speed": 0.9,
        "team_building": 0.3  # Weakness to balance
    },
    limit=5,
    exclude_founder_id="genome_001"
)

for match in matches:
    print(f"{match.founder_genome.founder_id}: {match.similarity_score:.2f}")
    print(f"  Complementary: {match.insights}")
```

### 3. Investor Recommendations

```python
def recommend_investors(genome: FounderGenome) -> List[str]:
    """Suggest investor types based on founder profile."""

    recommendations = []

    if genome.get_trait("vision_clarity") > 0.8:
        recommendations.append("Vision-focused VCs (a16z-style)")
    if genome.get_trait("capital_efficiency") > 0.7:
        recommendations.append("Micro-VCs, angel investors (bootstrap-friendly)")
    if genome.get_trait("risk_tolerance") > 0.8:
        recommendations.append("Corporate VCs (strategic, risk-tolerant)")
    if genome.get_trait("founder_market_fit") < 0.5:
        recommendations.append("Incubators with mentorship (Y Combinator)")

    return recommendations
```

---

## CLI Commands

### Initialize Genome

```bash
mekong genome init
```

Launches interactive wizard (8 steps). Stores encrypted in database.

### View Genome

```bash
mekong genome view --founder-id genome_001

# Output:
Founder Genome: genome_001
────────────────────────────────────────────────────
Cluster: Serial Entrepreneur (78% confidence)

Trait Scores:
  Risk Tolerance:       0.72 ████████░░░░
  Execution Speed:      0.85 ███████████░
  Capital Efficiency:   0.68 ███████░░░░░
  Vision Clarity:       0.79 █████████░░░
  Team Building:        0.45 ████░░░░░░░░
  Customer Obsession:   0.82 ██████████░░
  Adaptability:         0.76 █████████░░░
  Resilience:           0.71 ████████░░░░
  Strategic Thinking:   0.64 ███████░░░░░
  Founder-Market Fit:   0.88 ███████████░

Executive Summary:
"Experienced founder with strong execution track record...
Primary growth opportunity: Build out sales leadership."

AI Analysis Confidence: 0.87
Created: 2025-06-01T10:30:00Z
```

### Find Similar Founders

```bash
mekong genome similar --founder-id genome_001 --limit 10

# Or by traits directly
mekong genome similar --traits '{"execution_speed": 0.9, "risk_tolerance": 0.7}'
```

### Delete Genome

```bash
mekong genome delete --founder-id genome_001

# Confirm:
? Delete genome for founder genome_001? This cannot be undone. (yes/no): yes
✓ Genome deleted (encrypted data removed from database)
```

### Rotate Encryption Key

```bash
mekong genome rotate-key

# Output:
Rotating encryption key...
Loaded 47 genomes
Re-encrypting... [████████████░░] 80%
Key rotated successfully
Old key archived: ~/.mekong/genomes/.aesgcm_key.20250618.backup
```

---

## Database Schema

```sql
CREATE TABLE founder_genomes (
    id SERIAL PRIMARY KEY,
    founder_id VARCHAR(255) UNIQUE NOT NULL,
    encrypted_data BYTEA NOT NULL,
    encryption_key_id VARCHAR(64) NOT NULL,
    genome_hash CHAR(64) NOT NULL,  -- SHA-256
    analysis_summary TEXT,
    confidence_score DECIMAL(3,2),
    trait_scores JSONB,  -- {"risk_tolerance": 0.72, ...}
    cluster_id INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_founder_genomes_founder_id ON founder_genomes(founder_id);
CREATE INDEX idx_founder_genomes_cluster ON founder_genomes(cluster_id);
CREATE INDEX idx_founder_genomes_trait_scores ON founder_genomes USING GIN(trait_scores);
```

---

## Troubleshooting

### Decryption Failed

If genome decryption fails (corrupted or wrong key):

```bash
# Try with backup key (if available)
mekong genome decrypt --use-backup-key --founder-id genome_001

# If unrecoverable, delete and recapture
mekong genome delete --founder-id genome_001
mekong genome init  # Recapture
```

### Missing Trait Scores

If analysis didn't extract all traits:

```bash
# Rerun analysis with full prompt
mekong genome analyze --founder-id genome_001 --type full

# Or quick traits only (cheaper)
mekong genome analyze --founder-id genome_001 --type quick
```

### Similarity Search Returns Nothing

Ensure trait_scores are populated:
```bash
# List genomes with trait scores
python3 -c "
from src.services.genome_service import get_genome_service
svc = get_genome_service()
genomes = svc.get_all_genomes(limit=10)
for g in genomes:
    print(g.founder_id, g.trait_scores.keys())
"
```

---

## Best Practices

1. **Recapture annually** — Founder profiles evolve; update every 12 months
2. **Encrypt always** — Never store raw genome in database
3. **Backup keys** — Keep encrypted backup of `.aesgcm_key` in secure location
4. **Review cluster assignment** — Manual override allowed if AI misclassified
5. **Use similarity for teams** — Complement traits, don't duplicate

---

## Privacy & Security

- **Encryption**: AES-256-GCM (or Fernet)
- **Key Storage**: Local filesystem only (`~/.mekong/genomes/`, mode 600)
- **No Cloud Sync**: Genomes never leave the machine by default
- **Export**: `mekong genome export --format json` creates encrypted backup
- **Import**: `mekong genome import --file backup.json` (requires key)

### Right to Be Forgotten

```bash
mekong genome delete --founder-id <id>
# Permanently removes:
# - Encrypted blob from database
# - Decryption key from local storage (if no other genomes use it)
# - All metadata (created_at, analysis_summary, trait_scores)
```

---

## References

- **Service Implementation**: `src/services/genome_service.py`
- **Model Definition**: `src/models/founder_genome.py`
- **CLI Commands**: `src/cli/genome_command.py`
- **Tests**: `tests/zenos/test_genome_service.py`
- **Migration**: [`docs/zenos-migration-guide.md`](./zenos-migration-guide.md)

---

**Next**: Return to [`docs/zenos-migration-guide.md`](./zenos-migration-guide.md) for migration steps, or explore [`docs/economic-particles.md`](./economic-particles.md) for the financial layer.
