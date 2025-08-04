
from promptflow.core import tool


# The inputs section will change based on the arguments of the tool function, after you save the code
# Adding type to arguments and return value will help the system show the types properly
# Please update the function name/signature per need
@tool
def my_python_tool(safety_result, attack_result: bool, sensitive_subject_filter: str, date_filter_result: str) -> str:
    suggested_safety_action = safety_result["suggested_action"]
    if (suggested_safety_action == 'Accept') and (sensitive_subject_filter == 'Accept') and (date_filter_result == 'Accept') and (attack_result == False):
        return 'Accept'
    else:
        return f"Attack Detected: {attack_result}, Content Safety Result: {suggested_safety_action}, Protected Groups Detection Result: {sensitive_subject_filter}, Date Validity Result: {date_filter_result}"
