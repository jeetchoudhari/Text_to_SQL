import streamlit as st
import os
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv
import re
import pandasql as ps


# Set the page configuration
st.set_page_config(page_title="SQL Query Retrieval App", layout="centered")

# Function to load CSS from a file
def load_css(file_name):
    with open(file_name) as f:
        return f"<style>{f.read()}</style>"

# Load custom CSS
st.markdown(load_css("style.css"), unsafe_allow_html=True)

# Load environment variables
load_dotenv()


# Configure GenAI key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Function to load Google Gemini Model and provide queries as response
def get_gemini_response(question, prompt):
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content([prompt[0], question])
    return response.text

# Function to retrieve query from the DataFrame using eval
def read_sql_query(sql, df):
    try:
        result_df = ps.sqldf(sql, locals())
        return result_df
    except Exception as e:
        st.error(f"Query error: {e}")
        return pd.DataFrame()

# Streamlit App
st.title("Text to SQL")


#st.markdown("Press the button below to start recording your question.")

if 'transcription' not in st.session_state:
    st.session_state.transcription = ""



uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df_name = "df"  # Name for the dataframe in the prompt
    st.write("Data loaded successfully:")
    st.dataframe(df.head())

    # Dynamically create the prompt based on the DataFrame columns
    columns = ', '.join(df.columns)
    prompt = [
        f"""
        You are an expert in converting English questions to SQL query!
        The SQL database has the name {df_name} and has the following columns - {columns}.

        For example:
        Example 1 - How many entries of records are present?, the SQL command will be something like this:
        SELECT COUNT(*) FROM {df_name};

        Example 2 - Tell me all the entries where {df.columns[0]} is equal to "value", the SQL command will be something like this:
        SELECT * FROM {df_name} WHERE {df.columns[0]}="value";

        Please do not include ``` at the beginning or end and the SQL keyword in the output.
        """
    ]

    st.session_state.transcription = st.text_area("Input Question", value=st.session_state.transcription, height=100)


    if st.button("Click here to display results"):
        with st.spinner("Generating SQL query..."):
            response = get_gemini_response(st.session_state.transcription, prompt)
            st.success("SQL query generated!")

        sql_query = response.strip().split(';')[0].strip()

        st.code(sql_query, language='sql')

        with st.spinner("Executing SQL query..."):
            try:
                result = read_sql_query(sql_query, df)
                st.success("Query executed!")
                st.subheader("Query Results")
                st.dataframe(result)
            except Exception as e:
                #st.error(f"Query error: {e}")
                st.error("Query error: Result not found")
else:
    st.write("Please upload a CSV file to proceed.")
