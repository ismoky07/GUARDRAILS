import os
import re
import sys
import time
import threading
from typing import Dict, List, Any
from dataclasses import dataclass
from textwrap import dedent
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.xai import xAI

load_dotenv()

@dataclass
class PerformanceMetric:
    """Structure pour stocker les métriques de performance"""
    type: str
    value: float
    unit: str
    timestamp: float
    context: Dict[str, Any]

class PerformanceTools:
    """Outils de performance pour les 4 mesures principales"""
    
    def __init__(self):
        # Historique des interventions humaines
        self.human_interventions = []
        self.intervention_count = 0
        
        # Suivi des étapes par tâche
        self.task_steps = {}
        self.current_task_id = None
        self.step_count = 0
        
        # Suivi des coûts
        self.cost_tracking = {
            'api_calls': 0,
            'tokens_used': 0,
            'storage_used': 0,
            'compute_time': 0
        }
        
        # Détection de boucles infinies
        self.loop_detection = {
            'call_history': [],
            'max_calls': 100,
            'timeout_threshold': 30,  # secondes
            'pattern_detection': True
        }
        
        # Coûts par type d'opération (exemples)
        self.cost_rates = {
            'api_call': 0.001,  # $0.001 par appel API
            'token': 0.0001,    # $0.0001 par token
            'storage_mb': 0.01, # $0.01 par MB de stockage
            'compute_second': 0.05  # $0.05 par seconde de calcul
        }
    
    def track_human_intervention(self, reason: str, task_id: str = None) -> None:
        """Enregistre une intervention humaine"""
        intervention = {
            'id': len(self.human_interventions) + 1,
            'reason': reason,
            'task_id': task_id or self.current_task_id,
            'timestamp': time.time(),
            'context': {
                'step_count': self.step_count,
                'cost_so_far': self.get_total_cost()
            }
        }
        
        self.human_interventions.append(intervention)
        self.intervention_count += 1
        
        print(f"🔧 Mesure Intervention humaine #{self.intervention_count}: {reason}")
    
    def start_task(self, task_id: str, description: str = None) -> None:
        """Démarre le suivi d'une nouvelle tâche"""
        self.current_task_id = task_id
        self.step_count = 0
        
        self.task_steps[task_id] = {
            'description': description,
            'start_time': time.time(),
            'steps': [],
            'interventions': 0,
            'cost': 0
        }
        
        print(f"📋 Mesure Nouvelle tâche démarrée: {task_id}")
    
    def add_step(self, step_description: str, step_type: str = "general") -> None:
        """Ajoute une étape à la tâche actuelle"""
        if not self.current_task_id:
            return
        
        step = {
            'step_number': self.step_count + 1,
            'description': step_description,
            'type': step_type,
            'timestamp': time.time(),
            'cost': 0.0  # Coût par défaut pour l'étape
        }
        
        self.task_steps[self.current_task_id]['steps'].append(step)
        self.step_count += 1
        
        print(f"📝 Mesure Étape {self.step_count}: {step_description}")
    
    def end_task(self, success: bool = True) -> Dict[str, Any]:
        """Termine la tâche actuelle et retourne les métriques"""
        if not self.current_task_id:
            return {}
        
        task = self.task_steps[self.current_task_id]
        task['end_time'] = time.time()
        task['duration'] = task['end_time'] - task['start_time']
        task['success'] = success
        task['total_steps'] = len(task['steps'])
        task['total_cost'] = self.get_total_cost()
        
        # Calculer les métriques
        metrics = {
            'task_id': self.current_task_id,
            'total_steps': task['total_steps'],
            'duration': task['duration'],
            'success': success,
            'cost': task['total_cost'],
            'interventions': task['interventions'],
            'steps_per_minute': task['total_steps'] / (task['duration'] / 60) if task['duration'] > 0 else 0
        }
        
        print(f"✅ Mesure Tâche terminée: {self.current_task_id}")
        print(f"📊 Mesure Étapes totales: {task['total_steps']}")
        print(f"⏱️ Mesure Durée: {task['duration']:.2f}s")
        print(f"💰 Mesure Coût: ${task['total_cost']:.4f}")
        
        self.current_task_id = None
        self.step_count = 0
        
        return metrics
    
    def track_api_call(self, tokens_used: int, call_type: str = "api") -> None:
        """Enregistre un appel API et ses coûts"""
        self.cost_tracking['api_calls'] += 1
        self.cost_tracking['tokens_used'] += tokens_used
        
        cost = self.cost_rates['api_call'] + (tokens_used * self.cost_rates['token'])
        self.cost_tracking['compute_time'] += 0.1  # Estimation du temps d'API
        
        print(f"🔌 Mesure Appel API: {tokens_used} tokens, coût: ${cost:.4f}")
    
    def track_storage(self, size_mb: float) -> None:
        """Enregistre l'utilisation du stockage"""
        self.cost_tracking['storage_used'] += size_mb
        cost = size_mb * self.cost_rates['storage_mb']
        
        print(f"💾 Mesure Stockage: {size_mb}MB, coût: ${cost:.4f}")
    
    def track_compute_time(self, duration_seconds: float) -> None:
        """Enregistre le temps de calcul"""
        self.cost_tracking['compute_time'] += duration_seconds
        cost = duration_seconds * self.cost_rates['compute_second']
        
        print(f"⚡ Mesure Calcul: {duration_seconds:.2f}s, coût: ${cost:.4f}")
    
    def get_total_cost(self) -> float:
        """Calcule le coût total"""
        api_cost = self.cost_tracking['api_calls'] * self.cost_rates['api_call']
        token_cost = self.cost_tracking['tokens_used'] * self.cost_rates['token']
        storage_cost = self.cost_tracking['storage_used'] * self.cost_rates['storage_mb']
        compute_cost = self.cost_tracking['compute_time'] * self.cost_rates['compute_second']
        
        return api_cost + token_cost + storage_cost + compute_cost
    
    
    def detect_infinite_loop(self, function_name: str, args: Dict[str, Any]) -> bool:
        """Détecte les boucles infinies"""
        current_time = time.time()
        
        # Ajouter l'appel à l'historique
        call = {
            'function': function_name,
            'args': args,
            'timestamp': current_time
        }
        self.loop_detection['call_history'].append(call)
        
        # Garder seulement les derniers appels
        if len(self.loop_detection['call_history']) > self.loop_detection['max_calls']:
            self.loop_detection['call_history'] = self.loop_detection['call_history'][-self.loop_detection['max_calls']:]
        
        # Détecter les patterns répétitifs
        if self.loop_detection['pattern_detection']:
            recent_calls = self.loop_detection['call_history'][-10:]  # Derniers 10 appels
            
            if len(recent_calls) >= 5:
                # Vérifier si la même fonction est appelée avec les mêmes arguments
                function_counts = {}
                for call in recent_calls:
                    key = f"{call['function']}_{hash(str(call['args']))}"
                    function_counts[key] = function_counts.get(key, 0) + 1
                
                # Si une fonction est appelée plus de 3 fois avec les mêmes arguments
                if max(function_counts.values()) > 3:
                    print(f"🔄 Mesure Boucle infinie détectée: {function_name}")
                    return True
        
        # Détecter les timeouts
        if len(self.loop_detection['call_history']) > 1:
            time_since_start = current_time - self.loop_detection['call_history'][0]['timestamp']
            if time_since_start > self.loop_detection['timeout_threshold']:
                print(f"⏰ Mesure Timeout détecté: {time_since_start:.2f}s")
                return True
        
        return False
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Génère un rapport de performance complet"""
        total_tasks = len(self.task_steps)
        completed_tasks = sum(1 for task in self.task_steps.values() if 'end_time' in task)
        
        avg_steps_per_task = 0
        avg_duration_per_task = 0
        avg_cost_per_task = 0
        
        if completed_tasks > 0:
            completed_task_data = [task for task in self.task_steps.values() if 'end_time' in task]
            avg_steps_per_task = sum(task['total_steps'] for task in completed_task_data) / completed_tasks
            avg_duration_per_task = sum(task['duration'] for task in completed_task_data) / completed_tasks
            avg_cost_per_task = sum(task['total_cost'] for task in completed_task_data) / completed_tasks
        
        report = {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'total_interventions': self.intervention_count,
            'total_cost': self.get_total_cost(),
            'avg_steps_per_task': avg_steps_per_task,
            'avg_duration_per_task': avg_duration_per_task,
            'avg_cost_per_task': avg_cost_per_task,
            'intervention_rate': self.intervention_count / completed_tasks if completed_tasks > 0 else 0,
            'cost_breakdown': {
                'api_calls': self.cost_tracking['api_calls'],
                'tokens_used': self.cost_tracking['tokens_used'],
                'storage_mb': self.cost_tracking['storage_used'],
                'compute_seconds': self.cost_tracking['compute_time']
            },
            'recent_interventions': self.human_interventions[-5:],  # 5 dernières interventions
            'task_summary': list(self.task_steps.values())[-5:]  # 5 dernières tâches
        }
        
        return report


class PerformanceAgent:
    """Agent de performance principal avec toutes les fonctionnalités"""
    
    def __init__(self):
        self.performance_tools = PerformanceTools()
        self.api_key = os.getenv("XAI_API_KEY")
        
        # Créer l'agent avec les outils de performance
        self.agent = Agent(
            name="Performance Assistant",
            model=xAI(id="grok-3-mini", api_key=self.api_key),
            tools=[self.performance_tools],
            markdown=True,
            show_tool_calls=True,
            instructions=dedent("""
            Tu es un agent de performance spécialisé dans la mesure et l'optimisation.
            Ton rôle est de :
            1. Suivre le nombre d'interventions humaines
            2. Compter les étapes par tâche
            3. Calculer les coûts par requête
            4. Détecter les boucles infinies
            
            Toujours prioriser l'efficacité et la performance.
            """)
        )
    
    def start_performance_tracking(self, task_id: str, description: str = None) -> None:
        """Démarre le suivi de performance pour une tâche"""
        self.performance_tools.start_task(task_id, description)
    
    def add_performance_step(self, step_description: str, step_type: str = "general") -> None:
        """Ajoute une étape de performance"""
        self.performance_tools.add_step(step_description, step_type)
    
    def track_human_intervention(self, reason: str) -> None:
        """Enregistre une intervention humaine"""
        self.performance_tools.track_human_intervention(reason)
    
    def end_performance_tracking(self, success: bool = True) -> Dict[str, Any]:
        """Termine le suivi de performance et retourne les métriques"""
        return self.performance_tools.end_task(success)
    
    def run_performance_analysis(self, query: str) -> str:
        """Exécute une analyse de performance avec l'agent complet"""
        print("🛡️ ANALYSE DE PERFORMANCE AVEC AGENT")
        print("="*50)
        
        # Démarrer le suivi
        task_id = f"analysis_{int(time.time())}"
        self.start_performance_tracking(task_id, f"Analyse: {query}")
        
        try:
            # Ajouter une étape
            self.add_performance_step("Démarrage de l'analyse", "analysis")
            
            # Utiliser l'agent pour traiter la requête
            response = self.agent.run(query)
            
            # Ajouter une étape
            self.add_performance_step("Traitement de la requête", "processing")
            
            # Simuler un appel API
            self.performance_tools.track_api_call(100, "analysis")
            
            print(f"📋 Requête: {query}")
            print(f"🔍 Réponse: {response.content}")
            
            # Terminer le suivi
            metrics = self.end_performance_tracking(True)
            
            return response.content
        except Exception as e:
            # Enregistrer l'intervention humaine
            self.track_human_intervention(f"Erreur lors de l'analyse: {str(e)}")
            
            error_msg = f"Erreur lors de l'analyse de performance: {str(e)}"
            print(f"❌ {error_msg}")
            
            # Terminer le suivi avec échec
            self.end_performance_tracking(False)
            
            return error_msg
    
    def search_performance_news(self, topic: str) -> str:
        """Recherche des actualités de performance avec Google Search"""
        print(f"🔍 RECHERCHE D'ACTUALITÉS DE PERFORMANCE: {topic}")
        print("="*50)
        
        # Démarrer le suivi
        task_id = f"search_{int(time.time())}"
        self.start_performance_tracking(task_id, f"Recherche: {topic}")
        
        try:
            # Ajouter une étape
            self.add_performance_step("Démarrage de la recherche", "search")
            
            # Utiliser l'agent avec Google Search pour les actualités
            query = f"Recherche les dernières actualités et tendances de performance concernant {topic} en utilisant Google Search. Inclus les benchmarks et les optimisations."
            response = self.agent.run(query)
            
            # Ajouter une étape
            self.add_performance_step("Traitement des résultats", "processing")
            
            # Simuler un appel API
            self.performance_tools.track_api_call(150, "search")
            
            # Terminer le suivi
            self.end_performance_tracking(True)
            
            return response.content
        except Exception as e:
            # Enregistrer l'intervention humaine
            self.track_human_intervention(f"Erreur lors de la recherche: {str(e)}")
            
            error_msg = f"Erreur lors de la recherche d'actualités: {str(e)}"
            print(f"❌ {error_msg}")
            
            # Terminer le suivi avec échec
            self.end_performance_tracking(False)
            
            return error_msg
    
    def search_performance_metrics(self, metric_type: str) -> str:
        """Recherche des métriques de performance spécifiques avec Google Search"""
        print(f"🔍 RECHERCHE DE MÉTRIQUES DE PERFORMANCE: {metric_type}")
        print("="*50)
        
        # Démarrer le suivi
        task_id = f"metrics_{int(time.time())}"
        self.start_performance_tracking(task_id, f"Métriques: {metric_type}")
        
        try:
            # Ajouter une étape
            self.add_performance_step("Démarrage de la recherche de métriques", "search")
            
            query = f"Recherche les métriques de performance concernant {metric_type} en utilisant Google Search. Inclus les benchmarks et les outils de mesure."
            response = self.agent.run(query)
            
            # Ajouter une étape
            self.add_performance_step("Traitement des métriques", "processing")
            
            # Simuler un appel API
            self.performance_tools.track_api_call(120, "metrics")
            
            # Terminer le suivi
            self.end_performance_tracking(True)
            
            return response.content
        except Exception as e:
            # Enregistrer l'intervention humaine
            self.track_human_intervention(f"Erreur lors de la recherche de métriques: {str(e)}")
            
            error_msg = f"Erreur lors de la recherche de métriques: {str(e)}"
            print(f"❌ {error_msg}")
            
            # Terminer le suivi avec échec
            self.end_performance_tracking(False)
            
            return error_msg
    
    def get_performance_timestamp(self) -> str:
        """Obtient l'horodatage pour les audits de performance"""
        print("⏰ HORODATAGE POUR AUDIT DE PERFORMANCE")
        print("="*50)
        
        try:
            query = "Quelle est la date et l'heure actuelle pour l'audit de performance ?"
            response = self.agent.run(query)
            
            return response.content
        except Exception as e:
            error_msg = f"Erreur lors de l'obtention de l'horodatage: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Obtient le rapport de performance complet"""
        print("📊 RAPPORT DE PERFORMANCE")
        print("="*50)
        
        report = self.performance_tools.get_performance_report()
        
        print(f"📈 Mesure Tâches totales: {report['total_tasks']}")
        print(f"✅ Mesure Tâches terminées: {report['completed_tasks']}")
        print(f"🔧 Mesure Interventions humaines: {report['total_interventions']}")
        print(f"💰 Mesure Coût total: ${report['total_cost']:.4f}")
        print(f"📝 Mesure Étapes moyennes par tâche: {report['avg_steps_per_task']:.2f}")
        print(f"⏱️ Mesure Durée moyenne par tâche: {report['avg_duration_per_task']:.2f}s")
        print(f"💵 Mesure Coût moyen par tâche: ${report['avg_cost_per_task']:.4f}")
        print(f"🔧 Mesure Taux d'intervention: {report['intervention_rate']:.2%}")
        
        return report
    
    def detect_infinite_loop(self, function_name: str, args: Dict[str, Any]) -> bool:
        """Détecte les boucles infinies"""
        return self.performance_tools.detect_infinite_loop(function_name, args)
    
    def secure_code_execution(self, code: str) -> Dict[str, Any]:
        """Exécute du code de manière sécurisée dans un environnement isolé"""
        print("🔒 EXÉCUTION SÉCURISÉE DU CODE")
        print("="*40)
        
        # Démarrer le suivi
        task_id = f"execution_{int(time.time())}"
        self.start_performance_tracking(task_id, "Exécution de code")
        
        try:
            # Ajouter une étape
            self.add_performance_step("Analyse du code", "analysis")
            
            # Détecter les boucles infinies potentielles
            if self.detect_infinite_loop("code_execution", {"code": code}):
                self.track_human_intervention("Boucle infinie détectée dans le code")
                return {
                    'success': False,
                    'error': 'Boucle infinie détectée',
                    'intervention_required': True
                }
            
            # Ajouter une étape
            self.add_performance_step("Exécution dans l'environnement isolé", "execution")
            
            # Exécuter dans l'environnement isolé
            result = self.isolated_env.execute_in_isolation(code)
            
            # Ajouter une étape
            self.add_performance_step("Traitement des résultats", "processing")
            
            # Simuler le coût de calcul
            self.performance_tools.track_compute_time(1.0)
            
            print(f"✅ Mesure Exécution terminée: {result['success']}")
            if result['stdout']:
                print(f"📤 Mesure Sortie: {result['stdout']}")
            if result['stderr']:
                print(f"❌ Mesure Erreurs: {result['stderr']}")
            
            # Terminer le suivi
            self.end_performance_tracking(result['success'])
            
            return result
        except Exception as e:
            # Enregistrer l'intervention humaine
            self.track_human_intervention(f"Erreur lors de l'exécution: {str(e)}")
            
            error_msg = f"Erreur lors de l'exécution: {str(e)}"
            print(f"❌ {error_msg}")
            
            # Terminer le suivi avec échec
            self.end_performance_tracking(False)
            
            return {
                'success': False,
                'error': error_msg,
                'intervention_required': True
            }
    
    def cleanup(self):
        """Nettoie les ressources"""
        self.isolated_env.cleanup()

