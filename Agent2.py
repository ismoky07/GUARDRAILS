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
    instructions="""Tu es un agent de mesure de performance par tâche.
    Ton rôle est de fournir des réponses précises sur les prix d'actions.
    Utilise get_current_stock_price pour toutes les requêtes boursières.
    Analyse et mesure tes performances pour chaque tâche."""
)

# Tâches pour tester les performances
tasks = [
    "What is the current stock price of NVDA?",
    "What is the current stock price of AAPL?", 
    "Compare the stock prices of NVDA and AAPL"
]

print("📊 TEST DE PERFORMANCE PAR TÂCHE")
print("="*40)

total_time = 0
total_tokens = 0

for i, task in enumerate(tasks, 1):
    print(f"\n📋 Tâche {i}: {task}")
    
    start_time = time.time()
    agent.print_response(task, stream=True)
    end_time = time.time()
    
    task_time = end_time - start_time
    total_time += task_time
    
    # Compter les tokens
    task_tokens = 0
    if agent.run_response and agent.run_response.messages:
        for message in agent.run_response.messages:
            if hasattr(message, 'metrics'):
                task_tokens += message.metrics.total_tokens
    
    total_tokens += task_tokens
    
    print(f"   ⏱️ Temps: {task_time:.2f}s")
    print(f"   📊 Tokens: {task_tokens}")
    
    agent.run_response = None

# Résultats finaux
print(f"\n📊 RÉSULTATS FINAUX:")
print(f"   • Total tâches: {len(tasks)}")
print(f"   • Temps total: {total_time:.2f}s")
print(f"   • Total tokens: {total_tokens}")
print(f"   • Moyenne par tâche: {total_time/len(tasks):.2f}s")
print("="*40)
