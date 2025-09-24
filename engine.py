import google.generativeai as genai
import os
import pandas as pd
from pandasql import sqldf
import matplotlib.pyplot as plt
import io
import base64
import json

DEBUG = False  # Set to True to enable debug output

def debug_print(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)

with open('settings.json', 'r') as f:
    settings = json.load(f)
api_key = settings.get('genai_api_key')

genai.configure(api_key=api_key)

def geminiAI(query):
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(query)
    return response.text.strip()

def nl_to_sql_translator(natural_language_query, table_schema, sample_data):
    prompt = f"""
    Table schema:
    {table_schema}

    Sample Data:
    {sample_data}

    Convert the following natural language query to a standard SQL query. Only show columns that are needed for the answer.
    Only return the SQL code. Do not include any extra text, explanations, or markdown code blocks
    and table name is df.
    Natural Language Query: '{natural_language_query}'
    """
    sql_query = geminiAI(prompt)
    return sql_query

def how_to_present(query, user_query):
    prompt = f"""
    How should I present the result from this sql query to a business audience?
    Should it be a matplotlib graph? If so, what type of graph? Or should it be a table? Just answer with the word table or the type of graph. No explanations.
    The question was: {user_query}
    Here is the sql query:
    {query}
    """
    sql_query = geminiAI(prompt)
    return sql_query

def nl_to_matplot_translator(query, typen):
    if typen.lower() == "table":
        prompt = f"""
        Can you generate a python function that returns the html code to make a table that shows this? The result from the sql query are stored in result_df
        return the html code as a string variable named html_table, function named generate_html_table
        Only return the code. Do not include any extra text, explanations, or markdown code blocks
        {query}
        """
    else:
        prompt = f"""
        Can you generate a python function that returns the matplot code to make a {typen} that shows this? The result from the sql query are stored in result_df
        No imports in the code. Just the code to make the {typen}. Use matplotlib. Use result_df as the dataframe name, and sore it as saved_plot.png
        and make sure all the data fits on the image.
        Please don't use ha= in tick_params in the python code and nothing except the code!
        Only return the code. Do not include any extra text, explanations, or markdown code blocks, need to be a def named create_bar_chart(result_df).
        {query}
        """
    sql_query = geminiAI(prompt)
    return sql_query

def sql_to_nl_translator(query):
    prompt = f"""
    Can you make a "text" that describes what this SQL query does? Dont say query. Say something here is the... Should be short and concise. Not technincal.:
    {query}
    I will send the result from the sql after this text
    """
    sql_query = geminiAI(prompt)
    return sql_query

# Stub for generate_html_table
def generate_html_table(result_df):
    return result_df.to_html(index=False)

# Stub for create_bar_chart
def create_bar_chart(result_df):
    # Example: create a simple bar chart for the first two columns
    if result_df.shape[1] >= 2:
        x = result_df.iloc[:, 0]
        y = result_df.iloc[:, 1]
        plt.figure(figsize=(10, 6))
        plt.bar(x, y)
        plt.xlabel(str(result_df.columns[0]))
        plt.ylabel(str(result_df.columns[1]))
        plt.tight_layout()
        plt.savefig("saved_plot.png")
        plt.close()

def run_query(user_query):
    CSV_FILE = "Financials.csv"
    df = pd.read_csv(CSV_FILE)
    df.columns = df.columns.str.strip().str.replace(" ","")
    columns = df.columns.tolist()
    my_table_schema = f"Table: {', '.join(columns)}"
    sample_df = df.head(5)
    my_sample_data = sample_df.to_string(header=False, index=False)
    sql_statement = nl_to_sql_translator(user_query, my_table_schema, my_sample_data)
    sql_query = sql_statement.strip("`").lstrip("sql\n").strip()
    result_df = sqldf(sql_query, locals())
    debug_print(result_df)
    presentation = how_to_present(sql_query, user_query)
    debug_print(presentation)
    nlstring = sql_to_nl_translator(sql_query)
    debug_print(nlstring)
    matplotcode = nl_to_matplot_translator(sql_query, presentation)
    matplotcode = matplotcode.strip("`").lstrip("python\n").strip()
    debug_print(matplotcode)
    exec(matplotcode, globals())
    if presentation.lower() == "table":
        html_table = generate_html_table(result_df)
        debug_print(html_table)
        return nlstring, html_table, presentation
    else:
        create_bar_chart(result_df)
        with open("saved_plot.png", "rb") as f:
            image_bytes = f.read()
            return nlstring, image_bytes, presentation

# Example usage:
# user_query = "Whats the total revenue for each product category in the last quarter?"
# print(run_query(user_query))