# Exemple d'utilisation
if __name__ == "__main__":
    # Créer l'agent de performance
    performance_agent = PerformanceAgent()
    
    print("🛡️ AGENT DE PERFORMANCE - 4 MESURES PRINCIPALES")
    print("="*60)
    
    # Test 1: Suivi des interventions humaines
    print("\n📋 MESURE 1: HUMAN INTERVENTIONS TRACKING")
    print("-" * 40)
    performance_agent.start_performance_tracking("task_1", "Test des interventions humaines")
    performance_agent.track_human_intervention("Correction d'erreur de validation")
    performance_agent.track_human_intervention("Ajustement de paramètres")
    performance_agent.track_human_intervention("Validation manuelle des résultats")
    performance_agent.add_performance_step("Étape de validation", "validation")
    metrics_1 = performance_agent.end_performance_tracking(True)
    print(f"Mesure Interventions humaines: {metrics_1.get('interventions', 0)}")
    print(f"Mesure Durée de la tâche: {metrics_1.get('duration', 0):.2f}s")
    
    # Test 2: Suivi des étapes par tâche
    print("\n📋 MESURE 2: STEPS PER TASK TRACKING")
    print("-" * 40)
    performance_agent.start_performance_tracking("task_2", "Test des étapes par tâche")
    performance_agent.add_performance_step("Initialisation", "init")
    performance_agent.add_performance_step("Traitement des données", "processing")
    performance_agent.add_performance_step("Validation des résultats", "validation")
    performance_agent.add_performance_step("Optimisation", "optimization")
    performance_agent.add_performance_step("Finalisation", "finalization")
    metrics_2 = performance_agent.end_performance_tracking(True)
    print(f"Mesure Étapes par tâche: {metrics_2.get('total_steps', 0)}")
    print(f"Mesure Durée de la tâche: {metrics_2.get('duration', 0):.2f}s")
    
    # Test 3: Suivi des coûts par requête
    print("\n📋 MESURE 3: COST PER REQUEST TRACKING")
    print("-" * 40)
    performance_agent.start_performance_tracking("task_3", "Test des coûts par requête")
    performance_agent.performance_tools.track_api_call(150, "api_call")
    performance_agent.performance_tools.track_api_call(200, "api_call")
    performance_agent.performance_tools.track_storage(2.5)
    performance_agent.performance_tools.track_storage(1.8)
    performance_agent.performance_tools.track_compute_time(1.2)
    performance_agent.performance_tools.track_compute_time(0.8)
    performance_agent.add_performance_step("Calcul des coûts", "cost_calculation")
    metrics_3 = performance_agent.end_performance_tracking(True)
    print(f"Mesure Coût total: ${metrics_3.get('cost', 0):.4f}")
    print(f"Mesure Appels API: {performance_agent.performance_tools.cost_tracking['api_calls']}")
    print(f"Mesure Tokens utilisés: {performance_agent.performance_tools.cost_tracking['tokens_used']}")
    
    # Test 4: Détection de boucles infinies
    print("\n📋 MESURE 4: INFINITE LOOP DETECTION")
    print("-" * 40)
    # Simuler des appels répétitifs
    loop_detected = False
    for i in range(5):
        loop_detected = performance_agent.performance_tools.detect_infinite_loop("test_function", {"param": "value"})
        if loop_detected:
            print(f"Mesure Boucle infinie détectée à l'itération {i+1}")
            break
    if not loop_detected:
        print("Mesure Aucune boucle infinie détectée")
    
    # Test 5: Test combiné avec toutes les métriques
    print("\n📋 MESURE 5: TEST COMBINÉ - TOUTES LES MÉTRIQUES")
    print("-" * 40)
    performance_agent.start_performance_tracking("task_combined", "Test combiné")
    performance_agent.track_human_intervention("Intervention pour optimisation")
    performance_agent.add_performance_step("Étape 1", "step1")
    performance_agent.add_performance_step("Étape 2", "step2")
    performance_agent.performance_tools.track_api_call(100, "combined")
    performance_agent.performance_tools.track_storage(1.0)
    performance_agent.performance_tools.track_compute_time(0.5)
    metrics_combined = performance_agent.end_performance_tracking(True)
    print(f"Mesure Total étapes: {metrics_combined.get('total_steps', 0)}")
    print(f"Mesure Interventions: {metrics_combined.get('interventions', 0)}")
    print(f"Mesure Coût total: ${metrics_combined.get('cost', 0):.4f}")
    print(f"Mesure Durée: {metrics_combined.get('duration', 0):.2f}s")
    
    print("\n✅ Tests de performance terminés!")
    print("="*60)
