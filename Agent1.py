from typing import Iterator
import os
from dotenv import load_dotenv
from agno.agent import Agent, RunResponse
from agno.models.xai import xAI
from agno.tools.yfinance import YFinanceTools
from rich.pretty import pprint

load_dotenv()
XAI_API_KEY = os.getenv("XAI_API_KEY")

agent = Agent(
    model=xAI(id="grok-3", api_key=XAI_API_KEY),
    tools=[YFinanceTools(stock_price=True)],
    markdown=True,
    show_tool_calls=True,
    instructions="""Tu es un agent financier.
    Ton rôle est de fournir des réponses sur les prix d'actions.
    Utilise get_current_stock_price pour toutes les requêtes boursières.
    Fournis des réponses claires et précises."""
)

agent.print_response(
    "What is the stock price of NVDA", stream=True
)

# Print detailed metrics per tool call
if agent.run_response.messages:
    print("\n" + "="*60)
    print("DÉTAILS DES MÉTRIQUES PAR APPEL D'OUTIL")
    print("="*60)
    
    total_tokens = 0
    total_time = 0
    tool_call_count = 0
    
    for i, message in enumerate(agent.run_response.messages):
        print(f"\n--- Message {i+1} (Rôle: {message.role}) ---")
        
        if message.role == "user":
            print(f"Question utilisateur: {message.content}")
        elif message.role == "assistant":
            if message.content:
                print(f"Contenu: {message.content}")
            
            if message.tool_calls:
                tool_call_count += 1
                print(f"Appels d'outils: {len(message.tool_calls)}")
                for j, tool_call in enumerate(message.tool_calls):
                    if isinstance(tool_call, dict):
                        print(f"  Outil {j+1}: {tool_call.get('function', {}).get('name', 'Unknown')}")
                        print(f"  Arguments: {tool_call.get('function', {}).get('arguments', 'None')}")
                    else:
                        print(f"  Outil {j+1}: {getattr(tool_call, 'function', {}).get('name', 'Unknown')}")
                        print(f"  Arguments: {getattr(tool_call, 'function', {}).get('arguments', 'None')}")
            
            # Métriques détaillées
            metrics = message.metrics
            print(f"\n📊 MÉTRIQUES DÉTAILLÉES:")
            print(f"  • Tokens d'entrée: {metrics.input_tokens}")
            print(f"  • Tokens de sortie: {metrics.output_tokens}")
            print(f"  • Total tokens: {metrics.total_tokens}")
            print(f"  • Temps d'exécution: {metrics.time:.3f}s")
            print(f"  • Temps jusqu'au premier token: {metrics.time_to_first_token:.3f}s")
            
            # Calculs de latence
            latency = metrics.time - metrics.time_to_first_token
            print(f"  • Latence de génération: {latency:.3f}s")
            
            # Tokens par seconde
            if metrics.time > 0:
                tokens_per_second = metrics.total_tokens / metrics.time
                print(f"  • Tokens/seconde: {tokens_per_second:.2f}")
            
            total_tokens += metrics.total_tokens
            total_time += metrics.time
            
            print("-" * 40)
    
    # Résumé global
    print(f"\n📈 RÉSUMÉ GLOBAL:")
    print(f"  • Nombre total d'appels d'outils: {tool_call_count}")
    print(f"  • Total tokens utilisés: {total_tokens}")
    print(f"  • Temps total d'exécution: {total_time:.3f}s")
    if total_time > 0:
        print(f"  • Tokens/seconde moyen: {total_tokens/total_time:.2f}")
    
    print("="*60)
