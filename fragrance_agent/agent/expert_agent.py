"""
Epicure-Fragrance Expert Agent
================================
A world-class fragrance expert agent powered by the fragrance knowledge base.
Combines retrieval-augmented generation with deep domain expertise.

The agent can:
- Recommend note pairings and substitutions
- Suggest formulations based on briefs
- Explain perfume history and cultural traditions
- Advise on IFRA compliance and reformulation
- Navigate the odor-chemistry spectrum (Epicure-style)
- Provide accords and structural guidance
- Identify perfumer signatures and house styles
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import AGENT_NAME, AGENT_TEMPERATURE
from knowledge.knowledge_base import FragranceKnowledgeBase

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are {agent_name}, a world-expert fragrance formulation agent with encyclopedic knowledge of:

## Your Expertise

### 1. Aroma Chemistry & Raw Materials
- Every commercially significant aroma molecule (natural and synthetic): CAS numbers, odor profiles, physicochemical properties, supplier information
- The 15 primary odor families: floral, woody, citrus, spicy, amber, musky, green, fruity, gourmand, aquatic, aromatic_herbal, powdery, leathery, aldehydic, earthy
- Natural extracts (essential oils, absolutes, concretes, CO2 extracts) and their composition
- Synthetic aroma chemicals and their role in modern perfumery
- Volatility classification (top/heart/base notes) and evaporation curves

### 2. Perfume Structure & Formulation
- Classical accord structures: chypre, fougère, oriental/ambery, floral aldehydic, cologne, aquatic, gourmand, leather, oud
- Note pyramid construction (top → heart → base)
- The "Epicure" framework adapted for fragrance:
  - **Cooc model** perspective: "What notes appear together in real perfumes?" (composition-context)
  - **Chem model** perspective: "What shares the same aroma molecules?" (chemistry-context)
  - **Core model** perspective: "What blends both pathways?"
- Note co-occurrence (NPMI) data for evidence-based pairings
- Molecule-to-odor-family typed graph for chemistry-grounded recommendations

### 3. Perfume History (3000 BCE – Present)
- Ancient Egyptian kyphi and temple incense
- Islamic Golden Age distillation breakthroughs
- Eau de Cologne and the citrus revolution (1709)
- Belle Epoque synthetics: coumarin, vanillin, ionones
- Golden Age: Chanel No. 5, Shalimar, Mitsouko
- Power fragrances: Opium, Poison, Cool Water
- Gourmand revolution: Angel (1992)
- Molecular age: Iso E Super, Ambroxan, oud trend

### 4. Master Perfumers & House Styles
- Ernest Beaux (aldehydic florals), Jacques Guerlain (Guerlinade)
- Edmond Roudnitska (hedione, naturalism), Jean-Claude Ellena (minimalism)
- Dominique Ropion (floral overdose), Pierre Bourdon (aquatic pioneer)
- Francis Kurkdjian (precision), Geza Schoen (molecular), Olivier Cresp (gourmand)

### 5. Cultural Fragrance Traditions
- French Haute Parfumerie (Grasse, Paris)
- Middle Eastern attar tradition (oud, rose, saffron)
- Indian gandha (sandalwood, jasmine sambac, mitti attar)
- Japanese kōdō (kyara, listening to incense)
- Chinese xiang (chenxiang, scholar's studio)

### 6. IFRA & Regulatory Compliance
- Current restrictions on oakmoss, lilial, citrus phototoxicity, eugenol, coumarin
- Reformulation strategies for restricted materials
- EU CLP/REACH implications
- Natural vs. synthetic regulatory differences

## How You Answer

1. **Always ground recommendations in data.** When suggesting pairings, cite NPMI co-occurrence strength or molecular overlap. Reference real perfumes as examples.

2. **Distinguish the chemistry-context vs. composition-context perspective.** A substitution can be "what else appears with this note in real perfumes" (Cooc) or "what shares its molecular profile" (Chem). Both are valid; say which you're using.

3. **Provide structural guidance.** Don't just list notes — explain the accord architecture. Where does each note sit in the pyramid? What's its functional role (sparkle, body, fixative)?

4. **Flag regulatory issues.** If a suggestion involves restricted materials (oakmoss, lilial, bergamot non-FCF), note the IFRA restriction and suggest compliant alternatives.

5. **Respect tradition while innovating.** Know the rules (classical accords, cultural protocols) before breaking them. Explain *why* a classical structure works before proposing modifications.

6. **Be specific about raw materials.** Don't say "citrus" — say "bergamot FCF (FCF required for phototoxicity compliance) at 15-20% of the top note accord." Don't say "musk" — say "galaxolide (clean, laundry-musk) or habanolide (warm, skin-musk) depending on the desired warmth."

7. **Cite your sources.** Reference perfumes, perfumers, or historical precedent when making claims. "This rose-jasmine-sandalwood structure echoes the heart of Shalimar (1925, Jacques Guerlain)."

## Response Format

Structure your responses as:
1. **Direct answer** to the question
2. **Structural analysis** (accord architecture, note pyramid placement)
3. **Evidence** (co-occurrence data, molecular overlap, reference perfumes)
4. **Practical notes** (IFRA compliance, sourcing, alternatives)
5. **Cultural/historical context** when relevant
"""


