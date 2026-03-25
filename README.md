# 🤖 AI Data Analyst

A local, AI-powered application that lets you query your database using plain English. No cloud API required — everything runs on your machine using **Ollama** and **local LLMs**.

---

## 📌 Table of Contents

- [Overview]
- [Features]
- [Tech Stack]
- [Project Structure]
- [Database Schema]
- [How It Works]
- [Setup & Installation]
- [Running the App]
- [Example Queries]
- [Known Limitations]
- [Future Improvements]

---

## 🧠 Overview

**AI Data Analyst** is a Text-to-SQL application that bridges the gap between non-technical users and databases. You type a question like *"Which product has the lowest price?"* and the app:

1. Converts your question into a SQL query using a local LLM
2. Runs that query against a SQLite database
3. Returns the result as a clean, human-readable sentence

All processing happens **100% locally** — no data is sent to any external API.

---

## ✨ Features

- 💬 **Natural Language Querying** — Ask questions in plain English
- 🔄 **Text-to-SQL Generation** — Automatically converts questions to valid SQLite queries
- 🛡️ **SQL Error Self-Healing** — Automatically retries and fixes broken queries (up to 2 attempts)
- 📊 **Human-Readable Answers** — Results are interpreted into clear sentences, not raw tuples
- 🔍 **Raw Results Expander** — Optionally view the underlying database output
- 🔒 **100% Local & Private** — Powered by Ollama; your data never leaves your machine
- ⚡ **Fast Inference** — Uses lightweight models optimized for code/SQL tasks

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | [Streamlit](https://streamlit.io/) |
| **LLM Backend** | [Ollama](https://ollama.com/) (local inference) |
| **LLM Model** | `qwen2.5-coder:1.5b` (recommended) |
| **LLM Framework** | [LangChain](https://www.langchain.com/) (`langchain-ollama`) |
| **Database** | SQLite (`amazon.db`) |
| **DB Connector** | SQLAlchemy + sqlite3 |
| **Language** | Python 3.10+ |

---

## 📁 Project Structure

```
Data_Analyst/
│
├── amazon.db               # SQLite database with sample e-commerce data
├── create_database.py      # Script to create and populate the database
├── main.py                 # Core logic: schema extraction, Text-to-SQL, result interpretation
├── frontend.py             # Streamlit UI
├── pyproject.toml          # Project dependencies
├── README.md               # This file
└── .venv/                  # Virtual environment (not committed)
```

---

## 🗃️ Database Schema

The app ships with a sample **Amazon-like e-commerce database** containing 4 tables:

### `customers`
| Column | Type | Description |
|---|---|---|
| customer_id | INTEGER (PK) | Unique customer ID |
| name | TEXT | Customer full name |
| email | TEXT | Email address |
| city | TEXT | City of residence |
| join_date | TEXT | Account creation date |

### `products`
| Column | Type | Description |
|---|---|---|
| product_id | INTEGER (PK) | Unique product ID |
| name | TEXT | Product name |
| category | TEXT | Category (e.g. Electronics, Stationery) |
| price | REAL | Price in USD |

### `orders`
| Column | Type | Description |
|---|---|---|
| order_id | INTEGER (PK) | Unique order ID |
| customer_id | INTEGER (FK) | References `customers` |
| order_date | TEXT | Date order was placed (YYYY-MM-DD) |
| total_amount | REAL | Total order value in USD |

### `order_items`
| Column | Type | Description |
|---|---|---|
| order_item_id | INTEGER (PK) | Unique item ID |
| order_id | INTEGER (FK) | References `orders` |
| product_id | INTEGER (FK) | References `products` |
| quantity | INTEGER | Number of units purchased |
| subtotal | REAL | Line item total |


---

## ⚙️ How It Works

```
User Question
      │
      ▼
┌─────────────────────┐
│  Schema Extractor   │  ← Reads table names, columns & 2 sample rows
└─────────────────────┘
      │
      ▼
┌─────────────────────┐
│   Text-to-SQL LLM   │  ← llama3.2:1b via Ollama + LangChain
│  (with strict rules)│  ← No aliases, LOWER() comparisons, ORDER BY for min/max
└─────────────────────┘
      │
      ▼
┌─────────────────────┐
│  SQL Execution      │  ← Runs against amazon.db via sqlite3
│  + Retry on Error   │  ← Auto-fixes broken SQL up to 2 times
└─────────────────────┘
      │
      ▼
┌─────────────────────┐
│  Result Interpreter │  ← Second LLM call: converts tuples → readable sentence
└─────────────────────┘
      │
      ▼
  Clean Answer displayed in Streamlit UI
```

### Key Design Decisions

- **Sample rows in schema prompt** — The LLM sees real data values, preventing case-mismatch errors (e.g., `'Electronics'` vs `'electronics'`)
- **Explicit SQL anti-patterns in prompt** — The system prompt shows the model WRONG vs CORRECT query patterns for common edge cases
- **Self-healing retry loop** — If SQLite throws an error, the broken query + error message is fed back to the LLM for correction
- **Two-stage LLM pipeline** — Stage 1 generates SQL; Stage 2 interprets results. This separation keeps each prompt focused and accurate

---

## 🚀 Setup & Installation

### Prerequisites

- Python 3.10 or higher
- [Ollama](https://ollama.com/download) installed and running
- The `llama3.2:1b` model pulled

### Step 1 — Clone the Repository

```bash
git clone https://github.com/Hiteshi3121/AI_Data_Analyst.git
cd AI_Data_Analyst
```

### Step 2 — Create a Virtual Environment

```bash
python -m venv .venv

# Activate on Windows
.venv\Scripts\activate

# Activate on Mac/Linux
source .venv/bin/activate
```

### Step 3 — Install Dependencies

```bash
pip install streamlit langchain langchain-ollama langchain-core sqlalchemy
```

### Step 4 — Pull the LLM Model via Ollama

```bash
ollama pull llama3.2:1b
```

> 💡 Make sure Ollama is running in the background before starting the app. You can verify with `ollama list`.

### Step 5 — Create the Database

```bash
python create_database.py
```

You should see:
```
✅ Database 'amazon.db' created with dummy data!
```

---

## ▶️ Running the App

```bash
streamlit run frontend.py
```

The app will open in your browser at `http://localhost:8501`.

---

## 💡 Example Queries

Try these questions in the app:

| Question | Expected Answer |
|---|---|
| How many customers are there? | There are 4 customers |
| Which product has the lowest price? | Notebook at $3.50 |
| On which date was the highest order placed? | 2024-05-05 with $83.47 |
| How many electronic products are there? | There are 2 electronic products |
| Which city Charlie Lee is from? | Chicago |
| Show all products in the Accessories category | Laptop Sleeve |
| What is the total revenue from all orders? | $168.95 |

---

## ⚠️ Known Limitations

- **Small model accuracy** — `qwen2.5-coder:1.5b` is fast but may occasionally misinterpret very complex or ambiguous questions. Use a larger model like `mistral:7b` for higher accuracy.
- **No conversation memory** — Each query is independent; the app doesn't remember previous questions.
- **SQLite only** — Currently hardcoded to work with SQLite. PostgreSQL/MySQL support would require additional configuration.
- **English only** — The LLM prompts and system instructions are in English.

---

## 🔮 Future Improvements

- [ ] **Chat history** — Remember previous questions within a session
- [ ] **Upload your own database** — Let users connect any SQLite `.db` file via the UI
- [ ] **Show the generated SQL** — Display the SQL query alongside the result for transparency
- [ ] **Multi-database support** — Add PostgreSQL and MySQL connectors
- [ ] **Data visualization** — Auto-generate charts for numerical results using Plotly
- [ ] **Model selector** — Let users pick their preferred Ollama model from the UI
- [ ] **Export results** — Download query results as CSV

---

## 🙌 Acknowledgements

- [Ollama](https://ollama.com/) for making local LLM inference easy
- [LangChain](https://www.langchain.com/) for the LLM orchestration framework
- [Streamlit](https://streamlit.io/) for the rapid UI development
- [Qwen](https://huggingface.co/Qwen) team for the `llama3.2:1b` model