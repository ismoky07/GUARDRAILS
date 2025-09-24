import os
import time
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.xai import xAI
from agno.tools.yfinance import YFinanceTools
from agno.tools.calculator import CalculatorTools

load_dotenv()
XAI_API_KEY = os.getenv("XAI_API_KEY")

# Créer 2 agents spécialisés
stock_agent = Agent(
    model=xAI(id="grok-3", api_key=XAI_API_KEY),
    tools=[YFinanceTools(stock_price=True)],
    show_tool_calls=True,
    name="StockAgent"
)

calc_agent = Agent(
    model=xAI(id="grok-3", api_key=XAI_API_KEY),
    tools=[CalculatorTools()],
    show_tool_calls=True,
    name="CalcAgent"
)

# Tâches pour tester les interactions entre agents
interaction_tasks = [
    {
        "name": "Simple Stock Query",
        "input": "What is the stock price of NVDA?",
        "expected_agents": ["StockAgent"],
        "expected_interactions": 1
    },
    {
        "name": "Simple Calculation",
        "input": "Calculate 25 * 4",
        "expected_agents": ["CalcAgent"],
        "expected_interactions": 1
    },
    {
        "name": "Stock + Calculation",
        "input": "Get NVDA stock price and calculate 100 * 2.5",
        "expected_agents": ["StockAgent", "CalcAgent"],
        "expected_interactions": 2
    },
    {
        "name": "Complex Multi-Agent",
        "input": "Get AAPL stock price, calculate 50 + 75, and get MSFT stock price",
        "expected_agents": ["StockAgent", "CalcAgent", "StockAgent"],
        "expected_interactions": 3
    },
    {
        "name": "Calculation Chain",
        "input": "Calculate 10 * 5, then add 25, then multiply by 2",
        "expected_agents": ["CalcAgent", "CalcAgent", "CalcAgent"],
        "expected_interactions": 3
    }
]

print("🤝 AGENT INTERACTIONS COUNT TEST")
print("="*50)

total_interactions = 0
total_tasks = len(interaction_tasks)

for i, task in enumerate(interaction_tasks, 1):
    print(f"\n📋 Tâche {i}: {task['name']}")
    print(f"📝 Input: {task['input']}")
    print(f"🎯 Agents attendus: {', '.join(task['expected_agents'])}")
    print(f"📊 Interactions attendues: {task['expected_interactions']}")
    print("-" * 50)
    
    start_time = time.time()
    interactions_this_task = 0
    agents_used = []
    
    # Analyser le type de tâche et choisir l'agent approprié
    if "stock" in task['input'].lower() or any(symbol in task['input'].upper() for symbol in ['NVDA', 'AAPL', 'MSFT', 'TSLA', 'GOOGL']):
        print("🔄 Utilisation de StockAgent...")
        stock_agent.print_response(task['input'], stream=True)
        interactions_this_task += 1
        agents_used.append("StockAgent")
        
        # Vérifier si des calculs sont aussi nécessaires
        if any(op in task['input'] for op in ['+', '-', '*', '/', 'calculate', 'add', 'multiply', 'divide']):
            print("🔄 Utilisation de CalcAgent pour les calculs...")
            calc_agent.print_response(task['input'], stream=True)
            interactions_this_task += 1
            agents_used.append("CalcAgent")
    
    elif any(word in task['input'].lower() for word in ['calculate', 'add', 'multiply', 'divide', 'subtract']):
        print("🔄 Utilisation de CalcAgent...")
        calc_agent.print_response(task['input'], stream=True)
        interactions_this_task += 1
        agents_used.append("CalcAgent")
    
    else:
        print("🔄 Utilisation de StockAgent par défaut...")
        stock_agent.print_response(task['input'], stream=True)
        interactions_this_task += 1
        agents_used.append("StockAgent")
    
    end_time = time.time()
    total_interactions += interactions_this_task
    
    print(f"   🤝 Agents utilisés: {agents_used}")
    print(f"   📞 Interactions: {interactions_this_task}")
    print(f"   ⏱️ Temps: {end_time - start_time:.2f}s")
    
    # Vérifier si le nombre d'interactions correspond aux attentes
    if interactions_this_task == task['expected_interactions']:
        status = "✅"
    else:
        status = "❌"
    
    print(f"   📊 Résultat: {status} (Attendu: {task['expected_interactions']}, Obtenu: {interactions_this_task})")
    
    # Réinitialiser les agents
    stock_agent.run_response = None
    calc_agent.run_response = None

# Résultats finaux
avg_interactions = total_interactions / total_tasks if total_tasks > 0 else 0

print(f"\n📊 RÉSULTATS FINAUX:")
print(f"   • Total d'interactions: {total_interactions}")
print(f"   • Moyenne par tâche: {avg_interactions:.1f}")
print(f"   • Nombre de tâches: {total_tasks}")

# Analyse par type d'agent
stock_interactions = sum(1 for task in interaction_tasks if "StockAgent" in task['expected_agents'])
calc_interactions = sum(1 for task in interaction_tasks if "CalcAgent" in task['expected_agents'])

print(f"\n🔍 ANALYSE PAR AGENT:")
print(f"   • Interactions StockAgent: {stock_interactions}")
print(f"   • Interactions CalcAgent: {calc_interactions}")

print("="*50)