#!/usr/bin/env python3
"""
Configuration Settings for KYC & Sanctions Screening Tool
Version: 1.0.0
"""

import os
from datetime import datetime

# ==================== APPLICATION SETTINGS ====================
APP_NAME = "KYC & Sanctions Screening Tool"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Automated Customer Due Diligence and Sanctions Screening"
DEVELOPER_NAME = "Muhammad Alaa Lotfy Hussein"
DEVELOPER_EMAIL = "muhammadalaa.rt@gmail.com"
DEVELOPER_PHONE = "+201034024403"
COPYRIGHT_YEAR = datetime.now().year

# ==================== DATABASE CONFIGURATION ====================
DATABASE_CONFIG = {
    'engine': 'sqlite',
    'database': 'kyc_screening.db',
    'host': 'localhost',
    'port': None,
    'pool_size': 10,
    'max_overflow': 20,
    'pool_timeout': 30,
    'echo': False
}

# ==================== SCREENING CONFIGURATION ====================
SCREENING_CONFIG = {
    'name_match_threshold': 85,      # Minimum similarity score for name matching
    'dob_match_threshold': 90,       # Minimum similarity score for date of birth matching
    'id_match_threshold': 95,        # Minimum similarity score for ID matching
    'fuzzy_match_enabled': True,     # Enable fuzzy matching algorithms
    'partial_match_weight': 0.7,     # Weight for partial matches in risk scoring
    'exact_match_weight': 1.0,       # Weight for exact matches in risk scoring
    'auto_generate_reports': True,   # Automatically generate screening reports
    'default_screening_type': 'ONBOARDING',  # Default screening type
}

# ==================== RISK ASSESSMENT CONFIGURATION ====================
RISK_SCORING = {
    'pep_penalty': 30,               # Risk score penalty for PEP identification
    'high_risk_country_penalty': 25, # Risk score penalty for high-risk countries
    'sanction_match_penalty': 100,   # Risk score penalty for sanction matches
    'partial_match_penalty': 50,     # Risk score penalty for partial matches
    'age_risk_threshold': 70,        # Age threshold for additional risk (years)
    'unusual_id_penalty': 20,        # Penalty for unusual ID patterns
    'max_risk_score': 100,           # Maximum possible risk score
}

# ==================== HIGH-RISK COUNTRIES ====================
HIGH_RISK_COUNTRIES = [
    'AF',  # Afghanistan
    'IR',  # Iran
    'KP',  # North Korea
    'SY',  # Syria
    'YE',  # Yemen
    'SD',  # Sudan
    'SO',  # Somalia
    'IQ',  # Iraq
    'LY',  # Libya
    'VE',  # Venezuela
    'CU',  # Cuba
    'RU',  # Russia
    'BY',  # Belarus
    'MM',  # Myanmar
    'ER',  # Eritrea
    'ZW',  # Zimbabwe
]

MEDIUM_RISK_COUNTRIES = [
    'PK',  # Pakistan
    'NG',  # Nigeria
    'ET',  # Ethiopia
    'CD',  # DR Congo
    'TZ',  # Tanzania
    'KE',  # Kenya
    'UG',  # Uganda
    'GH',  # Ghana
    'CI',  # Ivory Coast
    'CM',  # Cameroon
]

# ==================== PEP (POLITICALLY EXPOSED PERSONS) INDICATORS ====================
PEP_INDICATORS = [
    # Political Positions
    'minister', 'president', 'prime minister', 'senator', 'congress', 'parliament',
    'ambassador', 'governor', 'mayor', 'diplomat', 'secretary', 'commissioner',
    
    # Military Ranks
    'general', 'colonel', 'major', 'captain', 'admiral', 'marshal',
    
    # Royalty and Nobility
    'king', 'queen', 'prince', 'princess', 'emir', 'sultan', 'sheikh', 'royal',
    
    # Judiciary
    'judge', 'justice', 'magistrate', 'prosecutor',
    
    # Government Agencies
    'director', 'commissioner', 'controller', 'auditor',
]

# ==================== SANCTIONS LIST SOURCES ====================
SANCTIONS_SOURCES = {
    'OFAC': 'Office of Foreign Assets Control (US Treasury)',
    'UN': 'United Nations Security Council',
    'EU': 'European Union Consolidated List',
    'UK': 'UK Office of Financial Sanctions Implementation',
    'AU': 'Australian Department of Foreign Affairs and Trade',
    'CA': 'Canadian Office of the Superintendent of Financial Institutions',
}

# ==================== FILE PATHS AND DIRECTORIES ====================
FILE_PATHS = {
    'database': 'kyc_screening.db',
    'logs': 'logs/',
    'exports': 'exports/',
    'reports': 'reports/',
    'templates': 'templates/',
    'backups': 'backups/',
}

# ==================== LOGGING CONFIGURATION ====================
LOGGING_CONFIG = {
    'level': 'INFO',  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'date_format': '%Y-%m-%d %H:%M:%S',
    'log_file': 'kyc_screening.log',
    'max_size_mb': 10,  # Maximum log file size in MB
    'backup_count': 5,  # Number of backup log files to keep
}

# ==================== REPORT CONFIGURATION ====================
REPORT_CONFIG = {
    'company_name': 'AML Compliance Solutions',
    'company_logo': None,  # Path to logo image (optional)
    'report_footer': 'Confidential - For Internal Use Only',
    'date_format': '%d/%m/%Y %H:%M:%S',
    'timezone': 'Africa/Cairo',
    'default_language': 'en',  # en, ar
    'include_executive_summary': True,
    'include_recommendations': True,
}

# ==================== VALIDATION RULES ====================
VALIDATION_RULES = {
    'min_name_length': 2,
    'max_name_length': 100,
    'min_id_length': 4,
    'max_id_length': 50,
    'allowed_id_types': ['PASSPORT', 'NATIONAL_ID', 'DRIVERS_LICENSE', 'RESIDENCE_PERMIT'],
    'allowed_genders': ['M', 'F', 'O'],  # Male, Female, Other
    'allowed_customer_types': ['INDIVIDUAL', 'CORPORATE', 'PARTNERSHIP', 'TRUST'],
}

# ==================== UTILITY FUNCTIONS ====================
def create_directories():
    """Create necessary directories for the application"""
    for path in FILE_PATHS.values():
        if path and '/' in path and not path.endswith('.db'):
            os.makedirs(path, exist_ok=True)
            print(f"Created directory: {path}")

def get_current_timestamp():
    """Get current timestamp in standard format"""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def validate_country_code(country_code):
    """Validate if a country code is valid (2-letter ISO code)"""
    if not country_code or len(country_code) != 2:
        return False
    return country_code.isalpha()

# Initialize directories when module is imported
create_directories()