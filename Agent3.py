import os
import time
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.xai import xAI
from agno.tools.yfinance import YFinanceTools

load_dotenv()
XAI_API_KEY = os.getenv("XAI_API_KEY")

# Créer l'agent
agent = Agent(
    model=xAI(id="grok-3", api_key=XAI_API_KEY),
    tools=[YFinanceTools(stock_price=True)],
    show_tool_calls=True,
    instructions="""Tu es un agent financier.
    Ton rôle est de fournir des réponses rapides sur les prix d'actions.
    Utilise get_current_stock_price pour toutes les requêtes boursières.
    Optimise tes temps de réponse pour de meilleures performances."""
)

# Tâches pour mesurer la latence
tasks = [
    "What is the current stock price of NVDA?",
    "Compare the stock prices of NVDA and AAPL"
]

print("⏱️ TEST DE LATENCE PAR REQUÊTE")
print("="*40)

total_time = 0

for i, task in enumerate(tasks, 1):
    print(f"\n📋 Tâche {i}: {task}")
    
    start_time = time.time()
    agent.print_response(task, stream=True)
    end_time = time.time()
    
    task_time = end_time - start_time
    total_time += task_time
    
    print(f"   ⏱️ Temps: {task_time:.2f}s")
    
    agent.run_response = None

# Résultats finaux
print(f"\n⏱️ RÉSULTATS FINAUX:")
print(f"   • Total tâches: {len(tasks)}")
print(f"   • Temps total: {total_time:.2f}s")
print(f"   • Moyenne par tâche: {total_time/len(tasks):.2f}s")
print("="*40)