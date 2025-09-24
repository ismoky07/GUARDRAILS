from typing import Iterator
import os
import agentops
from dotenv import load_dotenv
from agno.agent import Agent, RunResponse
from agno.models.xai import xAI
from agno.tools.yfinance import YFinanceTools
from rich.pretty import pprint

load_dotenv()
XAI_API_KEY = os.getenv("XAI_API_KEY")

AGENTOPS_API_KEY = os.getenv("AGENTOPS_API_KEY")

agentops.init(api_key=AGENTOPS_API_KEY, default_tags=['Agno'])

agent = Agent(
    model=xAI(id="grok-3", api_key=XAI_API_KEY),
    tools=[YFinanceTools(stock_price=True)],
    markdown=True,
    show_tool_calls=True,
    instructions="""Tu es un agent financier.
    Ton rôle est de fournir des réponses précises sur les prix d'actions.
    Utilise get_current_stock_price pour toutes les requêtes boursières.
    Surveille et trace tes performances en temps réel."""
)

agent.print_response(
    "What is the stock price of NVDA", stream=True
)

# Print metrics per message
if agent.run_response.messages:
    for message in agent.run_response.messages:
        if message.role == "assistant":
            if message.content:
                print(f"Message: {message.content}")
            elif message.tool_calls:
                print(f"Tool calls: {message.tool_calls}")
            print("---" * 5, "Metrics", "---" * 5)
            pprint(message.metrics)
            print("---" * 20)

# Print the aggregated metrics for the whole run
print("---" * 5, "Collected Metrics", "---" * 5)
pprint(agent.run_response.metrics)
# Print the aggregated metrics for the whole session
print("---" * 5, "Session Metrics", "---" * 5)
pprint(agent.session_metrics)