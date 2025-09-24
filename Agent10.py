import os
import time
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.xai import xAI
from agno.tools.yfinance import YFinanceTools
from agno.tools.calculator import CalculatorTools

load_dotenv()
XAI_API_KEY = os.getenv("XAI_API_KEY")

# Créer l'agent avec 2 outils
agent = Agent(
    model=xAI(id="grok-3", api_key=XAI_API_KEY),
    tools=[YFinanceTools(stock_price=True), CalculatorTools()],
    show_tool_calls=True,
    instructions="""Tu es un agent polyvalent financier et mathématique.
    Tu peux récupérer les prix d'actions et effectuer des calculs.
    Utilise get_current_stock_price pour les données boursières.
    Utilise les outils de calcul pour les opérations mathématiques."""
)

# Tâches pour tester le nombre d'appels d'API
tasks = [
    {"input": "What is the current stock price of NVDA?", "expected_tools": ["get_current_stock_price"]},
    {"input": "Calculate 15 * 25", "expected_tools": ["multiply"]},
    {"input": "Get AAPL stock price and calculate 100 * 2.5", "expected_tools": ["get_current_stock_price", "multiply"]}
]

print("📞 API CALLS COUNT TEST")
print("="*30)

total_api_calls = 0
total_tasks = len(tasks)

for i, task in enumerate(tasks, 1):
    print(f"\n📋 Tâche {i}: {task['input']}")
    
    start_time = time.time()
    agent.print_response(task['input'], stream=True)
    end_time = time.time()
    
    # Compter les appels d'API
    api_calls_this_task = 0
    tools_used = []
    
    if agent.run_response and agent.run_response.messages:
        for message in agent.run_response.messages:
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    api_calls_this_task += 1
                    if isinstance(tool_call, dict):
                        tool_name = tool_call.get('function', {}).get('name', 'unknown')
                    else:
                        tool_name = getattr(tool_call, 'function', {}).get('name', 'unknown')
                    tools_used.append(tool_name)
    
    total_api_calls += api_calls_this_task
    
    print(f"   🔧 Outils: {tools_used}")
    print(f"   📞 Appels: {api_calls_this_task}")
    
    agent.run_response = None

# Résultats finaux
avg_api_calls = total_api_calls / total_tasks if total_tasks > 0 else 0

print(f"\n📊 RÉSULTATS FINAUX:")
print(f"   • Total appels d'API: {total_api_calls}")
print(f"   • Moyenne par tâche: {avg_api_calls:.1f}")
print("="*30)