"""
AETHER Core Prompts
The 6 battle-tested first-principles templates.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel

class Prompt(BaseModel):
    id: str
    title: str
    category: str  # "core" | "discovery" | "audit" | "longterm" | "connection" | "meta"
    description: str
    template: str
    placeholder_hint: str = "Enter your topic, claim, or question"
    is_core: bool = True

# The canonical 6 prompts from the AETHER 48-hour project
CORE_PROMPTS: List[Prompt] = [
    Prompt(
        id="first-principles-deconstructor",
        title="First Principles Deconstructor",
        category="core",
        description="Break down any belief, system, or problem to its fundamentals.",
        placeholder_hint="e.g. Why is AI alignment so hard?",
        template="""You are a first-principles reasoning engine. For the following topic or belief: {input}.

1. List the absolute fundamental truths that cannot be broken (physical laws, mathematical constants, human nature, etc.).
2. Identify every hidden assumption people usually make.
3. Reconstruct the concept from those fundamentals only.
4. What new insights or solutions emerge that conventional thinking misses?

Be ruthless with truth. Avoid hedging. Respond in Grok's voice — curious, direct, and maximally helpful.""",
    ),
    Prompt(
        id="cosmic-hypothesis-generator",
        title="Cosmic Hypothesis Generator",
        category="discovery",
        description="Generate bold, testable ideas about unsolved mysteries.",
        placeholder_hint="e.g. What is the origin of life?",
        template="""Act as a theoretical physicist + philosopher hybrid at xAI. Generate 3 novel, falsifiable hypotheses for: {input}.

For each:
• One-sentence statement
• Underlying first principles
• Specific experiment/observation that could support or falsify it in <10 years
• Elegance + explanatory power score (1-10)

Prioritize ideas that bridge currently disconnected fields (physics + consciousness, biology + computation, etc.).""",
    ),
    Prompt(
        id="truth-audit-engine",
        title="Truth Audit Engine",
        category="audit",
        description="Maximum truth-seeking audit on any claim, news, paper or viral post.",
        placeholder_hint="Paste the claim e.g. AI will replace 80% of jobs by 2030",
        template="""Perform a maximum truth-seeking audit on: {input}.

Use this exact structure:
1. Core Claim (verbatim, one sentence)
2. Evidence Quality Score (0-100) + justification with sources
3. Primary biases / incentives of the source
4. Strongest alternative explanations consistent with data
5. What specific new evidence would move the score >20 points?
6. Final Truth Score (0-100) with 95% confidence interval

No sycophancy. No hedging. Be Grok.""",
    ),
    Prompt(
        id="civilizational-consequence-mapper",
        title="Civilizational Consequence Mapper",
        category="longterm",
        description="Map 2nd, 3rd and 4th order effects of technologies or policies over 50-100 years.",
        placeholder_hint="e.g. CRISPR gene editing or universal basic income",
        template="""Map the 2nd-, 3rd-, and 4th-order effects of {input} on humanity over 50–100 years across:
- Cognition & identity
- Power & coordination
- Meaning & mental health
- Existential risk vs flourishing

End with exactly 3 concrete, actionable recommendations for positive steering.""",
    ),
    Prompt(
        id="interdisciplinary-synthesizer",
        title="Interdisciplinary Synthesizer",
        category="connection",
        description="Find hidden bridges and structural connections between fields.",
        placeholder_hint="e.g. Field A: attention mechanisms in transformers | Field B: natural selection",
        template="""You are a master of deep domain analogy. Connect {input} at the structural level.

1. Deepest non-obvious similarities
2. Concepts from one that would revolutionize the other
3. One specific new research program or invention this connection makes obvious

Be precise and surprising.""",
    ),
    Prompt(
        id="question-quality-amplifier",
        title="Question Quality Amplifier",
        category="meta",
        description="Turn weak questions into profound cosmic-scale ones and answer the deepest version.",
        placeholder_hint="e.g. How can we make AI safe?",
        template="""Take this question: "{input}"

Rewrite it at three increasing levels of depth:
• V1: Clear + specific
• V2: Adds critical context + constraints
• V3: First-principles cosmic-scale version

Then give a maximum-depth answer to V3.""",
    ),
]

def get_core_prompts() -> List[Prompt]:
    return CORE_PROMPTS

def get_prompt_by_id(prompt_id: str) -> Optional[Prompt]:
    for p in CORE_PROMPTS:
        if p.id == prompt_id:
            return p
    return None

def fill_template(template: str, user_input: str) -> str:
    """Replace {input} without str.format (user text may contain braces)."""
    text = template or ""
    if "{input}" in text:
        return text.replace("{input}", user_input)
    # Fallbacks for legacy [PASTE ...] style if someone pastes raw
    legacy = text.replace("[PASTE TOPIC HERE]", user_input)
    legacy = legacy.replace("[PASTE CLAIM]", user_input)
    legacy = legacy.replace("[TOPIC]", user_input)
    legacy = legacy.replace("[YOUR QUESTION]", user_input)
    legacy = legacy.replace("[PASTE OPEN QUESTION]", user_input)
    legacy = legacy.replace("[PASTE ...]", user_input)
    return legacy

def get_all_core_prompt_dicts() -> List[Dict]:
    """For API responses."""
    return [p.model_dump() for p in CORE_PROMPTS]