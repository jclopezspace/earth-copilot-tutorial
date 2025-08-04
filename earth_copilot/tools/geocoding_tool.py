from langchain.agents import tool
import os
import requests
from dotenv import load_dotenv, find_dotenv
    
# LangChain tool that geocodes a placename using Azure Maps API. Intended to be passed into
# and utilized by a LangChain ReAct Agent at runtime
# Parameters: 
#   text - A placename
@tool
def geocode_location(text: str) -> str:
    """Geocode a query (location, region, or landmark)"""
    
    find_dotenv()
    SUBSCRIPTION_KEY = os.getenv("AZURE_MAPS_SUBSCRIPTION_KEY")
    GEOCODE_API_URL = "https://atlas.microsoft.com/geocode"
    GEOCODE_API_VERSION = "2023-06-01"
    
    response = requests.get(
                "{geocode_api_url}?api-version={geocode_api_version}&subscription-key={key}&query={query}".format(
                    geocode_api_url=GEOCODE_API_URL,
                    geocode_api_version = GEOCODE_API_VERSION,
                    key=SUBSCRIPTION_KEY,
                    query=text
                )
            )
    if 200 <= response.status_code <= 226:
        try:        
            return response.json()
        except:
            return response.content
    else:
        return "Error in geocoding attempt"