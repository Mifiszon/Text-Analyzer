# 📊 Text Analyzer — NLP-Based Document Scoring & Classification

A Python web application that performs **natural language processing, semantic role analysis, and frequency statistics** on Polish-language texts. Built as a university project analyzing press coverage of the 1994 San Marino Grand Prix (Ayrton Senna).

---

## 🔍 What It Does

The app ingests a corpus of text documents and answers the question: *how thematically relevant is each document to a given topic?* — using a custom scoring engine rather than a black-box ML model, making every decision fully explainable.

### Core analytical features

| Feature | Description |
|---|---|
| **Semantic role detection** | Identifies 6 roles in text: agent, event, object, tool, location, goal |
| **Weighted scoring** | Each detected role contributes a configurable weight to a relevance score (0–1) |
| **Synergy bonuses** | Co-occurrence of role pairs (e.g. agent + location) adds additional score |
| **Document ranking** | All documents sorted by relevance score descending |
| **Frequency analysis** | Top-30 lemmatized word frequencies, split by document category |
| **Text highlighting** | Visual markup of detected keywords by semantic role |

---

## 🧠 Scoring Algorithm

The relevance score is computed in three steps:

**1. Lemmatization** — each word is reduced to its base form using the `clp3` Polish morphological analyzer, ensuring "Senny", "Sennie", "Sennę" all map to "Senna".

**2. Role matching** — base forms are matched against a configurable keyword dictionary split into 6 semantic roles:

```
roles = {
    "agent":    ["senna", "ayrton", "ratzenberger", ...],
    "event":    ["wypadek", "wyścig", "śmierć", ...],
    "location": ["imola", "san marino", "tamburello"],
    "object":   ["samochód", "bolid", "williams", ...],
    "tool":     ["formuła", "prędkość", "km/h", ...],
    "goal":     ["bezpieczeństwo", "życie", "zwycięstwo", ...]
}
```

**3. Score calculation:**

```
score = Σ weight[role]  +  Σ synergy[role_pair]
```

Example weights: `agent=0.20`, `location=0.15`, `event=0.12` — tunable via config.  
Example synergy: `(agent, location) = +0.25`, `(agent, event) = +0.15`.

Final score is capped at 1.0 and used to classify documents as *thematic* or *other*.

---

## 📈 Analysis Views

- **`/teksty`** — ranked document list with scores, detected roles, and highlighted keywords
- **`/frekwencja`** — side-by-side word frequency tables: thematic corpus vs. rest
- **`/wagi`** — weight and synergy table (full scoring transparency)
- **`/formularz`** — keyword dictionary browser by role

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3, Flask |
| NLP | clp3 (Polish morphological analyzer) |
| Text processing | `re` (regex), custom lemmatization pipeline |
| Frontend | HTML, Jinja2 templates, CSS |
| Data | Plain `.txt` corpus, organized by category |

---

## 🚀 Running Locally

```bash
git clone https://github.com/Mifiszon/Text-Analyzer.git
cd Text-Analyzer
pip install -r requirements.txt
python app.py
```

App runs at `http://localhost:12226`

---

## 💡 Key Takeaways & Potential Extensions

This project demonstrates core data analysis concepts applied to text:
- designing an **interpretable scoring model** with configurable weights
- **corpus segmentation** and comparative frequency analysis
- **pipeline thinking**: raw text → normalization → feature extraction → scoring → ranking

Possible extensions:
- Replace keyword matching with **TF-IDF or word embeddings** for broader coverage
- Add **pandas + matplotlib** export for score distribution visualization
- Expand corpus and evaluate scoring accuracy against human-labeled data
- Port keyword config to a **database or JSON** for runtime editing without code changes

---

## 👨‍💻 Author

**Michał Ogiba** — [linkedin.com/in/michalogiba](https://linkedin.com/in/michalogiba) · [github.com/Mifiszon](https://github.com/Mifiszon)

*University project, Jagiellonian University — Digital Information Processing, 2024*
