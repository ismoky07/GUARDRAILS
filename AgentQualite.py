import os
import re
import sys
import time
import numpy as np
from typing import Dict, List, Any
from dataclasses import dataclass
from textwrap import dedent
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.xai import xAI

load_dotenv()

@dataclass
class QualityIssue:
    """Structure pour stocker les problèmes de qualité détectés"""
    type: str
    severity: str
    description: str
    confidence: float
    metrics: Dict[str, Any]

class QualityTools:
    """Outils de qualité pour la détection des problèmes"""
    
    def __init__(self):
        # Patterns de détection d'hallucinations
        self.hallucination_patterns = [
            r'according\s+to\s+(my\s+)?knowledge',
            r'as\s+far\s+as\s+I\s+know',
            r'I\s+believe\s+',
            r'it\s+seems\s+like',
            r'probably\s+',
            r'likely\s+',
            r'I\s+think\s+',
            r'from\s+what\s+I\s+understand',
            r'if\s+I\s+remember\s+correctly',
            r'to\s+my\s+knowledge'
        ]
        
        # Patterns de détection de biais
        self.bias_patterns = {
            'cultural': [
                r'western\s+culture',
                r'eastern\s+culture',
                r'american\s+way',
                r'european\s+tradition',
                r'asian\s+values',
                r'african\s+culture'
            ],
            'gender': [
                r'he\s+should\s+',
                r'she\s+should\s+',
                r'man\s+up',
                r'act\s+like\s+a\s+man',
                r'be\s+more\s+feminine',
                r'typical\s+(man|woman)'
            ],
            'social': [
                r'rich\s+people',
                r'poor\s+people',
                r'educated\s+class',
                r'working\s+class',
                r'elite\s+',
                r'common\s+folk'
            ],
            'age': [
                r'young\s+people\s+should',
                r'old\s+people\s+',
                r'millennials\s+',
                r'boomers\s+',
                r'generation\s+',
                r'age\s+appropriate'
            ]
        }
        
        # Historique pour détection de dérive
        self.input_history = []
        self.output_history = []
        self.max_history_size = 1000
        
        # Niveaux de sévérité
        self.severity_levels = {
            'hallucination': 'HIGH',
            'bias': 'MEDIUM',
            'input_drift': 'LOW',
            'output_drift': 'MEDIUM'
        }
    
    def detect_hallucination(self, text: str) -> List[QualityIssue]:
        """Détecte les hallucinations dans le texte"""
        issues = []
        
        for pattern in self.hallucination_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                issue = QualityIssue(
                    type='hallucination',
                    severity=self.severity_levels['hallucination'],
                    description=f"Hallucination potentielle détectée: {match.group()}",
                    confidence=self._calculate_confidence(match.group(), 'hallucination'),
                    metrics={'pattern': pattern, 'position': match.start()}
                )
                issues.append(issue)
        
        return issues
    
    def detect_bias(self, text: str) -> List[QualityIssue]:
        """Détecte les biais dans le texte"""
        issues = []
        
        for bias_type, patterns in self.bias_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    issue = QualityIssue(
                        type=f'bias_{bias_type}',
                        severity=self.severity_levels['bias'],
                        description=f"Biais {bias_type} détecté: {match.group()}",
                        confidence=self._calculate_confidence(match.group(), 'bias'),
                        metrics={'bias_type': bias_type, 'pattern': pattern, 'position': match.start()}
                    )
                    issues.append(issue)
        
        return issues
    
    def detect_input_drift(self, new_input: str) -> List[QualityIssue]:
        """Détecte la dérive dans les données d'entrée"""
        issues = []
        
        # Ajouter à l'historique
        self.input_history.append({
            'text': new_input,
            'timestamp': time.time(),
            'length': len(new_input),
            'word_count': len(new_input.split())
        })
        
        # Garder seulement les derniers éléments
        if len(self.input_history) > self.max_history_size:
            self.input_history = self.input_history[-self.max_history_size:]
        
        # Analyser la dérive si on a assez d'historique
        if len(self.input_history) >= 10:
            drift_metrics = self._calculate_input_drift()
            
            if drift_metrics['drift_detected']:
                issue = QualityIssue(
                    type='input_drift',
                    severity=self.severity_levels['input_drift'],
                    description=f"Dérive d'entrée détectée: {drift_metrics['description']}",
                    confidence=drift_metrics['confidence'],
                    metrics=drift_metrics
                )
                issues.append(issue)
        
        return issues
    
    def detect_output_drift(self, new_output: str) -> List[QualityIssue]:
        """Détecte la dérive dans les réponses générées"""
        issues = []
        
        # Ajouter à l'historique
        self.output_history.append({
            'text': new_output,
            'timestamp': time.time(),
            'length': len(new_output),
            'word_count': len(new_output.split())
        })
        
        # Garder seulement les derniers éléments
        if len(self.output_history) > self.max_history_size:
            self.output_history = self.output_history[-self.max_history_size:]
        
        # Analyser la dérive si on a assez d'historique
        if len(self.output_history) >= 10:
            drift_metrics = self._calculate_output_drift()
            
            if drift_metrics['drift_detected']:
                issue = QualityIssue(
                    type='output_drift',
                    severity=self.severity_levels['output_drift'],
                    description=f"Dérive de sortie détectée: {drift_metrics['description']}",
                    confidence=drift_metrics['confidence'],
                    metrics=drift_metrics
                )
                issues.append(issue)
        
        return issues
    
    def _calculate_input_drift(self) -> Dict[str, Any]:
        """Calcule la dérive dans les données d'entrée"""
        if len(self.input_history) < 10:
            return {'drift_detected': False}
        
        # Analyser les métriques récentes vs anciennes
        recent = self.input_history[-10:]
        older = self.input_history[-20:-10] if len(self.input_history) >= 20 else self.input_history[:-10]
        
        # Calculer les moyennes
        recent_avg_length = np.mean([item['length'] for item in recent])
        older_avg_length = np.mean([item['length'] for item in older])
        
        recent_avg_words = np.mean([item['word_count'] for item in recent])
        older_avg_words = np.mean([item['word_count'] for item in older])
        
        # Détecter les changements significatifs
        length_change = abs(recent_avg_length - older_avg_length) / older_avg_length if older_avg_length > 0 else 0
        word_change = abs(recent_avg_words - older_avg_words) / older_avg_words if older_avg_words > 0 else 0
        
        drift_detected = length_change > 0.3 or word_change > 0.3
        
        return {
            'drift_detected': drift_detected,
            'description': f"Changement de {length_change:.2%} en longueur, {word_change:.2%} en mots",
            'confidence': min(0.9, length_change + word_change),
            'metrics': {
                'length_change': length_change,
                'word_change': word_change,
                'recent_avg_length': recent_avg_length,
                'older_avg_length': older_avg_length
            }
        }
    
    def _calculate_output_drift(self) -> Dict[str, Any]:
        """Calcule la dérive dans les réponses générées"""
        if len(self.output_history) < 10:
            return {'drift_detected': False}
        
        # Analyser les métriques récentes vs anciennes
        recent = self.output_history[-10:]
        older = self.output_history[-20:-10] if len(self.output_history) >= 20 else self.output_history[:-10]
        
        # Calculer les moyennes
        recent_avg_length = np.mean([item['length'] for item in recent])
        older_avg_length = np.mean([item['length'] for item in older])
        
        recent_avg_words = np.mean([item['word_count'] for item in recent])
        older_avg_words = np.mean([item['word_count'] for item in older])
        
        # Détecter les changements significatifs
        length_change = abs(recent_avg_length - older_avg_length) / older_avg_length if older_avg_length > 0 else 0
        word_change = abs(recent_avg_words - older_avg_words) / older_avg_words if older_avg_words > 0 else 0
        
        drift_detected = length_change > 0.3 or word_change > 0.3
        
        return {
            'drift_detected': drift_detected,
            'description': f"Changement de {length_change:.2%} en longueur, {word_change:.2%} en mots",
            'confidence': min(0.9, length_change + word_change),
            'metrics': {
                'length_change': length_change,
                'word_change': word_change,
                'recent_avg_length': recent_avg_length,
                'older_avg_length': older_avg_length
            }
        }
    
    def _calculate_confidence(self, match: str, issue_type: str) -> float:
        """Calcule la confiance de détection"""
        confidence_map = {
            'hallucination': 0.85,
            'bias': 0.80,
            'input_drift': 0.75,
            'output_drift': 0.75
        }
        return confidence_map.get(issue_type, 0.5)
    
    def analyze_quality(self, text: str, input_text: str = None) -> Dict[str, Any]:
        """Analyse complète de qualité d'un texte"""
        print("🔍 ANALYSE DE QUALITÉ")
        print("="*50)
        
        # Détecter toutes les violations
        hallucination_issues = self.detect_hallucination(text)
        bias_issues = self.detect_bias(text)
        
        # Détecter la dérive si on a un input
        input_drift_issues = []
        output_drift_issues = []
        
        if input_text:
            input_drift_issues = self.detect_input_drift(input_text)
            output_drift_issues = self.detect_output_drift(text)
        
        all_issues = hallucination_issues + bias_issues + input_drift_issues + output_drift_issues
        
        # Calculer le score de qualité
        quality_score = self._calculate_quality_score(all_issues)
        
        # Générer le rapport
        report = {
            'text': text,
            'input_text': input_text,
            'total_issues': len(all_issues),
            'hallucination_issues': len(hallucination_issues),
            'bias_issues': len(bias_issues),
            'input_drift_issues': len(input_drift_issues),
            'output_drift_issues': len(output_drift_issues),
            'quality_score': quality_score,
            'issues': [
                {
                    'type': i.type,
                    'severity': i.severity,
                    'description': i.description,
                    'confidence': i.confidence,
                    'metrics': i.metrics
                } for i in all_issues
            ]
        }
        
        # Afficher les résultats
        print(f"📊 Mesure Problèmes détectés: {len(all_issues)}")
        print(f"🛡️ Mesure Score de qualité: {quality_score}/100")
        print(f"🔴 Mesure Hallucinations: {len(hallucination_issues)}")
        print(f"🟡 Mesure Biais: {len(bias_issues)}")
        print(f"🟠 Mesure Dérive entrée: {len(input_drift_issues)}")
        print(f"🟠 Mesure Dérive sortie: {len(output_drift_issues)}")
        
        for issue in all_issues:
            print(f"  • {issue.type.upper()}: {issue.description}")
        
        return report
    
    def _calculate_quality_score(self, issues: List[QualityIssue]) -> int:
        """Calcule un score de qualité basé sur les problèmes"""
        if not issues:
            return 100
        
        # Pénalités par type de problème
        penalties = {
            'hallucination': 20,
            'bias_cultural': 15,
            'bias_gender': 15,
            'bias_social': 15,
            'bias_age': 15,
            'input_drift': 10,
            'output_drift': 15
        }
        
        total_penalty = sum(penalties.get(i.type, 10) for i in issues)
        return max(0, 100 - total_penalty)
    


