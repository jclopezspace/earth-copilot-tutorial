import os
import requests
import json
from dotenv import find_dotenv
from promptflow.core import tool
from promptflow.connections import AzureContentSafetyConnection


# The inputs section will change based on the arguments of the tool function, after you save the code
# Adding type to arguments and return value will help the system show the types properly
# Please update the function name/signature per need
@tool
def my_python_tool(prompt: str, acsConnection: AzureContentSafetyConnection) -> bool:

    # create request to prompt shield
    url = f"{acsConnection.endpoint}/contentsafety/text:shieldPrompt?api-version=2024-09-01"
    headers = {
        # "Accept": "application/geo+json",
        "Ocp-Apim-Subscription-Key": acsConnection.api_key,
        "Content-Type": "application/json",
    }
    response = requests.post(
        url=url, headers=headers, json={"userPrompt": prompt, "documents": []}
    )
    attackDetected = True
    if 200 <= response.status_code <= 226:
        print(f"Prompt shield request: {response.request.url}")
        print(f"Prompt shield response: {response.content}")

        response_json = json.loads(response.content)
        attackDetected = response_json["userPromptAnalysis"]["attackDetected"]
        print(f"Attack Detected: {attackDetected}")
    else:
        print(
            f"Unsuccessful call to Prompt Shield. Disabling further processing to be safe."
        )
    return attackDetected
