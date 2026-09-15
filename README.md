# 📰 Pratai

An AI-powered weekly newsletter that curates, summarizes, and delivers the most significant AI news, straight to your inbox every Wednesday — fully automated, with an AI Reviewer Agent (not a human) acting as the final quality gate before anything gets sent.

![Python](https://img.shields.io/badge/Python-3.13-blue.svg)
![Vercel](https://img.shields.io/badge/Deployed%20on-Vercel-000000.svg)
![LLM](https://img.shields.io/badge/LLM-Gemini%202.5-purple.svg)
![Email](https://img.shields.io/badge/Email-Resend-1a1a2e.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

---

## 🌐 Schedule

**🚀 Delivered every Wednesday at 12:30 PM IST**, straight to the configured recipient list — no manual work required.

---

## ✨ Features

### 📡 Multi-Source News Aggregation
- Pulls recent AI news from **13 curated RSS feeds**, spanning official AI labs (OpenAI, Anthropic, Google DeepMind), research (arXiv cs.AI, Google Research), and mainstream tech press (The Verge, TechCrunch, Wired, Ars Technica, MIT Technology Review).
- Automatically filters to only the last 7 days of content, so every issue reflects genuinely current news.
- Gracefully skips any feed that's temporarily unavailable, rate-limited, or has no fresh posts that week — never blocks the pipeline.

### 🧠 AI Curator Agent
- Uses Gemini to select at least 7 of the most significant, diverse stories from the raw pool.
- Automatically merges near-duplicate stories covering the same event, rather than listing them separately.
- Writes genuine 4-6 sentence summaries with real depth — background, specifics, and forward-looking implications — not shallow one-liners.
- Enforces single, clean source attribution per story (no "Source A / Source B" mashups).
- Aware of the actual current date, avoiding false "this must be fake/future-dated" hallucinations on genuinely recent news.

### ✅ AI Reviewer Agent (No Human Approval)
- Two-layer quality gate, since there is no manual review step:
  - **Rule-based checks**: minimum story count, required fields, summary length, no leaked API keys/secrets, no leftover placeholder text, single-source enforcement.
  - **LLM critic**: scores the draft 1-10 on editorial quality, topic diversity, relevance, tone, depth, and source cleanliness.
- If the score falls below the configured threshold, the Curator automatically regenerates the draft using the critic's specific feedback, up to a configurable number of retries.
- Configurable fallback policy: send the best-scoring draft anyway after max retries, or skip sending entirely that week if nothing meets the bar.

### 📧 Automated Delivery
- Sends a fully styled HTML email via the Resend API, including a TL;DR section, full story write-ups with clickable headlines, and a CAN-SPAM-compliant footer with the required physical postal address.
- Recipient list is configured directly via environment variables — no database or subscriber management system required.

### ☁️ Serverless Deployment
- Runs as a single Vercel serverless function, triggered weekly by a Vercel Cron Job.
- No persistent server, no database — fully stateless and free to run on Vercel's Hobby tier.

---

## 🛠️ Tech Stack

| Category | Technology |
|----------|------------|
| **Runtime** | Python 3.13, Vercel Serverless Functions |
| **LLM** | Google Gemini (via LangChain) |
| **News Sources** | RSS (feedparser) — 13 curated feeds |
| **Email** | Resend (HTTPS API) |
| **Scheduling** | Vercel Cron Jobs |
| **Deployment** | Vercel |
| **Version Control** | Git, GitHub |

---

## 📸 What a Typical Issue Includes

- 📝 **Intro** — a short, friendly framing paragraph for the week
- ⚡ **TL;DR** — one-line highlights of every story, guaranteed to match the full story list exactly
- 📚 **7+ in-depth stories** — each with a punchy headline, a genuine multi-sentence summary, a single clean source, and a direct link
- 📮 **Compliant footer** — newsletter name and physical address, per CAN-SPAM requirements

---

## 📁 Project Structure

```
PratAI/
│
├── api/
│   └── send_newsletter.py     # Vercel serverless entrypoint (triggered by cron)
│
├── lib/
│   ├── rss_fetcher.py         # Pulls and filters recent items from 13 RSS feeds
│   ├── curator.py             # Gemini agent: selects stories, writes summaries
│   ├── reviewer.py            # Rule-based + LLM critic quality gate, with retry feedback
│   ├── pipeline.py            # Orchestrates fetch -> curate -> review -> retry loop
│   ├── composer.py            # Builds the final styled HTML email
│   └── sender.py               # Sends the email via Resend
│
├── vercel.json                 # Cron schedule configuration
├── requirements.txt            # Python dependencies
├── .env.example                 # Environment variable template
└── README.md                    # Project documentation
```

---

## 🚀 Installation & Setup

### 1. Clone the repository
```bash
git clone https://github.com/surajprakashverma/pratai-newsletter.git
cd pratai-newsletter
```

### 2. Create a virtual environment
```bash
# Windows
python -m venv myvenv
myvenv\Scripts\Activate.ps1

# macOS / Linux
python3 -m venv myvenv
source myvenv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
Copy `.env.example` to `.env` and fill in real values (Gemini API key, Resend API key, recipient list, newsletter name, physical address, quality thresholds).

### 5. Run a local test (sends a real email)
```bash
python api/send_newsletter.py
```

---

## ⚙️ How It Works

1. **Fetch** — `rss_fetcher.py` pulls the last 7 days of entries from 13 AI news sources.
2. **Curate** — `curator.py` asks Gemini to select 7+ diverse, non-redundant stories and write in-depth summaries, aware of the current date to avoid hallucinated "future-dated" flags.
3. **Review** — `reviewer.py` runs rule-based checks, then an LLM critic scores the draft. If it fails the threshold, specific feedback is generated.
4. **Retry** — `pipeline.py` feeds that feedback back into the Curator and tries again, up to `MAX_RETRIES` times.
5. **Resolve** — once the threshold is met (or retries are exhausted), the pipeline either proceeds with the best draft or skips the week entirely, based on `FALLBACK_POLICY`.
6. **Compose & Send** — `composer.py` builds the final HTML email, and `sender.py` delivers it via Resend to every address in `RECIPIENT_EMAILS`.

---

## 🔑 Environment Variables

| Variable | Purpose |
|---|---|
| `GEMINI_API_KEY` | Google Gemini API key for curation and review |
| `GOOGLE_Model` | Gemini model name (e.g. gemini-2.5-flash) |
| `RESEND_API_KEY` | Resend API key for sending the newsletter |
| `RECIPIENT_EMAILS` | Comma-separated list of recipient email addresses |
| `NEWSLETTER_NAME` | Display name of the newsletter (e.g. Pratai) |
| `PHYSICAL_ADDRESS` | Required footer address for CAN-SPAM compliance |
| `SCORE_THRESHOLD` | Minimum LLM critic score (out of 10) required to send |
| `MAX_RETRIES` | Maximum curate-and-review attempts before falling back |
| `FALLBACK_POLICY` | `send_best` (send best draft anyway) or `skip` (send nothing if threshold never met) |

---

## ☁️ Deployment on Vercel

1. Push this repository to GitHub.
2. Go to [vercel.com/new](https://vercel.com/new) and import the repository.
3. Set the Framework Preset to **Other**.
4. Add all environment variables listed above under Project Settings.
5. Deploy. Vercel automatically reads `vercel.json` and registers the weekly cron trigger.
6. Confirm the cron job appears under **Settings → Cron Jobs**, scheduled for `0 7 * * 3` (07:00 UTC = 12:30 PM IST every Wednesday).
7. Optionally, trigger `/api/send_newsletter` manually once after deployment to confirm everything works in the live environment.

### Auto-deploy
Every `git push` to `main` triggers an automatic redeployment on Vercel.

---

## 👥 Who Is This For?

- 🧑‍💻 **Developers and AI enthusiasts** who want a reliable weekly digest without manually tracking a dozen news sources.
- 📚 **Anyone building "learning in public" habits** who wants curated context on the fast-moving AI industry, delivered automatically.
- 🎯 **Builders exploring agentic content pipelines** — this project doubles as a working example of a fully autonomous curate-review-retry-send loop with no human in the loop.

---

## ⚠️ Disclaimer

> This newsletter is generated and reviewed entirely by AI agents, with no human editorial review before sending.
> While the Reviewer Agent enforces quality and factual-sounding checks, occasional inaccuracies are possible — always verify important claims via the linked original sources.
> Commercial email regulations (e.g. CAN-SPAM) apply; ensure your recipient list, sender identity, and footer address remain compliant if you expand distribution.

---

## 👨‍💻 Author

**Suraj Prakash Verma**
- 🏢 UST
- 🌐 GitHub: https://github.com/surajprakashverma

---

## 📄 License

This project is licensed under the **MIT License** — see the LICENSE file for details.

---

## 🌟 Show Your Support

If you found this project useful, give it a ⭐ on GitHub!

Contributions, issues, and feature requests are always welcome. 🙌
