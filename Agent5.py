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
    Ton rôle est de fournir des réponses précises sur les prix d'actions.
    Utilise get_current_stock_price pour toutes les requêtes boursières.
    Mesure et évalue la qualité de tes réponses."""
)

# Tâches pour mesurer le succès et l'achèvement
tasks = [
    "What is the current stock price of NVDA?",
    "What is the current stock price of MSFT?",
    "What is the current stock price of INVALID?"
]

print("✅ TEST DE SUCCÈS ET D'ACHÈVEMENT")
print("="*40)

successful = 0
completed = 0

for i, task in enumerate(tasks, 1):
    print(f"\n📋 Tâche {i}: {task}")
    
    start_time = time.time()
    agent.print_response(task, stream=True)
    end_time = time.time()
    
    # Vérifier le succès basé sur la réponse
    if agent.run_response and agent.run_response.messages:
        for message in agent.run_response.messages:
            if message.role == "assistant" and message.content:
                response = message.content.lower()
                if "$" in response and "stock" in response:
                    successful += 1
                    completed += 1
                elif "invalid" in response or "error" in response:
                    completed += 1
                break
    
    print(f"   ⏱️ Temps: {end_time - start_time:.2f}s")
    agent.run_response = None

# Calcul des taux
success_rate = (successful / len(tasks)) * 100
completion_rate = (completed / len(tasks)) * 100

print(f"\n📊 RÉSULTATS FINAUX:")
print(f"   • Tâches réussies: {successful}/{len(tasks)} ({success_rate:.1f}%)")
print(f"   • Tâches terminées: {completed}/{len(tasks)} ({completion_rate:.1f}%)")
print("="*40)