# OFFICIAL DOCUMENTATION RESEARCH — as checked 24 October 2026

Google AI Studio and Gemini capabilities verified against official documentation:

| Capability | Official reference | Design use / limitation |
|---|---|---|
| Interactions API (preferred for new builds) | https://ai.google.dev/gemini-api/docs/interactions-overview | Stateful model/agent tasks and background tasks; `generateContent` legacy but supported; confirm current SDK. |
| Google AI Studio Build mode | https://ai.google.dev/gemini-api/docs/aistudio-build-mode | Can prototype full-stack web apps and download ZIP; secure server-side Gemini key; separate host required if not using AI Studio deployment. |
| AI Studio app deployment | https://ai.google.dev/gemini-api/docs/aistudio-deploying | Cloud Run; eligibility-specific Starter tier up to two services, standard billing plan other cases; don't promise free hosting. |
| AI Studio Agents | https://ai.google.dev/gemini-api/docs/aistudio-agents | Managed agents have Search, URL Context, Code Execution, filesystem in ephemeral sandbox; cost and project limits apply. |
| Document/PDF understanding | https://ai.google.dev/gemini-api/docs/document-processing | Parse PDF including charts/tables up to published page constraints. Input must be authorised. |
| Structured outputs | https://ai.google.dev/gemini-api/docs/structured-output | Typed JSON; schema correct ≠ factual or numeric correct, must validate independently. |
| Files API / deletion | https://ai.google.dev/gemini-api/docs/files | Files API exposes up to 20GB storage per project and 48h auto deletion; explicit `files.delete` needed for 24h target, verify receipts. 20GB is NOT ChatGPT conversation storage. |
| Search grounding | https://ai.google.dev/gemini-api/docs/google-search | Google Search with citation evidence; provider/project billed quotas must be checked. |
| URL Context | https://ai.google.dev/gemini-api/docs/url-context | Fetch publicly accessible web/PDF URLs; not Google Docs/Sheets, login-required/paywalled or localhost content. |
| Tool calling and Code Execution | https://ai.google.dev/gemini-api/docs/tools ; https://ai.google.dev/gemini-api/docs/code-execution | Can ask functions and calculate; never allow AI code to execute real broker orders. |
| Price and free tier rules | https://ai.google.dev/gemini-api/docs/pricing ; https://ai.google.dev/gemini-api/docs/billing | Price, free tier availability and data use depend on model/project; review before processing private or licensed text. |
| Quotas and retry | https://ai.google.dev/gemini-api/docs/rate-limits | RPM, TPM and daily quota per project; 429 means backoff/budget, not silent skipping. |
| Batch API | https://ai.google.dev/gemini-api/docs/batch-api | Reduced listed API cost; 24h SLO unsuitable for guaranteed before-open news; use for overnight nonurgent tasks. |
| Gemini current models | https://ai.google.dev/gemini-api/docs/models | Query stable models accessible to this project, don't hardcode old previews. |
| NSE regular trading hours | https://www.nseindia.com/resources/exchange-communication-holidays | Regular 09:15 to 15:30 IST (exchange trading sessions/holidays). |
| SEBI retail algo regulatory transition | https://www.sebi.gov.in/sebi_data/attachdocs/sep-2025/1759232056254.pdf | Check current SEBI/NSE broker implementation before ever considering real algo execution. |
| ChatGPT Work/Codex purpose and quotas | https://help.openai.com/en/articles/20001275-chatgpt-work-and-codex ; https://help.openai.com/en/articles/20001516-managing-usage-with-gpt-6-astra-in-work-and-codex | Work/Codex usage is limited per user/plan; move recurring runtime into owned scheduler, not repeated Chats. |

**Important technical corrections**
- Merely connecting ChatGPT to a Google account/Drive does NOT grant Gemini API developer access, billing, project quota, nor automatically set up Gemini as an auditing agent.
- ChatGPT Plus covers interactive ChatGPT access, not the costs of hosted Gemini/OpenAI APIs, market licensing or a hosting service.
- Parallel agents are not free hidden ChatGPT workers; use a genuine host/task queue with explicit identities, permissions, quotas and deterministic audit evidence.
- Gmail newsletters can help broker-research intake but only with owner OAuth permission. Telegram plugin was not discovered in this environment: use authorized Telegram API/bot outside ChatGPT, never a pasted session secret.
- Google AI Studio availability/price/terms may change; recheck at deployment and log evaluated API version and model IDs.
