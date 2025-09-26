import os
import re
import sys
import hashlib
import secrets
import subprocess
import tempfile
import json
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from textwrap import dedent
from dotenv import load_dotenv
from agno.agent import Agent, RunResponse
from agno.models.xai import xAI
# from agno.tools.googlesearch import GoogleSearchTools  # Non utilisé pour les 4 mesures principales
# from rich.pretty import pprint  # Non utilisé pour les 4 mesures principales

load_dotenv()

# def get_date_time():  # Non utilisé pour les 4 mesures principales
#     """Fonction personnalisée pour obtenir la date et l'heure"""
#     from datetime import datetime
#     return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@dataclass
class PIIDetection:
    """Structure pour stocker les informations PII détectées"""
    type: str
    value: str
    position: int
    confidence: float
    masked_value: str

class SecurityTools:
    """Outils de sécurité pour la détection et le masquage PII"""
    
    def __init__(self):
        # Patterns de détection PII
        self.pii_patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
            'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
            'address': r'\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr)\b',
            'name': r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b'
        }
        
        # Stockage sécurisé des tokens
        self.secure_token_store = {}
        
    def detect_pii(self, text: str) -> List[PIIDetection]:
        """Détecte les informations personnelles identifiables dans un texte"""
        detections = []
        
        for pii_type, pattern in self.pii_patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                detection = PIIDetection(
                    type=pii_type,
                    value=match.group(),
                    position=match.start(),
                    confidence=self._calculate_confidence(match.group(), pii_type),
                    masked_value=self._mask_value(match.group(), pii_type)
                )
                detections.append(detection)
        
        return detections
    
    def _calculate_confidence(self, value: str, pii_type: str) -> float:
        """Calcule la confiance de détection PII"""
        confidence_map = {
            'email': 0.95,
            'phone': 0.90,
            'ssn': 0.98,
            'credit_card': 0.85,
            'address': 0.75,
            'name': 0.60
        }
        return confidence_map.get(pii_type, 0.5)
    
    def _mask_value(self, value: str, pii_type: str) -> str:
        """Masque une valeur PII selon son type"""
        if pii_type == 'email':
            parts = value.split('@')
            return f"{parts[0][:2]}***@{parts[1]}"
        elif pii_type == 'phone':
            return f"***-***-{value[-4:]}"
        elif pii_type == 'ssn':
            return f"***-**-{value[-4:]}"
        elif pii_type == 'credit_card':
            return f"****-****-****-{value[-4:]}"
        elif pii_type == 'address':
            return f"*** {value.split()[-1]}"
        elif pii_type == 'name':
            parts = value.split()
            return f"{parts[0][0]}*** {parts[1][0]}***"
        else:
            return "***"
    
    def mask_text(self, text: str) -> Tuple[str, List[PIIDetection]]:
        """Masque toutes les informations PII dans un texte"""
        detections = self.detect_pii(text)
        masked_text = text
        
        # Trier par position décroissante pour éviter les décalages
        for detection in sorted(detections, key=lambda x: x.position, reverse=True):
            masked_text = masked_text[:detection.position] + detection.masked_value + masked_text[detection.position + len(detection.value):]
        
        return masked_text, detections
    
    def store_secure_token(self, token_name: str, token_value: str) -> str:
        """Stocke un token de manière sécurisée avec un ID de référence"""
        token_id = secrets.token_urlsafe(32)
        hashed_token = hashlib.sha256(token_value.encode()).hexdigest()
        
        self.secure_token_store[token_id] = {
            'hashed_value': hashed_token,
            'name': token_name,
            'created_at': time.time()
        }
        
        return token_id
    
    def get_secure_token(self, token_id: str) -> Optional[str]:
        """Récupère un token sécurisé par son ID"""
        if token_id in self.secure_token_store:
            return self.secure_token_store[token_id]['hashed_value']
        return None
    
    def validate_token(self, token_id: str, provided_token: str) -> bool:
        """Valide un token fourni contre le token stocké"""
        stored_token = self.get_secure_token(token_id)
        if stored_token:
            hashed_provided = hashlib.sha256(provided_token.encode()).hexdigest()
            return stored_token == hashed_provided
        return False

