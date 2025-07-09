import os
import json
import pandas as pd
from dotenv import load_dotenv
from typing import List, Dict, Union

from langchain_core.tools import tool
from langchain_openai import AzureChatOpenAI
from langgraph.prebuilt import create_react_agent
from thefuzz import fuzz

# Load environment variables from .env file
load_dotenv()

# --- Refined Tool with Fuzzy Matching ---
@tool
def find_bad_calls_for_user(user_name: str, similarity_threshold: int = 80) -> Union[List[Dict], Dict]:
    """
    Searches local JSONL files for bad call records for a user, using fuzzy name matching.
    A 'bad call' is identified by 'High' or 'Medium' severity.
    Finds users even if the name is slightly misspelled or contains identifiers like 'XT'.
    """
    data_dir = "jsonl_data"
    if not os.path.exists(data_dir):
        return {"error": f"Data directory '{data_dir}' not found. Please run the data generation script."}

    bad_calls = []
    found_user_name = None

    for filename in os.listdir(data_dir):
        if filename.endswith(".jsonl"):
            filepath = os.path.join(data_dir, filename)
            with open(filepath, "r") as f:
                for line in f:
                    try:
                        record = json.loads(line)
                        display_name = record.get("User", {}).get("DisplayName", "")
                        
                        # Fuzzy match the display name against the query
                        ratio = fuzz.ratio(user_name.lower(), display_name.lower())
                        
                        if ratio >= similarity_threshold:
                            # If a match is found, check severity
                            if record.get("Severity") in ["High", "Medium"]:
                                if not found_user_name:
                                    found_user_name = display_name # Store the correctly cased name
                                bad_calls.append(record)
                    except json.JSONDecodeError:
                        continue # Ignore malformed lines
    
    if not bad_calls:
        return {"message": f"No bad calls found for a user matching '{user_name}'."}

    # Use pandas for a clean summary format, returning only the most relevant fields
    df = pd.DataFrame(bad_calls)
    output_data = json.loads(df[['timestamp', 'Severity', 'Issue', 'Platform', 'Description']].to_json(orient='records'))
    
    return {
        "found_user": found_user_name,
        "call_records": output_data
    }


# --- Agent Initialization with Expert System Prompt ---
def create_refined_agent():
    """Initializes and returns the LangGraph agent with an expert persona."""
    llm = AzureChatOpenAI(
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        temperature=0,
        streaming=True,
    )

    tools = [find_bad_calls_for_user]

    # CORRECTED: The system_message argument is removed from this function call.
    agent_executor = create_react_agent(llm, tools)
    return agent_executor


# --- Main Execution Block ---
if __name__ == "__main__":
    agent = create_refined_agent()
    
    # The system prompt is now defined here before being passed to the agent.
    system_prompt = """
    You are an expert Call Quality Data (CQD) Analyst. Your primary function is to analyze call quality reports for users and provide precise, actionable insights. Do not be vague.

    When you receive data from the `find_bad_calls_for_user` tool, your task is to:
    1.  Carefully review all the provided call records.
    2.  Synthesize the information into a structured report.
    3.  Identify recurring patterns, such as repeated issues or problems on a specific platform.
    4.  Provide concrete, actionable recommendations for an IT support team to investigate.

    Your final answer MUST be in the following Markdown format:

    ### CQD Analysis for [User's Name]

    **Summary of Findings:**
    A brief, one-sentence summary of the number of bad calls found and the general time frame.

    **Identified Patterns:**
    - **Most Frequent Issue:** [Name of the most common issue and how many times it occurred].
    - **Platform-Specific Problems:** [Note if issues are concentrated on a specific platform like Windows, CitrixVDI, etc.].
    - **Severity Trend:** [Mention if the issues are predominantly 'High' or 'Medium' severity].

    **Actionable Recommendations:**
    - **For IT Support:** [Provide 1-3 specific, numbered recommendations. For example: "1. Investigate the user's home network for packet loss, as this was reported multiple times." or "2. Verify the user's client version on their Windows device, as high CPU usage can be linked to outdated software."].
    """
    
    # Example query with a slightly misspelled name
    user_query = "Please find all bad calls for 'Jaimie Tores' and give me actionable insights."
    # Another example: user_query = "find bad calls for nayanxt"

    print(f"Querying for: {user_query}\n")
    
    # CORRECTED: The system_prompt is passed as the first message in the list.
    response = agent.invoke({
        "messages": [
            ("system", system_prompt),
            ("user", user_query)
        ]
    })
    
    print("\n--- CQD Expert Analysis ---")
    # The final, formatted answer is in the last message content
    print(response['messages'][-1].content)
