import os
import re
import sys
import time
from typing import Dict, List, Any
from dataclasses import dataclass
from textwrap import dedent
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.xai import xAI

load_dotenv()

@dataclass
class GovernancePolicy:
    """Structure pour stocker les politiques de gouvernance"""
    id: str
    name: str
    category: str
    description: str
    rules: List[str]
    boundaries: List[str]
    enforcement_level: str
    created_at: float
    updated_at: float

@dataclass
class AgentPurpose:
    """Structure pour définir le but et les cas d'usage de l'agent"""
    agent_id: str
    name: str
    primary_purpose: str
    authorized_use_cases: List[str]
    prohibited_use_cases: List[str]
    capabilities: List[str]
    limitations: List[str]
    boundaries: List[str]
    created_at: float

class GovernanceTools:
    """Outils de gouvernance pour les 2 mesures principales"""
    
    def __init__(self):
        # Politiques de gouvernance par défaut
        self.policies = {}
        self.agent_purposes = {}
        self.enforcement_log = []
        
        # Comportements par défaut
        self.default_behaviors = {
            'response_style': 'professional',
            'safety_level': 'high',
            'transparency': 'full',
            'accountability': 'enabled',
            'audit_trail': 'enabled'
        }
        
        # Limites d'action par défaut
        self.default_boundaries = {
            'max_response_length': 5000,
            'max_processing_time': 30,
            'max_api_calls': 10,
            'max_file_size': 10,  # MB
            'allowed_domains': ['*'],
            'prohibited_content': ['illegal', 'harmful', 'discriminatory']
        }
        
        # Initialiser les politiques par défaut
        self._initialize_default_policies()
    
    def _initialize_default_policies(self):
        """Initialise les politiques de gouvernance par défaut"""
        
        # Politique de sécurité
        security_policy = GovernancePolicy(
            id="security_001",
            name="Politique de Sécurité",
            category="security",
            description="Politique de sécurité pour la protection des données et des utilisateurs",
            rules=[
                "Ne jamais exposer d'informations sensibles",
                "Toujours valider les entrées utilisateur",
                "Utiliser des connexions sécurisées uniquement",
                "Chiffrer les données sensibles en transit et au repos"
            ],
            boundaries=[
                "Accès limité aux données autorisées uniquement",
                "Aucun accès aux systèmes de production sans autorisation",
                "Audit obligatoire de toutes les actions sensibles"
            ],
            enforcement_level="critical",
            created_at=time.time(),
            updated_at=time.time()
        )
        
        # Politique de conformité
        compliance_policy = GovernancePolicy(
            id="compliance_001",
            name="Politique de Conformité",
            category="compliance",
            description="Politique de conformité pour respecter les réglementations",
            rules=[
                "Respecter le RGPD pour les données personnelles",
                "Respecter les lois locales et internationales",
                "Maintenir la traçabilité des actions",
                "Signaler les violations de conformité"
            ],
            boundaries=[
                "Aucune utilisation de données sans consentement",
                "Respect des délais de rétention des données",
                "Notification obligatoire des violations"
            ],
            enforcement_level="high",
            created_at=time.time(),
            updated_at=time.time()
        )
        
        # Politique de qualité
        quality_policy = GovernancePolicy(
            id="quality_001",
            name="Politique de Qualité",
            category="quality",
            description="Politique de qualité pour maintenir l'excellence des services",
            rules=[
                "Fournir des réponses précises et vérifiées",
                "Admettre les limitations et incertitudes",
                "Citer les sources quand approprié",
                "Maintenir un niveau de service constant"
            ],
            boundaries=[
                "Ne jamais inventer d'informations",
                "Limiter les réponses aux domaines d'expertise",
                "Escalader les questions complexes"
            ],
            enforcement_level="medium",
            created_at=time.time(),
            updated_at=time.time()
        )
        
        self.policies = {
            security_policy.id: security_policy,
            compliance_policy.id: compliance_policy,
            quality_policy.id: quality_policy
        }
    
    def define_agent_purpose(self, agent_id: str, name: str, primary_purpose: str, 
                           authorized_use_cases: List[str], prohibited_use_cases: List[str] = None,
                           capabilities: List[str] = None, limitations: List[str] = None) -> AgentPurpose:
        """Définit le but et les cas d'usage d'un agent"""
        
        purpose = AgentPurpose(
            agent_id=agent_id,
            name=name,
            primary_purpose=primary_purpose,
            authorized_use_cases=authorized_use_cases,
            prohibited_use_cases=prohibited_use_cases or [],
            capabilities=capabilities or [],
            limitations=limitations or [],
            boundaries=self.default_boundaries.copy(),
            created_at=time.time()
        )
        
        self.agent_purposes[agent_id] = purpose
        
        print(f"🎯 Mesure But de l'agent défini: {name}")
        print(f"📋 Mesure Cas d'usage autorisés: {len(authorized_use_cases)}")
        print(f"🚫 Mesure Cas d'usage interdits: {len(prohibited_use_cases or [])}")
        
        return purpose
    
    def set_default_behavior(self, behavior_type: str, value: Any) -> None:
        """Définit un comportement par défaut"""
        if behavior_type in self.default_behaviors:
            self.default_behaviors[behavior_type] = value
            print(f"⚙️ Mesure Comportement par défaut mis à jour: {behavior_type} = {value}")
        else:
            print(f"❌ Mesure Type de comportement non reconnu: {behavior_type}")
    
    def set_boundary(self, boundary_type: str, value: Any) -> None:
        """Définit une limite d'action"""
        if boundary_type in self.default_boundaries:
            self.default_boundaries[boundary_type] = value
            print(f"🔒 Mesure Limite mise à jour: {boundary_type} = {value}")
        else:
            print(f"❌ Mesure Type de limite non reconnu: {boundary_type}")
    
    def add_policy(self, policy: GovernancePolicy) -> None:
        """Ajoute une nouvelle politique de gouvernance"""
        self.policies[policy.id] = policy
        print(f"📜 Mesure Politique ajoutée: {policy.name}")
    
    def update_policy(self, policy_id: str, updates: Dict[str, Any]) -> None:
        """Met à jour une politique existante"""
        if policy_id in self.policies:
            policy = self.policies[policy_id]
            for key, value in updates.items():
                if hasattr(policy, key):
                    setattr(policy, key, value)
            policy.updated_at = time.time()
            print(f"📝 Mesure Politique mise à jour: {policy.name}")
        else:
            print(f"❌ Mesure Politique non trouvée: {policy_id}")
    
    def check_authorization(self, agent_id: str, action: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Vérifie si une action est autorisée pour un agent"""
        if agent_id not in self.agent_purposes:
            return {
                'authorized': False,
                'reason': 'Agent non enregistré',
                'recommendation': 'Enregistrer l\'agent avec define_agent_purpose'
            }
        
        purpose = self.agent_purposes[agent_id]
        context = context or {}
        
        # Vérifier les cas d'usage interdits
        for prohibited in purpose.prohibited_use_cases:
            if prohibited.lower() in action.lower():
                self._log_enforcement(agent_id, action, False, f"Cas d'usage interdit: {prohibited}")
                return {
                    'authorized': False,
                    'reason': f'Cas d\'usage interdit: {prohibited}',
                    'recommendation': 'Utiliser un cas d\'usage autorisé'
                }
        
        # Vérifier les limites
        if 'max_response_length' in self.default_boundaries:
            if len(action) > self.default_boundaries['max_response_length']:
                self._log_enforcement(agent_id, action, False, "Dépassement de la limite de longueur")
                return {
                    'authorized': False,
                    'reason': 'Dépassement de la limite de longueur de réponse',
                    'recommendation': 'Réduire la longueur de la requête'
                }
        
        # Vérifier les politiques applicables
        for policy in self.policies.values():
            if self._check_policy_violation(policy, action, context):
                self._log_enforcement(agent_id, action, False, f"Violation de politique: {policy.name}")
                return {
                    'authorized': False,
                    'reason': f'Violation de la politique: {policy.name}',
                    'recommendation': 'Respecter les règles de la politique'
                }
        
        # Action autorisée
        self._log_enforcement(agent_id, action, True, "Action autorisée")
        return {
            'authorized': True,
            'reason': 'Action conforme aux politiques',
            'recommendation': 'Continuer l\'exécution'
        }
    
    def _check_policy_violation(self, policy: GovernancePolicy, action: str, context: Dict[str, Any]) -> bool:
        """Vérifie si une action viole une politique"""
        # Vérifier les règles de la politique
        for rule in policy.rules:
            if self._check_rule_violation(rule, action, context):
                return True
        
        # Vérifier les limites de la politique
        for boundary in policy.boundaries:
            if self._check_boundary_violation(boundary, action, context):
                return True
        
        return False
    
    def _check_rule_violation(self, rule: str, action: str, context: Dict[str, Any]) -> bool:
        """Vérifie si une règle est violée"""
        # Logique simple de vérification - peut être étendue
        rule_lower = rule.lower()
        action_lower = action.lower()
        
        if "ne jamais" in rule_lower and "exposer" in rule_lower:
            return "password" in action_lower or "secret" in action_lower
        
        if "toujours valider" in rule_lower:
            return not self._is_valid_input(action)
        
        return False
    
    def _check_boundary_violation(self, boundary: str, action: str, context: Dict[str, Any]) -> bool:
        """Vérifie si une limite est violée"""
        boundary_lower = boundary.lower()
        action_lower = action.lower()
        
        if "accès limité" in boundary_lower:
            return "admin" in action_lower or "root" in action_lower
        
        if "aucun accès" in boundary_lower:
            return "production" in action_lower or "système" in action_lower
        
        return False
    
    def _is_valid_input(self, input_text: str) -> bool:
        """Valide une entrée utilisateur"""
        # Logique de validation simple - peut être étendue
        if not input_text or len(input_text.strip()) == 0:
            return False
        
        if len(input_text) > 10000:  # Limite de longueur
            return False
        
        return True
    
    def _log_enforcement(self, agent_id: str, action: str, authorized: bool, reason: str):
        """Enregistre une action d'application des politiques"""
        log_entry = {
            'timestamp': time.time(),
            'agent_id': agent_id,
            'action': action,
            'authorized': authorized,
            'reason': reason
        }
        self.enforcement_log.append(log_entry)
        
        # Garder seulement les 1000 dernières entrées
        if len(self.enforcement_log) > 1000:
            self.enforcement_log = self.enforcement_log[-1000:]
    
    def get_governance_report(self) -> Dict[str, Any]:
        """Génère un rapport de gouvernance complet"""
        total_policies = len(self.policies)
        total_agents = len(self.agent_purposes)
        total_enforcements = len(self.enforcement_log)
        
        authorized_actions = sum(1 for log in self.enforcement_log if log['authorized'])
        denied_actions = total_enforcements - authorized_actions
        
        report = {
            'total_policies': total_policies,
            'total_agents': total_agents,
            'total_enforcements': total_enforcements,
            'authorized_actions': authorized_actions,
            'denied_actions': denied_actions,
            'compliance_rate': authorized_actions / total_enforcements if total_enforcements > 0 else 1.0,
            'default_behaviors': self.default_behaviors,
            'default_boundaries': self.default_boundaries,
            'policies': list(self.policies.values()),
            'agent_purposes': list(self.agent_purposes.values()),
            'recent_enforcements': self.enforcement_log[-10:]  # 10 dernières actions
        }
        
        return report


class GovernanceAgent:
    """Agent de gouvernance pour les 2 mesures principales"""
    
    def __init__(self):
        self.governance_tools = GovernanceTools()
        self.api_key = os.getenv("XAI_API_KEY")
        
        # Créer l'agent avec les outils de gouvernance
        self.agent = Agent(
            name="Governance Assistant",
            model=xAI(id="grok-3-mini", api_key=self.api_key),
            tools=[self.governance_tools],
            markdown=True,
            show_tool_calls=True,
            instructions=dedent("""
            Tu es un agent de gouvernance spécialisé dans la définition et l'application des politiques.
            Ton rôle est de :
            1. Définir les comportements par défaut et les limites d'action
            2. Définir clairement le but et les cas d'usage autorisés des agents
            
            Toujours prioriser la conformité et l'application des politiques.
            """)
        )
    
    def define_agent_purpose(self, agent_id: str, name: str, primary_purpose: str, 
                           authorized_use_cases: List[str], **kwargs) -> AgentPurpose:
        """Définit le but et les cas d'usage d'un agent"""
        return self.governance_tools.define_agent_purpose(
            agent_id, name, primary_purpose, authorized_use_cases, **kwargs
        )
    
    def set_default_behavior(self, behavior_type: str, value: Any) -> None:
        """Définit un comportement par défaut"""
        self.governance_tools.set_default_behavior(behavior_type, value)
    
    def set_boundary(self, boundary_type: str, value: Any) -> None:
        """Définit une limite d'action"""
        self.governance_tools.set_boundary(boundary_type, value)
    
    def check_authorization(self, agent_id: str, action: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Vérifie si une action est autorisée pour un agent"""
        return self.governance_tools.check_authorization(agent_id, action, context)
    
    def get_governance_report(self) -> Dict[str, Any]:
        """Obtient le rapport de gouvernance complet"""
        print("📊 RAPPORT DE GOUVERNANCE")
        print("="*50)
        
        report = self.governance_tools.get_governance_report()
        
        print(f"📜 Mesure Politiques totales: {report['total_policies']}")
        print(f"🤖 Mesure Agents enregistrés: {report['total_agents']}")
        print(f"🔍 Mesure Actions vérifiées: {report['total_enforcements']}")
        print(f"✅ Mesure Actions autorisées: {report['authorized_actions']}")
        print(f"❌ Mesure Actions refusées: {report['denied_actions']}")
        print(f"📈 Mesure Taux de conformité: {report['compliance_rate']:.2%}")
        
        return report

# Exemple d'utilisation
if __name__ == "__main__":
    # Créer l'agent de gouvernance
    governance_agent = GovernanceAgent()
    
    print("🛡️ AGENT DE GOUVERNANCE - 2 MESURES PRINCIPALES")
    print("="*60)
    
    # Test 1: Définir le but et les cas d'usage autorisés des agents
    print("\n📋 MESURE 1: INTENDED AGENT PURPOSE")
    print("-" * 40)
    purpose = governance_agent.define_agent_purpose(
        agent_id="security_agent_001",
        name="Agent de Sécurité",
        primary_purpose="Protection des données et détection des menaces",
        authorized_use_cases=[
            "Détection de PII",
            "Analyse de sécurité",
            "Audit de conformité",
            "Gestion des incidents"
        ],
        prohibited_use_cases=[
            "Accès non autorisé aux données",
            "Modification des configurations de sécurité",
            "Bypass des contrôles de sécurité"
        ],
        capabilities=[
            "Détection de menaces",
            "Analyse de logs",
            "Génération de rapports"
        ],
        limitations=[
            "Accès en lecture seule",
            "Pas de modification des systèmes",
            "Audit obligatoire des actions"
        ]
    )
    print(f"Mesure But de l'agent défini: {purpose.name}")
    print(f"Mesure Cas d'usage autorisés: {len(purpose.authorized_use_cases)}")
    print(f"Mesure Cas d'usage interdits: {len(purpose.prohibited_use_cases)}")
    
    # Test 2: Définir les comportements par défaut et les limites d'action
    print("\n📋 MESURE 2: DEFAULT BEHAVIOR AND BOUNDARIES")
    print("-" * 40)
    governance_agent.set_default_behavior("response_style", "formal")
    governance_agent.set_default_behavior("safety_level", "maximum")
    governance_agent.set_boundary("max_response_length", 3000)
    governance_agent.set_boundary("max_processing_time", 20)
    print("Mesure Comportements par défaut configurés")
    print("Mesure Limites d'action définies")
    
    # Test 3: Vérification d'autorisation
    print("\n📋 MESURE 3: AUTHORIZATION CHECK")
    print("-" * 40)
    auth_result = governance_agent.check_authorization(
        "security_agent_001",
        "Analyser les logs de sécurité pour détecter les intrusions",
        {"user_role": "security_analyst"}
    )
    print(f"Mesure Autorisation: {'✅ Autorisé' if auth_result['authorized'] else '❌ Refusé'}")
    print(f"Mesure Raison: {auth_result['reason']}")
    
    # Test 4: Rapport de gouvernance
    print("\n📋 MESURE 4: GOVERNANCE REPORT")
    print("-" * 40)
    governance_report = governance_agent.get_governance_report()
    
    print("\n✅ Tests de gouvernance terminés!")
    print("="*60)