class IsolatedExecutionEnvironment:
    """Environnement d'exécution isolé pour limiter l'accès aux ressources"""
    
    def __init__(self):
        self.temp_dir = None
        self.process = None
        
    def create_isolated_env(self) -> str:
        """Crée un environnement d'exécution isolé"""
        self.temp_dir = tempfile.mkdtemp(prefix="secure_agent_")
        
        # Créer un environnement Python virtuel isolé
        venv_path = os.path.join(self.temp_dir, "venv")
        subprocess.run([sys.executable, "-m", "venv", venv_path], check=True)
        
        return self.temp_dir
    
    def execute_in_isolation(self, code: str, timeout: int = 30) -> Dict[str, Any]:
        """Exécute du code dans un environnement isolé"""
        if not self.temp_dir:
            self.create_isolated_env()
        
        # Créer un fichier temporaire avec le code
        code_file = os.path.join(self.temp_dir, "secure_code.py")
        with open(code_file, 'w') as f:
            f.write(code)
        
        # Exécuter dans l'environnement isolé
        try:
            result = subprocess.run(
                [os.path.join(self.temp_dir, "venv", "Scripts", "python"), code_file],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.temp_dir
            )
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'stdout': '',
                'stderr': 'Timeout expired',
                'returncode': -1
            }
    
    def cleanup(self):
        """Nettoie l'environnement isolé"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)
            self.temp_dir = None

class SecureAgent:
    """Agent de sécurité principal avec toutes les fonctionnalités"""
    
    def __init__(self):
        self.security_tools = SecurityTools()
        self.isolated_env = IsolatedExecutionEnvironment()
        self.api_key = os.getenv("XAI_API_KEY")
        
        # Créer l'agent avec les outils de sécurité 
        self.agent = Agent(
            name="Security Assistant",
            model=xAI(id="grok-3-mini", api_key=self.api_key),
            tools=[self.security_tools],
            markdown=True,
            show_tool_calls=True,
            instructions=dedent("""
            Tu es un agent de sécurité spécialisé dans la protection des données.
            Ton rôle est de :
            1. Détecter les informations personnelles identifiables (PII)
            2. Masquer ou anonymiser les données sensibles
            3. Exécuter du code dans des environnements isolés
            4. Gérer les tokens d'authentification de manière sécurisée
            
            Toujours prioriser la sécurité et la confidentialité des données.
            """)
        )
    
    def analyze_text_security(self, text: str) -> Dict[str, Any]:
        """Analyse la sécurité d'un texte et détecte les PII"""
        print("🔍 ANALYSE DE SÉCURITÉ DU TEXTE")
        print("="*50)
        
        # Détecter les PII
        detections = self.security_tools.detect_pii(text)
        
        # Masquer le texte
        masked_text, masked_detections = self.security_tools.mask_text(text)
        
        # Créer le rapport
        report = {
            'original_text': text,
            'masked_text': masked_text,
            'pii_detected': len(detections),
            'detections': [
                {
                    'type': d.type,
                    'value': d.value,
                    'position': d.position,
                    'confidence': d.confidence,
                    'masked_value': d.masked_value
                } for d in detections
            ],
            'security_score': self._calculate_security_score(detections)
        }
        
        # Afficher les résultats avec noms des mesures
        print(f"📊 Mesure PII Détectées: {len(detections)}")
        print(f"🛡️ Mesure Score de sécurité: {report['security_score']}/100")
        
        for detection in detections:
            print(f"  • Mesure {detection.type.upper()}: {detection.value} → {detection.masked_value}")
        
        print(f"\n📝 Mesure Texte masqué:")
        print(f"   {masked_text}")
        
        return report
    
    def _calculate_security_score(self, detections: List[PIIDetection]) -> int:
        """Calcule un score de sécurité basé sur les détections PII"""
        if not detections:
            return 100
        
        # Pénalités par type de PII
        penalties = {
            'ssn': 30,
            'credit_card': 25,
            'email': 15,
            'phone': 10,
            'address': 20,
            'name': 5
        }
        
        total_penalty = sum(penalties.get(d.type, 10) for d in detections)
        return max(0, 100 - total_penalty)
    
    
    def secure_code_execution(self, code: str) -> Dict[str, Any]:
        """Exécute du code de manière sécurisée dans un environnement isolé"""
        print("🔒 EXÉCUTION SÉCURISÉE DU CODE")
        print("="*40)
        
        # Analyser le code pour les PII
        code_analysis = self.analyze_text_security(code)
        
        if code_analysis['pii_detected'] > 0:
            print("⚠️ ATTENTION: PII détectée dans le code!")
            return {
                'success': False,
                'error': 'Code contient des informations sensibles',
                'pii_detected': code_analysis['pii_detected']
            }
        
        # Exécuter dans l'environnement isolé
        result = self.isolated_env.execute_in_isolation(code)
        
        print(f"✅ Mesure Exécution terminée: {result['success']}")
        if result['stdout']:
            print(f"📤 Mesure Sortie: {result['stdout']}")
        if result['stderr']:
            print(f"❌ Mesure Erreurs: {result['stderr']}")
        
        return result
    
    def manage_secure_tokens(self, action: str, token_name: str = None, token_value: str = None, token_id: str = None) -> Dict[str, Any]:
        """Gère les tokens d'authentification de manière sécurisée"""
        print("🔐 GESTION SÉCURISÉE DES TOKENS")
        print("="*40)
        
        if action == "store":
            if not token_name or not token_value:
                return {'success': False, 'error': 'Nom et valeur du token requis'}
            
            token_id = self.security_tools.store_secure_token(token_name, token_value)
            print(f"✅ Mesure Token '{token_name}' stocké avec ID: {token_id}")
            return {'success': True, 'token_id': token_id}
        
        elif action == "validate":
            if not token_id or not token_value:
                return {'success': False, 'error': 'ID et valeur du token requis'}
            
            is_valid = self.security_tools.validate_token(token_id, token_value)
            print(f"🔍 Mesure Validation: {'✅ Valide' if is_valid else '❌ Invalide'}")
            return {'success': is_valid}
        
        elif action == "list":
            tokens = list(self.security_tools.secure_token_store.keys())
            print(f"📋 Mesure Tokens stockés: {len(tokens)}")
            return {'success': True, 'tokens': tokens}
        
        return {'success': False, 'error': 'Action non reconnue'}
    
    
    def cleanup(self):
        """Nettoie les ressources"""
        self.isolated_env.cleanup()

