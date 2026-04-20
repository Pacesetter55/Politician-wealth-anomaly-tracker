# Know Your Politician 🗳️

A Streamlit web app that lets Indian citizens research Lok Sabha candidates — tracking wealth, criminal cases, and suspicious patterns across elections from 1999 to 2024.

Data is sourced from official Election Commission affidavits via [myneta.info](https://myneta.info). AI summaries and chat are powered by Groq's `llama-3.1-8b-instant` model.

---

## Features

- **Wealth Tracking** — View how a politician's declared assets and liabilities changed across every Lok Sabha election they contested.
- **Criminal Records** — See criminal cases declared in official affidavits (declared ≠ convicted).
- **Discrepancy Flags** — Algorithmic detection of suspicious wealth spikes, zero-liability anomalies, and high case counts.
- **AI Summary** — One-click AI-generated voter briefing covering wealth trajectory, criminal history, and red flags.
- **AI Chat** — Ask plain-language questions about any politician, grounded in their affidavit data.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend / UI | Streamlit |
| Scraping | requests + BeautifulSoup (lxml) |
| Data | myneta.info (Election Commission affidavits) |
| Charts | Plotly |
| AI / LLM | Groq API — `llama-3.1-8b-instant` |
| Data wrangling | pandas |

---

## Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/your-username/Know_your_politician.git
cd Know_your_politician
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up environment variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
```

Get a free API key at [console.groq.com](https://console.groq.com).

### 4. Run the app

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`.

---

## Usage

1. Type a politician's name or constituency in the sidebar (e.g. *Narendra Modi*, *Rahul Gandhi*, *Varanasi*).
2. Select a candidate from the search results.
3. Explore the dashboard tabs:
   - **Overview** — Election history table + AI summary
   - **Wealth Analysis** — Asset/liability growth charts
   - **Criminal Cases** — Year-wise case breakdown
   - **Discrepancies** — Algorithmic red flags
   - **AI Chat** — Ask questions in natural language

---

## Project Structure

```
├── app.py            # Streamlit UI and page logic
├── scraper.py        # myneta.info scraper (search + profile + compare pages)
├── analyzer.py       # Charts, discrepancy detection, summary stats
├── llm_chat.py       # Groq LLM integration (chat + quick summary)
├── requirements.txt
└── .env              # GROQ_API_KEY (not committed)
```

---

## Data Coverage

- **Elections:** Lok Sabha 1999, 2004, 2009, 2014, 2019, 2024
- **Data points per election:** Total assets, total liabilities, criminal cases declared, party, constituency, education, age
- **Source:** Candidate affidavits published on [myneta.info](https://myneta.info) (sourced from the Election Commission of India)

---

## Disclaimer

This tool is built for civic transparency and voter education. All data is sourced from publicly available official election affidavits. Criminal cases shown are *declared* by candidates — declaration does not imply guilt. Always cross-verify with official Election Commission of India records.

---

## License

MIT
