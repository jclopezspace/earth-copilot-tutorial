from promptflow.core import tool
from promptflow.connections import AzureOpenAIConnection
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from prompt_templates import get_search_agent_JSON_output
from tools.geocoding_tool import geocode_location
from tools.system_time_tool import check_system_time
from tools.veda_collections_tool import determine_best_collections
from tools.fire_events_tool import search_fire_event
from dotenv import load_dotenv
import json
import os


# The inputs section will change based on the arguments of the tool function, after you save the code
# Adding type to arguments and return value will help the system show the types properly
# Please update the function name/signature per need
@tool
def search_agent(
    ask: str,
    original_ask: str,
    safety_action: str,
    deployment_name: str,
    intent: str,
    # chat_history: list[str],
    aoai_connection: AzureOpenAIConnection
    ) -> str:
    
    # filter based on safety
    if (safety_action == "Accept") and (intent == "Earth and Social Science"):

        # create LLM
        llm = AzureChatOpenAI(
            azure_endpoint=aoai_connection.api_base,
            openai_api_version=aoai_connection.api_version,
            deployment_name=deployment_name,
            openai_api_key=aoai_connection.api_key,
            openai_api_type="azure",
            max_tokens=12288,
            temperature=0,
            model_kwargs={"response_format": {"type": "json_object"}}
        )

        # grab our custom prompt template
        prompt_template: ChatPromptTemplate = get_search_agent_JSON_output()

        # instantiate some tools
        load_dotenv()
        # wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper(doc_content_chars_max=4000, top_k_results=1))
        
        tools = [check_system_time, determine_best_collections, geocode_location, search_fire_event]
        
        # create the agent
        agent = create_tool_calling_agent(llm, tools, prompt_template)

        # let the agent do its work
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True, max_iterations=5)
        result = agent_executor.invoke({"input": ask, "original_input": original_ask})
        
        return str(result['output'])
    else:
        print(f"Failed safety and intent checks. Safety Results: {safety_action}. Intent Detected: {intent}")
        return "{ \"summary\": \"I am sorry, I can't help you with that. I can however help with any questions you might have regarding data in VEDA\" }"
    
