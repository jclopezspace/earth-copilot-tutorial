#!/usr/bin/env python3
"""
Test script to run the search agent directly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from search_agent import search_agent
from promptflow.connections import AzureOpenAIConnection
from dotenv import load_dotenv

def main():
    # Load environment variables
    load_dotenv()
    
    # Create connection object
    aoai_connection = AzureOpenAIConnection(
        api_key=os.getenv("AOAI_KEY"),
        api_base=os.getenv("AOAI_ENDPOINT"),
        api_version=os.getenv("AOAI_VERSION", "2024-06-01")
    )
    
    # Test query
    test_query = "What satellite data is available for California wildfires in 2023?"
    
    print("🔍 Running Earth Copilot Search Agent...")
    print(f"Query: {test_query}")
    print("-" * 50)
    
    try:
        result = search_agent(
            ask=test_query,
            original_ask=test_query,
            safety_action="Accept",
            deployment_name=os.getenv("AOAI_DEPLOYMENT", "gpt-4o-mini"),
            intent="Earth and Social Science",
            aoai_connection=aoai_connection
        )
        
        print("✅ Result:")
        print(result)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nPlease check:")
        print("1. Your .env file has all required credentials")
        print("2. Your Azure services are properly configured")
        print("3. Your Azure AI Search index contains data")

if __name__ == "__main__":
    main()
