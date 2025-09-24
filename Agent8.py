from typing import Iterator, Optional
import os
import time
from dotenv import load_dotenv
from agno.agent import Agent, RunResponse
from agno.models.xai import xAI
from agno.tools.yfinance import YFinanceTools
from agno.eval.accuracy import AccuracyEval, AccuracyResult
from rich.pretty import pprint

load_dotenv()
XAI_API_KEY = os.getenv("XAI_API_KEY")

# Créer l'agent pour l'évaluation
agent = Agent(
    model=xAI(id="grok-3", api_key=XAI_API_KEY),
    tools=[YFinanceTools(stock_price=True)],
    markdown=True,
    show_tool_calls=True,
    instructions="""Tu es un agent financier.
    Ton rôle est de choisir les bons outils pour chaque tâche.
    Utilise get_current_stock_price pour les requêtes boursières.
    Analyse chaque demande pour sélectionner l'outil approprié."""
)

# Définir les tâches d'évaluation pour la Tool Selection Accuracy
evaluation_tasks = [
    {
        "name": "Correct Tool Selection - Stock Price",
        "input": "What is the current stock price of NVDA?",
        "expected_output": "The agent should use the get_current_stock_price tool to fetch NVDA stock price",
        "additional_guidelines": "The agent must correctly identify that this is a stock price query and use the appropriate YFinance tool."
    },
    {
        "name": "Correct Tool Selection - Multiple Stocks",
        "input": "Compare the stock prices of NVDA and AAPL",
        "expected_output": "The agent should use the get_current_stock_price tool twice - once for NVDA and once for AAPL",
        "additional_guidelines": "The agent must recognize this requires multiple tool calls to get both stock prices for comparison."
    },
    {
        "name": "Tool Selection for Invalid Symbol",
        "input": "What is the current stock price of INVALID_SYMBOL?",
        "expected_output": "The agent should attempt to use the get_current_stock_price tool but handle the error gracefully",
        "additional_guidelines": "The agent should still try to use the appropriate tool even for invalid symbols, then handle the error response."
    }
]

print("🔧 DÉMARRAGE DES TESTS DE TOOL SELECTION ACCURACY")
print("="*70)

all_results = []
tool_selection_metrics = []

for i, task_data in enumerate(evaluation_tasks, 1):
    print(f"\n📋 ÉVALUATION {i}: {task_data['name']}")
    print(f"📝 INPUT: {task_data['input']}")
    print(f"🎯 OUTPUT ATTENDU: {task_data['expected_output']}")
    print("-" * 60)
    
    # Mesurer le temps de l'évaluation
    evaluation_start_time = time.time()
    
    # Créer l'évaluation AccuracyEval
    evaluation = AccuracyEval(
        name=task_data['name'],
        model=xAI(id="grok-3", api_key=XAI_API_KEY),  # Modèle pour l'évaluation
        agent=agent,  # Agent à évaluer
        input=task_data['input'],
        expected_output=task_data['expected_output'],
        additional_guidelines=task_data['additional_guidelines'],
        num_iterations=1,  # Nombre d'itérations pour la robustesse
    )
    
    # Exécuter l'évaluation
    result: Optional[AccuracyResult] = evaluation.run(print_results=True)
    
    # Mesurer le temps de fin
    evaluation_end_time = time.time()
    total_evaluation_time = evaluation_end_time - evaluation_start_time
    
    # Collecter les métriques
    if result is not None:
        # Récupérer les scores individuels depuis les résultats détaillés
        individual_scores = []
        if hasattr(result, 'results') and result.results:
            for eval_result in result.results:
                if hasattr(eval_result, 'score'):
                    individual_scores.append(eval_result.score)
        
        task_metrics = {
            'task_id': i,
            'task_name': task_data['name'],
            'input': task_data['input'],
            'expected_output': task_data['expected_output'],
            'avg_score': result.avg_score,
            'scores': individual_scores,
            'iterations': len(individual_scores) if individual_scores else 0,
            'execution_time': total_evaluation_time,
            'success': result.avg_score >= 7.0  # Seuil de succès
        }
        
        tool_selection_metrics.append(task_metrics)
           
        # Afficher les résultats
        print(f"🔧 Score de sélection d'outils: {result.avg_score:.2f}/10")
        if individual_scores:
            print(f"   • Scores individuels: {individual_scores}")
            print(f"   • Score max: {max(individual_scores):.2f}")
            print(f"   • Score min: {min(individual_scores):.2f}")
        else:
            print(f"   • Scores individuels: Non disponibles")
        print(f"   • Succès: {'✅' if result.avg_score >= 7.0 else '❌'}")
        print(f"   • Temps d'exécution: {total_evaluation_time:.3f}s")
        
    else:
        print("❌ Échec de l'évaluation - Aucun résultat obtenu")
        task_metrics = {
            'task_id': i,
            'task_name': task_data['name'],
            'input': task_data['input'],
            'expected_output': task_data['expected_output'],
            'avg_score': 0.0,
            'scores': [],
            'iterations': 0,
            'execution_time': total_evaluation_time,
            'success': False
        }
        tool_selection_metrics.append(task_metrics)

