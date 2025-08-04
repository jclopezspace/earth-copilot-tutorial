import os
import requests
import json
from dotenv import find_dotenv
from promptflow.core import tool
from promptflow.connections import AzureContentSafetyConnection, AzureOpenAIConnection


# The inputs section will change based on the arguments of the tool function, after you save the code
# Adding type to arguments and return value will help the system show the types properly
# Please update the function name/signature per need
@tool
def my_python_tool(agentOutput: str, acsConnection: AzureContentSafetyConnection, aoaiConnection: AzureOpenAIConnection) -> str:
    
    modifiedAgentOutput = agentOutput
    
    if agentOutput != "" and agentOutput != None:
    
        # split up Search Agent Output so we can process
        summary = ""
        query = ""
        collections = list()
        dateRange = {}
        location = {}
        explanation = {}
        try: 
            outputJson = json.loads(agentOutput)
            if 'summary' in outputJson:
                summary = outputJson['summary']
            if 'query' in outputJson:
                query = outputJson['query']
            if 'dataset_ids' in outputJson:
                collections = outputJson['dataset_ids']
            if 'date_range' in outputJson:
                dateRange = outputJson['date_range']
            if 'bbox' in outputJson:
                location = outputJson['bbox']
            if 'explanation' in outputJson:
                explanation = outputJson['explanation']
            
            # only check groundedness on successful responses (ie those not failing guardrail checks)
            if query != "":
            
                # create groundedness source
                groundedness_string: str = f"{query} {collections} {dateRange} {location} {explanation}"
                
                with open('./open_veda_collections_minimized.json', 'r') as file:
                    data = json.load(file)
                for collection in collections:
                    # find the description and title of that collection
                    for dict in data:
                        if dict['id'] == collection:
                            groundedness_string = f"{groundedness_string} {dict['title']} {dict['description']}"
                            
                
                #create request to groundedness detection
                url = f"{acsConnection.endpoint}contentsafety/text:detectGroundedness?api-version=2024-09-15-preview"
                headers = {
                            "Ocp-Apim-Subscription-Key": acsConnection.api_key,
                            "Content-Type": "application/json"
                        }
                response = requests.post (
                    url=url,
                    headers=headers,
                    json={  "domain": "Generic",
                            "task": "QnA",
                            "qna": {
                                "query": query
                            },
                            "text": summary,
                            "groundingSources": [groundedness_string],
                            "reasoning": False
                        }
                    )
                ungroundedDetected = True
                ungroundedPercentage = 0.0
                
                if 200 <= response.status_code <= 226:
                        
                    response_json=json.loads(response.content)
                    ungroundedDetected = response_json['ungroundedDetected']
                    ungroundedPercentage = response_json['ungroundedPercentage']
                    ungroundedDetails = response_json['ungroundedDetails']
                    ungroundedTexts = list()
                    print(f"Ungrounded Detected: {ungroundedDetected}")
                    print(f"Ungrounded Percentage (0-1) {ungroundedPercentage}")
                    # Update summary by removing any ungrounded text - sledgehammer way of doing it for now
                    for detail in ungroundedDetails:
                        print(f"Ungrounded text: {detail['text']}")
                        ungroundedTexts.append(detail['text'])
                        # summary = summary.replace(detail['text'], "")
                    # outputJson.update({"summary": summary})
                    validation = {
                        "evaluation": {
                            "ungrounded_detected": ungroundedDetected,
                            "ungrounded_percentage": ungroundedPercentage,
                            "ungrounded_text": ungroundedTexts
                        }
                    }
                    outputJson.update(validation)
                    modifiedAgentOutput = json.dumps(outputJson, indent=4)
                    # print(f"Updated Output: {modifiedAgentOutput}")
                
            else:
                print(f"Unsuccessful call to Groundedness detection.")
                print(f"Code: {response.status_code}")
                print(f"{response.content}")
                print(f"{response.headers}")
        except:
            print(f"Input is not valid JSON. Skipping Groundedness checks")
    else:
        print(f"Input is null. Skipping Groundedness check.")
        
            
    
    return modifiedAgentOutput