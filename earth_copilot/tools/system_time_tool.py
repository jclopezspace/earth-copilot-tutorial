import datetime
from langchain.agents import tool

@tool
def check_system_time(format: str = "%Y-%m-%d %H:%M:%S"):
    """ Returns the current date and time in the specified format"""
    current_time = datetime.datetime.now()
    formatted_time = current_time.strftime(format)
    return formatted_time