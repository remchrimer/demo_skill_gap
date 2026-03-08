<div align="center">
  <h1>Skill-Bridge</h1>
  <p>
    <b>Career Navigator</b><br>
    AI-powered gap analysis that tells you what to learn next — from new grad to senior, across every career area.
  </p>
</div>

---

**Scenario Chosen:** Skill-Bridge Career Navigator

**Candidate Name:** David Lee

**Demo Video:** [link](https://youtu.be/-ONpRWeU-Hc)

---

## What This Is

A career navigation tool built where you enter your current skills, pick a target role and level, and the system tells you the top 5 skills you should focus on with reasons and real YouTube resources for each one.

The tool covers all 12 career areas from Palo Alto Networks' actual job board: Software Engineering, ML Engineering, Systems Engineering, Cybersecurity Consulting, Product Management, Technical Support, Professional Services, and more. Each role has three levels (Junior, Mid, Senior) with skills derived from real job postings.

I chose to scope this to Palo Alto Networks rather than building a generic career tool because (1) the problem is more concrete when grounded in real roles, (2) the synthetic data is more defensible when it maps to actual job descriptions, and (3) I wanted to build something directly relevant to the company I'm applying to.

---

## Quick Start

### Prerequisites

- Gemini API key (free, no credit card required) 
- YouTube Data API v3 key (free)

---

## How It Works

1. You enter your current skills using an autocomplete input (suggestions come from the role data, but you can type anything)
2. You pick a target role and career level from a filterable list
3. The system runs a gap analysis
4. You get 5 prioritized skills to develop, each with a reason and curated YouTube videos

### The AI Path

The user's skills and the target role's requirements get sent to Google Gemini. The prompt is structured to isolate user input from system instructions. The AI returns 5 skills with explanations of why each one matters for that specific role and level. If relevant, it includes certifications that would strengthen the candidate's profile.

### The Fallback Path

If Gemini is unavailable, returns bad JSON, fails request ID verification, or doesn't match the expected schema — the system falls back to a rule-based analysis. It does a set-difference between the user's skills and the role's required skills (which are ordered by importance in the data), and returns the top 5 gaps with mechanical reasons.

The fallback is less nuanced — it can't detect synonyms ("JS" vs "JavaScript"), can't recognize partial matches ("Docker" vs "Container Orchestration"), and can't reason about learning order. But it always returns a usable result.

### YouTube Integration

For each recommended skill, the system queries the YouTube Data API for relevant videos. The search queries are tailored by level:

- Junior: beginner tutorials and getting-started guides
- Mid: deep dives, real-world examples, and best practices
- Senior: conference talks, engineering leadership discussions, and expert-level content

The system also distinguishes between technical skills and leadership skills — a senior-level "Technical Leadership" skill surfaces talks from CTOs and VPs, not beginner management tutorials. If the YouTube API is unavailable, it falls back to direct YouTube search URLs.

---

## Tradeoffs and Prioritization

- Resume/GitHub parsing — would require a second AI call for extraction, doubling the failure surface. Structured skill input keeps the user as the source of truth and makes the fallback reliable.
- User accounts and persistence — the core flow is stateless. Adding auth and a database would consume time better spent on the AI integration and fallback system.

---

## AI Disclosure

**Did you use an AI assistant?** Yes. I used Claude throughout the project.

**How I used it:** Architecture planning and design decisions, code generation for the backend services and frontend, researching Palo Alto Networks' job postings to build realistic synthetic data, drafting documentation.

**How I verified suggestions:** Every design choice was discussed and challenged before implementation. I pushed back on several of Claude's initial suggestions (structured skill input vs free text, predefined roles vs free text dream roles, adding career levels, Palo Alto-specific scoping). All code was tested locally, and I debugged issues as they came up. The synthetic data was cross-referenced against real job postings from jobs.paloaltonetworks.com.

**Example of a suggestion I rejected:** Claude initially suggested sanitizing user input with regex before it reaches the AI prompt (stripping special characters, limiting length). I rejected this because it doesn't meaningfully prevent prompt injection, the real defense is the three-layer detection and containment system (prompt structure, request ID verification, schema validation). Input sanitization gives false confidence without solving the actual problem.