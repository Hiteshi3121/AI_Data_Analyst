from sqlalchemy import create_engine, inspect
import json
import re
import sqlite3
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaLLM

db_url = "sqlite:///amazon.db"

def extract_schema(db_url):
    engine = create_engine(db_url)
    inspector = inspect(engine)
    conn = sqlite3.connect("amazon.db")
    cursor = conn.cursor()
    schema = {}

    for table_name in inspector.get_table_names():
        columns = inspector.get_columns(table_name)
        col_names = [col['name'] for col in columns]
        try:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 2")
            sample_rows = cursor.fetchall()
        except:
            sample_rows = []
        schema[table_name] = {
            "columns": col_names,
            "sample_rows": sample_rows
        }

    conn.close()
    return json.dumps(schema)


def text_to_sql(schema, prompt):
    SYSTEM_PROMPT = """
You are an expert SQLite SQL generator. Given a schema and a user question, output ONLY a valid SQLite SQL query.

STRICT RULES:
1. Output ONLY raw SQL. No markdown, no backticks, no explanation, no preamble.
2. Do NOT use table aliases (no "AS p", no "p.name"). Always use full table.column names.
3. For string comparisons, always use: LOWER(column) = LOWER('value')
4. CRITICAL - For "which X has highest/lowest Y" questions:
   - WRONG: SELECT name FROM products WHERE price = MIN(price)
   - CORRECT: SELECT name, price FROM products ORDER BY price ASC LIMIT 1
5. CRITICAL - For "on which date was the highest/lowest amount" questions:
   - WRONG: SELECT MAX(total_amount) FROM orders
   - CORRECT: SELECT order_date, total_amount FROM orders ORDER BY total_amount DESC LIMIT 1
6. ALWAYS select all columns relevant to the question (e.g. if asked for date, SELECT the date column).
7. For aggregation with MIN/MAX in WHERE clause, always use a subquery:
   - WRONG: SELECT name WHERE price = MIN(price)
   - CORRECT: SELECT name, price FROM products WHERE price = (SELECT MIN(price) FROM products)
"""

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("user", "Schema:\n{schema}\n\nQuestion: {user_prompt}\n\nSQL Query:")
    ])

    model = OllamaLLM(model="llama3.2:1b", temperature=0)
    chain = prompt_template | model

    raw_response = chain.invoke({"schema": schema, "user_prompt": prompt})
    cleaned = re.sub(r"<think>.*?</think>", "", raw_response, flags=re.DOTALL)
    cleaned = re.sub(r"```[\w]*", "", cleaned)
    cleaned = cleaned.replace("```", "")
    return cleaned.strip()


def run_sql_with_retry(sql_query, prompt, schema, max_retries=2):
    """If SQL fails, ask model to fix it."""
    conn = sqlite3.connect("amazon.db")
    cursor = conn.cursor()

    for attempt in range(max_retries + 1):
        try:
            res = cursor.execute(sql_query)
            results = res.fetchall()
            conn.close()
            return results, sql_query
        except Exception as e:
            if attempt < max_retries:
                # Ask model to fix the broken SQL
                fix_prompt = f"""
The following SQL query failed with error: {str(e)}

Broken SQL: {sql_query}

Schema: {schema}
Original Question: {prompt}

Fix the SQL query. Output ONLY the corrected SQL, nothing else.
"""
                model = OllamaLLM(model="llama3.2:1b", temperature=0)
                sql_query = model.invoke(fix_prompt).strip()
                sql_query = re.sub(r"```[\w]*", "", sql_query).replace("```", "").strip()
            else:
                conn.close()
                raise e


def interpret_results(user_prompt, sql_results, sql_query):
    if not sql_results:
        return "No results found in the database for your query."

    SYSTEM_PROMPT = """
You are a helpful data analyst. Given a user's question, the SQL used, and the raw results,
write a clear 1-2 sentence natural language answer.
State the actual values from the results directly. Do not be vague.
Example: "The highest order was placed on 2024-05-05 with a total of $83.47."
"""

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("user", "Question: {question}\nSQL Used: {sql}\nRaw Results: {results}\n\nAnswer:")
    ])

    model = OllamaLLM(model="llama3.2:1b", temperature=0)
    chain = prompt_template | model
    return chain.invoke({
        "question": user_prompt,
        "sql": sql_query,
        "results": str(sql_results)
    })


def get_data_from_database(prompt):
    schema = extract_schema(db_url)
    sql_query = text_to_sql(schema, prompt)
    results, final_sql = run_sql_with_retry(sql_query, prompt, schema)
    natural_answer = interpret_results(prompt, results, final_sql)
    return natural_answer, results