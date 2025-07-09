import os
import json
import pandas as pd
from dotenv import load_dotenv
from typing import List

from langchain_core.tools import tool
from langchain_openai import AzureChatOpenAI
from langgraph.prebuilt import create_react_agent

# Load environment variables from .env file
load_dotenv()

# --- Tool Definition ---
@tool
def find_bad_calls_for_user(user_name: str) -> List[dict]:
    """
    Searches through local JSONL files to find records of bad calls for a specific user.
    A 'bad call' is identified by 'High' or 'Medium' severity.
    """
    data_dir = "jsonl_data"
    if not os.path.exists(data_dir):
        return {"error": "Data directory 'jsonl_data' not found. Please run the data generation script first."}

    bad_calls = []
    for filename in os.listdir(data_dir):
        if filename.endswith(".jsonl"):
            filepath = os.path.join(data_dir, filename)
            with open(filepath, "r") as f:
                for line in f:
                    try:
                        record = json.loads(line)
                        if record.get("User", {}).get("DisplayName", "").lower() == user_name.lower():
                            if record.get("Severity") in ["High", "Medium"]:
                                bad_calls.append(record)
                    except json.JSONDecodeError:
                        continue # Ignore malformed lines
    
    if not bad_calls:
        return {"message": f"No bad calls found for user {user_name}."}

    # Use pandas for a clean summary format
    df = pd.DataFrame(bad_calls)
    return json.loads(df[['timestamp', 'Severity', 'Issue', 'Description']].to_json(orient='records'))


# --- Agent Initialization ---
def create_agent():
    """Initializes and returns the LangGraph agent."""
    # Initialize the Azure OpenAI LLM
    llm = AzureChatOpenAI(
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        temperature=0,
        streaming=True,
    )

    # Define the list of tools the agent can use
    tools = [find_bad_calls_for_user]

    # Create the agent using LangGraph's prebuilt function[3]
    agent_executor = create_react_agent(llm, tools)
    return agent_executor


# --- Main Execution Block ---
if __name__ == "__main__":
    agent = create_agent()
    
    # Define the query
    user_query = "Please find all bad calls for 'Jamie Torres' and give me actionable insights on the recurring problems."

    # Invoke the agent
    print(f"Querying for: {user_query}\n")
    
    # The agent will automatically select and run the `find_bad_calls_for_user` tool
    # and then use the LLM to generate insights from the tool's output.
    response = agent.invoke({"messages": [("user", user_query)]})
    
    # Print the final answer from the agent
    print("\n--- Actionable Insights ---")
    print(response['messages'][-1].content)
