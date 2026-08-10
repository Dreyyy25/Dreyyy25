<div align="center">
  <img src="https://raw.githubusercontent.com/Dreyyy25/Dreyyy25/output/profile.svg"
       width="100%"
       alt="andrey.py open in a code editor — Andrey Jay Almosara, backend engineer, Metro Manila. Builds multi-tenant SaaS backends for legal, healthcare and fintech: 20+ table multi-tenant schemas, HIPAA auth stacks, async job pipelines. Python, FastAPI, Django, PostgreSQL.">
</div>

<p align="center">
  <a href="mailto:almosaraaj25@gmail.com">almosaraaj25@gmail.com</a>
  &nbsp;·&nbsp;
  <a href="https://linkedin.com/in/adyalmsr25">linkedin.com/in/adyalmsr25</a>
</p>

<br>

<div align="center">
  <img src="https://raw.githubusercontent.com/Dreyyy25/Dreyyy25/output/stack.svg"
       width="100%"
       alt="Toolchain, grouped: languages — Python, TypeScript, JavaScript, Java; backend — FastAPI, Django, Node.js; data and auth — PostgreSQL, MySQL, Supabase, Firebase, JSON Web Tokens; AI — LangChain, Pydantic, Google Gemini, TensorFlow, Claude, OpenAI; infra and web — Docker, Git, GitHub Actions, AWS, React, Next.js.">
</div>

<br>

<details>
<summary><b>Selected work</b> — click to expand</summary>
<br>

**Estate Vault** · legal-tech SaaS · FastAPI, Supabase, PostgreSQL
Multi-tenant isolation and role-based access control across 20+ normalized tables.
Integrated LangGraph agents (Google Gemini) for automated legal clause assembly, and
refactored their internals for performance and maintainability. Built Stripe Connect
billing with a 6-level firm hierarchy, commission splits and automated payouts.

**Meta Health** · HIPAA-compliant healthcare platform · Django REST Framework
Designed the initial backend: custom `UserAccount` model with UUID primary keys and
email-based auth, role-based access control across four roles, and a PostgreSQL schema
spanning 8 domain apps. OAuth2 + JWT foundation with PKCE for mobile clients and Argon2
password hashing.

**AI legal document platform** · FastAPI, Supabase
Eliminated API timeouts on long-running AI tasks with an asynchronous job-polling
pattern (pending → processing → completed), bringing perceived response time under
200 ms. JWT multi-tenant isolation with zero cross-tenant leakage across 3+ law firms.

**Automa8e** · corporate reporting · Django REST, Pydantic AI
Automated extraction of annual reports into structured XBRL, backed by a normalized
PostgreSQL schema with end-to-end validation.

**Job Board API** · personal project · Django 5.2, DRF
Custom JWT auth, Argon2 hashing, UUID domain models. Four LangChain/LangGraph features
including a ReAct-style assistant with read-only tool-calling, prompt-injection
defenses and per-thread cost controls. Custom QuerySets to eliminate N+1 queries, plus
layered API throttling.

</details>

<br>

<div align="center">
  <a href="https://github.com/Dreyyy25?tab=overview" title="Contribution graph">
    <img src="https://raw.githubusercontent.com/Dreyyy25/Dreyyy25/output/contributions.svg"
         width="100%"
         alt="Contribution grid for the last year, with a wave travelling across it crushing each column flat in turn">
  </a>
</div>