class QualityAgent:
    """Agent de qualité principal avec toutes les fonctionnalités"""
    
    def __init__(self):
        self.quality_tools = QualityTools()
        self.api_key = os.getenv("XAI_API_KEY")
        
        # Créer l'agent avec les outils de qualité
        self.agent = Agent(
            name="Quality Assistant",
            model=xAI(id="grok-3-mini", api_key=self.api_key),
            tools=[self.quality_tools],
            markdown=True,
            show_tool_calls=True,
            instructions=dedent("""
            Tu es un agent de qualité spécialisé dans la détection des problèmes.
            Ton rôle est de :
            1. Détecter les hallucinations
            2. Détecter les biais
            3. Détecter la dérive d'entrée
            4. Détecter la dérive de sortie
            
            Toujours prioriser la qualité et la cohérence des données.
            """)
        )
    
    def analyze_text_quality(self, text: str, input_text: str = None) -> Dict[str, Any]:
        """Analyse la qualité d'un texte"""
        print("🔍 ANALYSE DE QUALITÉ DU TEXTE")
        print("="*50)
        
        # Utiliser les outils de qualité
        report = self.quality_tools.analyze_quality(text, input_text)
        
        return report
    

# Exemple d'utilisation
if __name__ == "__main__":
    # Créer l'agent de qualité
    quality_agent = QualityAgent()
    
    print("🛡️ AGENT DE QUALITÉ - 4 MESURES PRINCIPALES")
    print("="*60)
    
    # Test 1: Détection d'hallucinations
    print("\n📋 MESURE 1: HALLUCINATION DETECTION")
    print("-" * 40)
    hallucination_text = """
    According to my knowledge, this is probably the best solution.
    I believe that it seems like the right approach.
    As far as I know, this is likely to work.
    It appears that this might be correct.
    From what I understand, this is possibly true.
    """
    hallucination_report = quality_agent.analyze_text_quality(hallucination_text)
    print(f"Mesure Hallucinations détectées: {hallucination_report['hallucination_issues']}")
    print(f"Mesure Score de qualité: {hallucination_report['quality_score']}/100")
    
    # Test 2: Détection de biais
    print("\n📋 MESURE 2: BIAS DETECTION")
    print("-" * 40)
    bias_text = """
    Women are more emotional than men and should stay at home.
    Men should be strong and not cry like babies.
    Old people are slow and outdated in their thinking.
    Young people are lazy and don't work hard.
    Rich people are always greedy and selfish.
    """
    bias_report = quality_agent.analyze_text_quality(bias_text)
    print(f"Mesure Biais détectés: {bias_report['bias_issues']}")
    print(f"Mesure Score de qualité: {bias_report['quality_score']}/100")
    
    # Test 3: Détection de dérive d'entrée
    print("\n📋 MESURE 3: INPUT DRIFT DETECTION")
    print("-" * 40)
    input_drift_text = """
    This is a completely new type of request that we've never seen before.
    It's innovative and revolutionary in its approach.
    This is unprecedented and never been done.
    It's a novel approach that's completely different.
    This is a first-time request that's unusual.
    """
    input_drift_report = quality_agent.analyze_text_quality(input_drift_text, input_drift_text)
    print(f"Mesure Dérive d'entrée détectée: {input_drift_report['input_drift_issues']}")
    print(f"Mesure Score de qualité: {input_drift_report['quality_score']}/100")
    
    # Test 4: Détection de dérive de sortie
    print("\n📋 MESURE 4: OUTPUT DRIFT DETECTION")
    print("-" * 40)
    output_drift_text = """
    This response seems different from our usual outputs.
    It's not typical and deviates from our standard.
    This is unexpected and unusual for our system.
    The response varies from our normal pattern.
    This departs from our usual way of answering.
    """
    output_drift_report = quality_agent.analyze_text_quality(output_drift_text, "test input")
    print(f"Mesure Dérive de sortie détectée: {output_drift_report['output_drift_issues']}")
    print(f"Mesure Score de qualité: {output_drift_report['quality_score']}/100")
    
    # Test 5: Test combiné avec toutes les violations
    print("\n📋 MESURE 5: TEST COMBINÉ - TOUTES LES VIOLATIONS")
    print("-" * 40)
    combined_text = """
    According to my knowledge, women are more emotional than men.
    This is a completely new type of request that's unprecedented.
    The response seems different from our usual outputs.
    I believe this is probably the best solution for old people.
    """
    combined_report = quality_agent.analyze_text_quality(combined_text, combined_text)
    print(f"Mesure Total problèmes: {combined_report['total_issues']}")
    print(f"Mesure Hallucinations: {combined_report['hallucination_issues']}")
    print(f"Mesure Biais: {combined_report['bias_issues']}")
    print(f"Mesure Dérive entrée: {combined_report['input_drift_issues']}")
    print(f"Mesure Dérive sortie: {combined_report['output_drift_issues']}")
    print(f"Mesure Score de qualité: {combined_report['quality_score']}/100")
    
    print("\n✅ Tests de qualité terminés!")
    print("="*60)