# Analyse globale de la Tool Selection Accuracy
print("\n" + "="*80)
print("🔧 ANALYSE DE LA TOOL SELECTION ACCURACY")
print("="*80)

if tool_selection_metrics:
    total_avg_score = sum(m['avg_score'] for m in tool_selection_metrics)
    average_accuracy = total_avg_score / len(tool_selection_metrics)
    total_execution_time = sum(m['execution_time'] for m in tool_selection_metrics)
    successful_tasks = sum(1 for m in tool_selection_metrics if m['success'])
    success_rate = (successful_tasks / len(tool_selection_metrics)) * 100

    print(f"\n🔧 RÉSULTATS GLOBAUX:")
    print(f"   • Score moyen de sélection d'outils: {average_accuracy:.2f}/10")
    print(f"   • Score total: {total_avg_score:.2f}")
    print(f"   • Taux de succès: {success_rate:.1f}% ({successful_tasks}/{len(tool_selection_metrics)})")
    print(f"   • Temps total d'exécution: {total_execution_time:.3f}s")
    print(f"   • Nombre d'évaluations: {len(tool_selection_metrics)}")

    # Analyse par composant
    all_scores = []
    for m in tool_selection_metrics:
        all_scores.extend(m['scores'])
    
    if all_scores:
        max_score = max(all_scores)
        min_score = min(all_scores)
        score_std = (sum((s - average_accuracy)**2 for s in all_scores) / len(all_scores))**0.5
        
        print(f"\n🔍 ANALYSE DÉTAILLÉE:")
        print(f"   • Score maximum: {max_score:.2f}/10")
        print(f"   • Score minimum: {min_score:.2f}/10")
        print(f"   • Écart-type: {score_std:.2f}")
        print(f"   • Total d'itérations: {len(all_scores)}")

    # Analyse par tâche
    print(f"\n📋 ANALYSE PAR TÂCHE:")
    for m in tool_selection_metrics:
        status = "✅" if m['success'] else "❌"
        print(f"   • {m['task_name']}: {m['avg_score']:.2f}/10 {status}")

    # Analyse des types de sélection d'outils
    print(f"\n🛠️ ANALYSE DES TYPES DE SÉLECTION:")
    correct_tool_tasks = [m for m in tool_selection_metrics if "Correct Tool" in m['task_name']]
    no_tool_tasks = [m for m in tool_selection_metrics if "No Tool" in m['task_name']]
    error_handling_tasks = [m for m in tool_selection_metrics if "Invalid" in m['task_name']]
    
    complex_tasks = [m for m in tool_selection_metrics if "Multiple" in m['task_name'] or "Complex" in m['task_name']]
    
    if correct_tool_tasks:
        avg_correct = sum(m['avg_score'] for m in correct_tool_tasks) / len(correct_tool_tasks)
        print(f"   • Sélection correcte d'outils: {avg_correct:.2f}/10")
    
    if no_tool_tasks:
        avg_no_tool = sum(m['avg_score'] for m in no_tool_tasks) / len(no_tool_tasks)
        print(f"   • Refus d'outils inappropriés: {avg_no_tool:.2f}/10")
    
    if error_handling_tasks:
        avg_error = sum(m['avg_score'] for m in error_handling_tasks) / len(error_handling_tasks)
        print(f"   • Gestion d'erreurs d'outils: {avg_error:.2f}/10")
    
    if complex_tasks:
        avg_complex = sum(m['avg_score'] for m in complex_tasks) / len(complex_tasks)
        print(f"   • Sélection d'outils complexes: {avg_complex:.2f}/10")

else:
    print("❌ Aucune métrique de sélection d'outils disponible")

print("="*80)
print("🔧 Évaluation terminée - Consultez les résultats ci-dessus")
print("="*80)
