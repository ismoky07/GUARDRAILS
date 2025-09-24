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
    Ton rôle est de récupérer les prix d'actions en temps réel.
    Utilise l'outil get_current_stock_price pour toutes les requêtes boursières.
    Fournis des réponses précises et professionnelles."""
)

# Tâches simples pour tester le Tool Success Rate
tasks = [
    {"input": "What is the stock price of NVDA?", "should_work": True},
    {"input": "Get AAPL stock price", "should_work": True},
    {"input": "What is the stock price of INVALID?", "should_work": False}
]

print("🛠️ TOOL SUCCESS RATE TEST")
print("="*30)

successful = 0
total = len(tasks)

for i, task in enumerate(tasks, 1):
    print(f"\n📋 Tâche {i}: {task['input']}")
    
    start_time = time.time()
    agent.print_response(task['input'], stream=True)
    end_time = time.time()
    
    # Vérifier si l'outil a fonctionné
    tool_worked = False
    if agent.run_response and agent.run_response.messages:
        for message in agent.run_response.messages:
            if message.tool_calls:
                tool_worked = True
                break
    
    # Déterminer le succès
    if task['should_work'] and tool_worked:
        successful += 1
        status = "✅"
    elif not task['should_work'] and not tool_worked:
        successful += 1
        status = "✅"
    else:
        status = "❌"
    
    print(f"   Résultat: {status} (Temps: {end_time - start_time:.2f}s)")
    agent.run_response = None

# Résultats finaux
success_rate = (successful / total) * 100
print(f"\n📊 RÉSULTATS:")
print(f"   • Taux de succès: {success_rate:.1f}% ({successful}/{total})")
print("="*30)