class FragranceExpertAgent:
    """The Epicure-Fragrance expert agent."""

    def __init__(self, knowledge_base: FragranceKnowledgeBase = None):
        self.kb = knowledge_base or FragranceKnowledgeBase()
        self.kb.load()
        self.system_prompt = SYSTEM_PROMPT.format(agent_name=AGENT_NAME)
        self.conversation_history = []

    def get_system_prompt(self) -> str:
        """Return the system prompt with any dynamic context."""
        return self.system_prompt

    def get_retrieval_context(self, query: str, max_tokens: int = 4000) -> str:
        """
        Retrieve relevant context from the knowledge base for a given query.
        This is the RAG component — inject relevant data before the LLM call.
        """
        context = self.kb.get_context_for_agent(query, max_tokens=max_tokens)
        if context:
            return f"\n\n## Retrieved Knowledge Base Context\n\n{context}"
        return ""

    def build_prompt(self, user_query: str) -> str:
        """
        Build the full prompt for the LLM, combining:
        1. System prompt (expert identity + domain knowledge)
        2. Retrieved context (RAG from knowledge base)
        3. Conversation history
        4. Current user query
        """
        # Retrieve relevant context
        retrieval_context = self.get_retrieval_context(user_query)

        # Build conversation context
        history_str = ""
        for turn in self.conversation_history[-6:]:  # Keep last 6 turns
            role = turn["role"]
            content = turn["content"]
            if role == "user":
                history_str += f"\nUser: {content}"
            else:
                history_str += f"\n{AGENT_NAME}: {content}"

        prompt = (
            f"{self.system_prompt}\n\n"
            f"{retrieval_context}\n\n"
            f"## Conversation\n{history_str}\n\n"
            f"User: {user_query}\n\n"
            f"{AGENT_NAME}:"
        )

        return prompt

    def query(self, user_query: str) -> Dict:
        """
        Process a user query through the full pipeline:
        1. Retrieve context from knowledge base
        2. Build augmented prompt
        3. Return the prompt and context (actual LLM call is external)

        Returns a dict with:
        - prompt: the full augmented prompt ready for an LLM
        - context: the retrieved knowledge base context
        - raw_results: the raw search results from the KB
        """
        # Search the knowledge base
        raw_results = self.kb.search(user_query)

        # Get formatted context
        context = self.get_retrieval_context(user_query)

        # Build the full prompt
        prompt = self.build_prompt(user_query)

        # Update conversation history
        self.conversation_history.append({"role": "user", "content": user_query})

        return {
            "prompt": prompt,
            "context": context,
            "raw_results": raw_results,
            "system_prompt": self.system_prompt,
        }

    def format_response(self, user_query: str, llm_response: str) -> str:
        """
        Format an LLM response and add it to conversation history.
        This method is called after receiving the LLM's output.
        """
        self.conversation_history.append({"role": "assistant", "content": llm_response})
        return llm_response

    def reset_conversation(self):
        """Reset the conversation history."""
        self.conversation_history = []

    def get_capabilities_summary(self) -> str:
        """Return a summary of what the agent can do."""
        return f"""
{AGENT_NAME} — World-Expert Fragrance Formulation Agent
========================================================

I can help you with:

1. **Note Pairings & Substitutions**
   - "What pairs well with oud?"
   - "Suggest a replacement for oakmoss in a chypre accord"
   - "What notes co-occur with bergamot in real perfumes?"

2. **Formulation Guidance**
   - "Build me a classical chypre accord"
   - "Create a fresh aquatic masculine formulation"
   - "Design a rose-oud oriental for the Middle Eastern market"

3. **Perfume History & Culture**
   - "What was revolutionary about Chanel No. 5?"
   - "Explain the Japanese kōdō tradition"
   - "How did Angel create the gourmand family?"

4. **Raw Material Expertise**
   - "Compare Indian sandalwood vs Australian sandalwood"
   - "What's the difference between Iso E Super and Ambroxan?"
   - "Explain hedione's role in modern perfumery"

5. **Regulatory & Safety**
   - "What are the current IFRA restrictions on oakmoss?"
   - "Is lilial still usable in EU fragrances?"
   - "How do I reformulate a fougère without coumarin?"

6. **Perfumer Profiles**
   - "What is Jean-Claude Ellena's signature approach?"
   - "Who created Cool Water and how?"
   - "What defines the Guerlinade?"

7. **Chemistry-Context Navigation (Epicure-style)**
   - "From a chemistry perspective, what molecules overlap with rose?"
   - "From a co-occurrence perspective, what appears with rose in real perfumes?"
   - "How does the Chem model vs Cooc model differ for jasmine pairings?"

Knowledge base stats:
- {len(self.kb.molecules)} aroma molecules
- {len(self.kb.notes)} fragrance notes
- {len(self.kb.perfumes)} reference perfumes
- {len(self.kb.cooccurrence_graph.get('edges', []))} note co-occurrence edges
- 8 historical periods covered
- 10 classical accord templates
- 10 master perfumer profiles
- 5 cultural traditions documented
"""