# Exemple d'utilisation
if __name__ == "__main__":
    # Créer l'agent de sécurité
    security_agent = SecureAgent()
    
    print("🛡️ AGENT DE SÉCURITÉ - 4 MESURES PRINCIPALES")
    print("="*60)
    
    test_text = """
    Bonjour, je suis Jean Dupont et mon email est jean.dupont@email.com.
    Mon numéro de téléphone est +1-555-123-4567.
    Mon SSN est 123-45-6789.
    Ma carte de crédit est 4532-1234-5678-9012.
    J'habite au 123 Main Street, New York.
    """
    
    # MESURE 1: PII Detection
    print("\n📋 MESURE 1: PII DETECTION")
    print("-" * 40)
    
    security_report = security_agent.analyze_text_security(test_text)
    print(f"Mesure PII détectées: {security_report['pii_detected']}")
    print(f"Mesure Score de sécurité: {security_report['security_score']}/100")
    
    # MESURE 2: PII Masking
    print("\n📋 MESURE 2: PII MASKING")
    print("-" * 40)
    
    masked_text = security_report['masked_text']
    print(f"Mesure Texte original: {test_text.strip()}")
    print(f"Mesure Texte masqué: {masked_text}")
    
    # MESURE 3: Separate Execution Environment
    print("\n📋 MESURE 3: SEPARATE EXECUTION ENVIRONMENT")
    print("-" * 40)
    
    safe_code = """
import os
print("Code sécurisé exécuté dans un environnement isolé")
print(f"Répertoire de travail: {os.getcwd()}")
"""
    
    execution_result = security_agent.secure_code_execution(safe_code)
    print(f"Mesure Exécution isolée: {'✅ Réussie' if execution_result['success'] else '❌ Échouée'}")
    
    # MESURE 4: Isolation of Authentication Information
    print("\n📋 MESURE 4: ISOLATION OF AUTHENTICATION INFORMATION")
    print("-" * 40)
    
    token_result = security_agent.manage_secure_tokens(
        action="store",
        token_name="API_KEY",
        token_value="secret_api_key_123"
    )
    
    if token_result['success']:
        token_id = token_result['token_id']
        print(f"Mesure Token stocké avec ID: {token_id}")
        print(f"Mesure Valeur originale: secret_api_key_123")
        print(f"Mesure Valeur stockée: [HACHÉE ET SÉCURISÉE]")
        
        # Valider le token
        validation_result = security_agent.manage_secure_tokens(
            action="validate",
            token_id=token_id,
            token_value="secret_api_key_123"
        )
        print(f"Mesure Validation: {'✅ Valide' if validation_result['success'] else '❌ Invalide'}")
    
    # Nettoyage
    security_agent.cleanup()
    
