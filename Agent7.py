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
    Ton rôle est de fournir des réponses dans des formats spécifiques.
    Utilise get_current_stock_price pour les données boursières.
    Respecte strictement les formats de sortie demandés."""
)

# Définir les tâches d'évaluation avec AccuracyEval
evaluation_tasks = [
    {
        "name": "NVDA Stock Price Format Accuracy",
        "input": "What is the current stock price of NVDA? Please format your response as: STOCK: [symbol] | PRICE: $[amount]",
        "expected_output": "STOCK: NVDA | PRICE: $[amount]",
        "additional_guidelines": "The response should follow the exact format specified with STOCK: and PRICE: labels and include the dollar sign."
    },
   
   
    {
        "name": "Table Format Accuracy",
        "input": "Get TSLA stock price. Format as a table: | Symbol | Price |\n|--------|-------|\n| TSLA   | $[price] |",
        "expected_output": "| Symbol | Price |\n|--------|-------|\n| TSLA   | $[price] |",
        "additional_guidelines": "The response should be formatted as a proper markdown table with headers and data rows."
    }
]

print("📊 DÉMARRAGE DES TESTS D'ACCURACY AVEC AGNO FRAMEWORK")
print("="*70)

all_results = []
accuracy_metrics = []

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
        
        accuracy_metrics.append(task_metrics)
           
        # Afficher les résultats
        print(f"📊 Score moyen: {result.avg_score:.2f}/10")
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
        accuracy_metrics.append(task_metrics)

# Analyse globale de l'accuracy evaluation
print("\n" + "="*80)
print("📊 ANALYSE DE L'ACCURACY EVALUATION")
print("="*80)

if accuracy_metrics:
    total_avg_score = sum(m['avg_score'] for m in accuracy_metrics)
    average_accuracy = total_avg_score / len(accuracy_metrics)
    total_execution_time = sum(m['execution_time'] for m in accuracy_metrics)
    successful_tasks = sum(1 for m in accuracy_metrics if m['success'])
    success_rate = (successful_tasks / len(accuracy_metrics)) * 100

    print(f"\n📊 RÉSULTATS GLOBAUX:")
    print(f"   • Score moyen d'accuracy: {average_accuracy:.2f}/10")
    print(f"   • Score total: {total_avg_score:.2f}")
    print(f"   • Taux de succès: {success_rate:.1f}% ({successful_tasks}/{len(accuracy_metrics)})")
    print(f"   • Temps total d'exécution: {total_execution_time:.3f}s")
    print(f"   • Nombre d'évaluations: {len(accuracy_metrics)}")

    # Analyse par composant
    all_scores = []
    for m in accuracy_metrics:
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
    for m in accuracy_metrics:
        status = "✅" if m['success'] else "❌"
        print(f"   • {m['task_name']}: {m['avg_score']:.2f}/10 {status}")

else:
    print("❌ Aucune métrique d'accuracy disponible")

print("="*80)
print("📊 Évaluation terminée - Consultez les résultats ci-dessus")
print("="*80)