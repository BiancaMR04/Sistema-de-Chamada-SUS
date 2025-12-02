"""
e-SUS API integration service.
"""
import requests
from typing import Optional
from datetime import datetime
from flask import current_app

from app import db
from app.models import Patient, PriorityType


class ESUSService:
    """Service for e-SUS API integration."""
    
    @staticmethod
    def _get_api_url() -> str:
        """Get e-SUS API URL from config."""
        return current_app.config.get('ESUS_API_URL', 'https://api.esus.gov.br')
    
    @staticmethod
    def _get_api_key() -> str:
        """Get e-SUS API key from config."""
        return current_app.config.get('ESUS_API_KEY', '')
    
    @staticmethod
    def _get_timeout() -> int:
        """Get API timeout from config (max 3 seconds as per requirements)."""
        return min(current_app.config.get('ESUS_API_TIMEOUT', 3), 3)
    
    @staticmethod
    def search_patient(cpf: Optional[str] = None, cns: Optional[str] = None) -> Optional[dict]:
        """
        Search for a patient in the e-SUS system.
        
        Args:
            cpf: Patient's CPF (Brazilian ID number)
            cns: Patient's CNS (SUS Card number)
            
        Returns:
            Patient data dict or None if not found
        """
        api_url = ESUSService._get_api_url()
        api_key = ESUSService._get_api_key()
        timeout = ESUSService._get_timeout()
        
        if not api_key:
            # Offline mode - return None to trigger manual registration
            return None
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        params = {}
        if cpf:
            params['cpf'] = cpf
        if cns:
            params['cns'] = cns
        
        if not params:
            return None
        
        try:
            response = requests.get(
                f"{api_url}/pacientes/buscar",
                headers=headers,
                params=params,
                timeout=timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                return data
            elif response.status_code == 404:
                return None
            else:
                current_app.logger.error(f"e-SUS API error: {response.status_code}")
                return None
                
        except requests.Timeout:
            current_app.logger.warning("e-SUS API timeout - switching to offline mode")
            return None
        except requests.RequestException as e:
            current_app.logger.error(f"e-SUS API error: {str(e)}")
            return None
    
    @staticmethod
    def sync_patient(esus_data: dict) -> Patient:
        """
        Sync patient data from e-SUS to local database.
        
        Args:
            esus_data: Patient data from e-SUS API
            
        Returns:
            Patient model instance
        """
        esus_id = esus_data.get('id')
        cpf = esus_data.get('cpf')
        
        # Check if patient already exists
        patient = None
        if esus_id:
            patient = Patient.query.filter_by(esus_id=esus_id).first()
        if not patient and cpf:
            patient = Patient.query.filter_by(cpf=cpf).first()
        
        if not patient:
            patient = Patient()
            db.session.add(patient)
        
        # Update patient data
        patient.esus_id = esus_id
        patient.name = esus_data.get('nome', 'Desconhecido')
        patient.cpf = cpf
        
        # Parse birth date
        birth_date_str = esus_data.get('dataNascimento')
        if birth_date_str:
            try:
                patient.birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        # Calculate priority based on age
        if patient.birth_date:
            today = datetime.now().date()
            age = (today - patient.birth_date).days // 365
            
            if age >= 80:
                patient.priority_type = PriorityType.IDOSO_80.value
            elif age >= 60:
                patient.priority_type = PriorityType.IDOSO_60.value
        
        # Check for other priorities from e-SUS data
        priority_flags = esus_data.get('prioridades', {})
        if priority_flags.get('gestante'):
            patient.priority_type = PriorityType.GESTANTE.value
        elif priority_flags.get('deficiente'):
            patient.priority_type = PriorityType.DEFICIENTE.value
        elif priority_flags.get('autista'):
            patient.priority_type = PriorityType.AUTISTA.value
        
        patient.is_offline = False
        db.session.commit()
        
        return patient
    
    @staticmethod
    def get_or_create_offline_patient(name: str, cpf: Optional[str] = None, 
                                       priority_type: str = PriorityType.NORMAL.value,
                                       birth_date: Optional[str] = None) -> Patient:
        """
        Create or get a patient for offline/manual registration.
        
        Args:
            name: Patient's full name
            cpf: Patient's CPF (optional)
            priority_type: Priority type
            birth_date: Birth date as string (YYYY-MM-DD)
            
        Returns:
            Patient model instance
        """
        # Try to find existing patient by CPF
        patient = None
        if cpf:
            patient = Patient.query.filter_by(cpf=cpf).first()
        
        if not patient:
            patient = Patient()
            patient.cpf = cpf
            db.session.add(patient)
        
        patient.name = name
        patient.priority_type = priority_type
        patient.is_offline = True
        
        if birth_date:
            try:
                patient.birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        db.session.commit()
        return patient
    
    @staticmethod
    def check_connection() -> bool:
        """Check if e-SUS API is available."""
        api_url = ESUSService._get_api_url()
        api_key = ESUSService._get_api_key()
        timeout = ESUSService._get_timeout()
        
        if not api_key:
            return False
        
        try:
            response = requests.get(
                f"{api_url}/health",
                timeout=timeout
            )
            return response.status_code == 200
        except requests.RequestException:
            return False
