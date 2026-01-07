#!/usr/bin/env python3
"""
Utility Functions Module for KYC & Sanctions Screening Tool
Version: 1.0.0
"""

import re
import unicodedata
import json
from datetime import datetime, date, timedelta
from difflib import SequenceMatcher
from typing import Dict, List, Tuple, Optional, Any, Union
import logging
import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== STRING UTILITIES ====================

class StringUtils:
    """Utilities for string manipulation and comparison"""
    
    @staticmethod
    def normalize_arabic(text: str) -> str:
        """
        Normalize Arabic text for consistent comparison
        
        Args:
            text (str): Arabic text to normalize
        
        Returns:
            str: Normalized text
        """
        if not text or not isinstance(text, str):
            return ""
        
        try:
            # Normalize Unicode characters
            text = unicodedata.normalize('NFKD', text)
            text = ''.join([c for c in text if not unicodedata.combining(c)])
            
            # Replace Arabic variations with standard forms
            replacements = {
                'آ': 'ا',
                'أ': 'ا',
                'إ': 'ا',
                'ى': 'ي',
                'ة': 'ه',
                'ؤ': 'و',
                'ئ': 'ي',
            }
            
            for old, new in replacements.items():
                text = text.replace(old, new)
            
            # Remove diacritics and tatweel
            text = re.sub(r'[\u064B-\u065F\u0670]', '', text)
            text = text.replace('ـ', '')
            
            # Remove extra whitespace
            text = ' '.join(text.split())
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error normalizing Arabic text: {e}")
            return text.strip() if text else ""
    
    @staticmethod
    def normalize_english(text: str) -> str:
        """
        Normalize English text for consistent comparison
        
        Args:
            text (str): English text to normalize
        
        Returns:
            str: Normalized text
        """
        if not text or not isinstance(text, str):
            return ""
        
        try:
            # Convert to lowercase
            text = text.lower().strip()
            
            # Remove common titles and honorifics
            titles = ['mr', 'mrs', 'ms', 'miss', 'dr', 'prof', 'eng', 
                     'sir', 'madam', 'lord', 'lady', 'haj', 'sheikh']
            
            for title in titles:
                text = re.sub(rf'\b{title}\b\.?\s*', '', text)
            
            # Remove punctuation and special characters
            text = re.sub(r'[^\w\s]', ' ', text)
            
            # Remove extra whitespace
            text = ' '.join(text.split())
            
            return text
            
        except Exception as e:
            logger.error(f"Error normalizing English text: {e}")
            return text.strip() if text else ""
    
    @staticmethod
    def similarity_ratio(str1: str, str2: str) -> float:
        """
        Calculate similarity ratio between two strings
        
        Args:
            str1 (str): First string
            str2 (str): Second string
        
        Returns:
            float: Similarity ratio (0-100)
        """
        if not str1 or not str2:
            return 0.0
        
        try:
            # Use SequenceMatcher for accurate similarity calculation
            return SequenceMatcher(None, str(str1), str(str2)).ratio() * 100
            
        except Exception as e:
            logger.error(f"Error calculating similarity ratio: {e}")
            return 0.0
    
    @staticmethod
    def fuzzy_match_names(name1: str, name2: str, threshold: float = 85.0) -> Tuple[bool, float]:
        """
        Perform fuzzy matching between two names
        
        Args:
            name1 (str): First name
            name2 (str): Second name
            threshold (float): Match threshold (0-100)
        
        Returns:
            tuple: (is_match, match_score)
        """
        if not name1 or not name2:
            return False, 0.0
        
        # Normalize names
        norm1 = StringUtils.normalize_english(name1)
        norm2 = StringUtils.normalize_english(name2)
        
        # Calculate multiple similarity metrics
        ratio = StringUtils.similarity_ratio(norm1, norm2)
        partial_ratio = StringUtils._partial_ratio(norm1, norm2)
        token_sort_ratio = StringUtils._token_sort_ratio(norm1, norm2)
        
        # Use the highest score
        match_score = max(ratio, partial_ratio, token_sort_ratio)
        is_match = match_score >= threshold
        
        return is_match, match_score
    
    @staticmethod
    def _partial_ratio(str1: str, str2: str) -> float:
        """Calculate partial ratio for fuzzy matching"""
        if len(str1) <= len(str2):
            shorter, longer = str1, str2
        else:
            shorter, longer = str2, str1
        
        m = len(shorter)
        scores = []
        
        for i in range(len(longer) - m + 1):
            substring = longer[i:i + m]
            score = StringUtils.similarity_ratio(shorter, substring)
            scores.append(score)
        
        return max(scores) if scores else 0.0
    
    @staticmethod
    def _token_sort_ratio(str1: str, str2: str) -> float:
        """Calculate token sort ratio for fuzzy matching"""
        tokens1 = sorted(str1.split())
        tokens2 = sorted(str2.split())
        
        sorted1 = ' '.join(tokens1)
        sorted2 = ' '.join(tokens2)
        
        return StringUtils.similarity_ratio(sorted1, sorted2)
    
    @staticmethod
    def extract_names(full_name: str) -> Tuple[str, str]:
        """
        Extract first and last names from full name
        
        Args:
            full_name (str): Full name
        
        Returns:
            tuple: (first_name, last_name)
        """
        if not full_name:
            return "", ""
        
        parts = full_name.strip().split()
        
        if len(parts) == 0:
            return "", ""
        elif len(parts) == 1:
            return parts[0], ""
        else:
            return parts[0], parts[-1]
    
    @staticmethod
    def contains_pep_indicator(text: str, indicators: List[str] = None) -> bool:
        """
        Check if text contains PEP indicators
        
        Args:
            text (str): Text to check
            indicators (list): List of PEP indicators
        
        Returns:
            bool: True if PEP indicator found
        """
        if not text:
            return False
        
        indicators = indicators or config.PEP_INDICATORS
        text_lower = text.lower()
        
        for indicator in indicators:
            if indicator in text_lower:
                return True
        
        return False

# ==================== DATE UTILITIES ====================

class DateUtils:
    """Utilities for date manipulation and validation"""
    
    @staticmethod
    def calculate_age(birth_date: Union[str, date]) -> Optional[int]:
        """
        Calculate age from birth date
        
        Args:
            birth_date: Date of birth (string or date object)
        
        Returns:
            int: Age in years or None if invalid
        """
        if not birth_date:
            return None
        
        try:
            # Convert string to date if necessary
            if isinstance(birth_date, str):
                birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
            
            if not isinstance(birth_date, date):
                return None
            
            today = date.today()
            age = today.year - birth_date.year
            
            # Adjust if birthday hasn't occurred yet this year
            if (today.month, today.day) < (birth_date.month, birth_date.day):
                age -= 1
            
            return age
            
        except (ValueError, TypeError) as e:
            logger.error(f"Error calculating age: {e}")
            return None
    
    @staticmethod
    def is_date_valid(date_str: str, date_format: str = '%Y-%m-%d') -> bool:
        """
        Check if a date string is valid
        
        Args:
            date_str (str): Date string to validate
            date_format (str): Expected date format
        
        Returns:
            bool: True if valid date
        """
        if not date_str:
            return False
        
        try:
            datetime.strptime(date_str, date_format)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def format_date(date_obj: Union[str, datetime, date], 
                   date_format: str = '%d/%m/%Y') -> str:
        """
        Format date object to string
        
        Args:
            date_obj: Date object or string
            date_format (str): Output format
        
        Returns:
            str: Formatted date string
        """
        if not date_obj:
            return ""
        
        try:
            # Convert string to datetime if necessary
            if isinstance(date_obj, str):
                for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d']:
                    try:
                        date_obj = datetime.strptime(date_obj, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    return date_obj  # Return original if cannot parse
            
            # Format the date
            if isinstance(date_obj, (datetime, date)):
                return date_obj.strftime(date_format)
            
            return str(date_obj)
            
        except Exception as e:
            logger.error(f"Error formatting date: {e}")
            return str(date_obj) if date_obj else ""
    
    @staticmethod
    def calculate_date_difference(date1: Union[str, date], 
                                 date2: Union[str, date]) -> Optional[int]:
        """
        Calculate difference in days between two dates
        
        Args:
            date1: First date
            date2: Second date
        
        Returns:
            int: Difference in days or None if invalid
        """
        try:
            # Convert strings to dates if necessary
            if isinstance(date1, str):
                date1 = datetime.strptime(date1, '%Y-%m-%d').date()
            if isinstance(date2, str):
                date2 = datetime.strptime(date2, '%Y-%m-%d').date()
            
            if not isinstance(date1, date) or not isinstance(date2, date):
                return None
            
            return abs((date2 - date1).days)
            
        except Exception as e:
            logger.error(f"Error calculating date difference: {e}")
            return None

# ==================== VALIDATION UTILITIES ====================

class ValidationUtils:
    """Utilities for data validation"""
    
    @staticmethod
    def validate_id_number(id_number: str, id_type: str = 'NATIONAL_ID') -> Tuple[bool, str]:
        """
        Validate ID number based on type
        
        Args:
            id_number (str): ID number to validate
            id_type (str): Type of ID
        
        Returns:
            tuple: (is_valid, message)
        """
        if not id_number or not isinstance(id_number, str):
            return False, "Invalid ID number"
        
        id_number = id_number.strip()
        
        if id_type.upper() == 'NATIONAL_ID':
            # Egyptian National ID validation
            if len(id_number) != 14 or not id_number.isdigit():
                return False, "Egyptian National ID must be 14 digits"
            
            # Validate century code
            century_code = int(id_number[0])
            if century_code not in [2, 3]:
                return False, "Invalid century code in Egyptian National ID"
            
            # Validate birth date
            year = int(id_number[1:3])
            month = int(id_number[3:5])
            day = int(id_number[5:7])
            
            if century_code == 2:
                year += 1900
            else:  # century_code == 3
                year += 2000
            
            try:
                datetime(year, month, day)
            except ValueError:
                return False, "Invalid birth date in Egyptian National ID"
            
            return True, "Valid Egyptian National ID"
        
        elif id_type.upper() == 'PASSPORT':
            # Passport validation
            if len(id_number) < 6:
                return False, "Passport number must be at least 6 characters"
            
            # Basic format check (letter followed by digits)
            if not re.match(r'^[A-Za-z][A-Za-z0-9]*$', id_number):
                return False, "Invalid passport number format"
            
            return True, "Valid passport number"
        
        else:
            # Generic ID validation
            if len(id_number) < 4:
                return False, "ID number too short"
            
            return True, "Valid ID number"
    
    @staticmethod
    def validate_phone_number(phone: str) -> Tuple[bool, str]:
        """
        Validate phone number format
        
        Args:
            phone (str): Phone number to validate
        
        Returns:
            tuple: (is_valid, message)
        """
        if not phone:
            return False, "Phone number is required"
        
        # Remove all non-digit characters except +
        phone_clean = re.sub(r'[^\d+]', '', phone)
        
        # Check Egyptian phone numbers
        if phone_clean.startswith('+20'):
            if len(phone_clean) == 13:  # +20XXXXXXXXXXX
                return True, "Valid Egyptian phone number"
        elif phone_clean.startswith('01'):
            if len(phone_clean) == 11:  # 01XXXXXXXXX
                return True, "Valid Egyptian phone number"
        
        # Check international format
        if phone_clean.startswith('+'):
            if 10 <= len(phone_clean) <= 15:
                return True, "Valid international phone number"
        
        return False, "Invalid phone number format"
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        """
        Validate email address format
        
        Args:
            email (str): Email address to validate
        
        Returns:
            tuple: (is_valid, message)
        """
        if not email:
            return False, "Email is required"
        
        # Basic email pattern
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if re.match(pattern, email):
            return True, "Valid email address"
        
        return False, "Invalid email format"
    
    @staticmethod
    def validate_nationality_code(country_code: str) -> bool:
        """
        Validate country code (2-letter ISO code)
        
        Args:
            country_code (str): Country code to validate
        
        Returns:
            bool: True if valid
        """
        if not country_code or len(country_code) != 2:
            return False
        
        return country_code.isalpha() and country_code.isupper()

# ==================== RISK CALCULATOR ====================

class RiskCalculator:
    """Calculate risk scores for customers"""
    
    def __init__(self, config_module):
        """
        Initialize risk calculator
        
        Args:
            config_module: Configuration module
        """
        self.config = config_module
    
    def calculate_customer_risk(self, customer_data: Dict[str, Any], 
                               sanction_matches: List[Dict]) -> Dict[str, Any]:
        """
        Calculate comprehensive risk score for a customer
        
        Args:
            customer_data (dict): Customer information
            sanction_matches (list): List of sanction matches
        
        Returns:
            dict: Risk assessment results
        """
        risk_score = 0
        risk_factors = []
        risk_details = {}
        
        # 1. PEP Check
        occupation = customer_data.get('occupation', '').lower()
        if StringUtils.contains_pep_indicator(occupation, self.config.PEP_INDICATORS):
            pep_penalty = self.config.RISK_SCORING['pep_penalty']
            risk_score += pep_penalty
            risk_factors.append("PEP - Politically Exposed Person")
            risk_details['pep_detected'] = True
            risk_details['pep_penalty'] = pep_penalty
        
        # 2. High-risk Country Check
        nationality = customer_data.get('nationality_code', '')
        if nationality in self.config.HIGH_RISK_COUNTRIES:
            country_penalty = self.config.RISK_SCORING['high_risk_country_penalty']
            risk_score += country_penalty
            risk_factors.append(f"High-risk country: {nationality}")
            risk_details['high_risk_country'] = True
            risk_details['country_penalty'] = country_penalty
        
        # 3. Sanction Matches
        if sanction_matches:
            for match in sanction_matches:
                if match.get('match_type') == 'EXACT':
                    penalty = self.config.RISK_SCORING['sanction_match_penalty']
                    risk_score += penalty
                    risk_factors.append(f"Exact sanction match: {match.get('sanction_name', 'Unknown')}")
                    risk_details['exact_matches'] = risk_details.get('exact_matches', 0) + 1
                else:
                    penalty = self.config.RISK_SCORING['partial_match_penalty']
                    risk_score += penalty
                    risk_factors.append(f"Partial sanction match: {match.get('sanction_name', 'Unknown')}")
                    risk_details['partial_matches'] = risk_details.get('partial_matches', 0) + 1
        
        # 4. Age-based Risk
        dob = customer_data.get('date_of_birth')
        if dob:
            age = DateUtils.calculate_age(dob)
            if age and age > self.config.RISK_SCORING['age_risk_threshold']:
                risk_score += 15
                risk_factors.append(f"High age risk: {age} years")
                risk_details['age_risk'] = True
        
        # 5. ID Number Pattern Analysis
        id_number = customer_data.get('id_number', '')
        if id_number:
            # Check for suspicious patterns
            if len(set(id_number)) <= 3:  # Too many repeating digits
                penalty = self.config.RISK_SCORING['unusual_id_penalty']
                risk_score += penalty
                risk_factors.append("Suspicious ID number pattern")
                risk_details['suspicious_id'] = True
            
            # Check if ID is all zeros or sequential
            if id_number == '0' * len(id_number):
                risk_score += 20
                risk_factors.append("ID number contains only zeros")
        
        # 6. Additional Risk Factors
        # - Multiple nationalities
        # - Unusual occupation patterns
        # - Recent changes in customer data
        
        # Cap risk score at maximum
        max_score = self.config.RISK_SCORING['max_risk_score']
        risk_score = min(risk_score, max_score)
        
        # Determine risk level
        risk_level = self._determine_risk_level(risk_score)
        
        return {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'risk_details': risk_details,
            'calculation_time': datetime.now().isoformat()
        }
    
    def _determine_risk_level(self, risk_score: int) -> str:
        """
        Determine risk level based on score
        
        Args:
            risk_score (int): Calculated risk score
        
        Returns:
            str: Risk level category
        """
        if risk_score >= 80:
            return 'CRITICAL'
        elif risk_score >= 60:
            return 'HIGH'
        elif risk_score >= 40:
            return 'MEDIUM'
        elif risk_score >= 20:
            return 'LOW'
        else:
            return 'VERY_LOW'

# ==================== REPORT GENERATOR ====================

class ReportGenerator:
    """Generate screening reports and documentation"""
    
    @staticmethod
    def generate_screening_report(screening_data: Dict, customer_data: Dict, 
                                 matches: List[Dict]) -> Dict[str, Any]:
        """
        Generate comprehensive screening report
        
        Args:
            screening_data (dict): Screening results
            customer_data (dict): Customer information
            matches (list): List of sanction matches
        
        Returns:
            dict: Complete screening report
        """
        report_id = f"SCR-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        report = {
            'report_id': report_id,
            'generation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'report_type': 'KYC_SCREENING_REPORT',
            'version': '1.0',
            
            'customer_information': {
                'customer_code': customer_data.get('customer_code'),
                'full_name': customer_data.get('full_name_en'),
                'nationality': customer_data.get('nationality_code'),
                'date_of_birth': customer_data.get('date_of_birth'),
                'id_number': customer_data.get('id_number'),
                'occupation': customer_data.get('occupation'),
            },
            
            'screening_summary': {
                'screening_id': screening_data.get('screening_id'),
                'screening_date': screening_data.get('screening_date'),
                'screening_type': screening_data.get('screening_type'),
                'total_matches': len(matches),
                'exact_matches': sum(1 for m in matches if m.get('match_type') == 'EXACT'),
                'partial_matches': sum(1 for m in matches if m.get('match_type') == 'PARTIAL'),
                'risk_score': screening_data.get('risk_score'),
                'risk_level': screening_data.get('risk_level'),
                'screening_result': screening_data.get('screening_result'),
            },
            
            'matches_details': matches,
            
            'risk_assessment': {
                'risk_factors': screening_data.get('risk_factors', []),
                'risk_details': screening_data.get('risk_details', {}),
            },
            
            'recommendations': ReportGenerator._generate_recommendations(screening_data, matches),
            
            'disclaimer': "This report is generated automatically for compliance screening purposes. " \
                         "Final decisions should be made by authorized personnel.",
        }
        
        return report
    
    @staticmethod
    def _generate_recommendations(screening_data: Dict, matches: List[Dict]) -> List[str]:
        """
        Generate recommendations based on screening results
        
        Args:
            screening_data (dict): Screening results
            matches (list): List of sanction matches
        
        Returns:
            list: List of recommendations
        """
        recommendations = []
        risk_level = screening_data.get('risk_level', 'LOW')
        
        if not matches:
            recommendations.append("✅ No sanctions matches found - Proceed with standard onboarding")
        else:
            recommendations.append("🚨 Sanctions matches detected - Immediate review required")
            
            exact_matches = [m for m in matches if m.get('match_type') == 'EXACT']
            if exact_matches:
                recommendations.append("⛔ REJECT customer - Exact matches with sanctioned entities")
                for match in exact_matches[:3]:  # Show top 3 matches
                    recommendations.append(f"   - {match.get('sanction_name')} ({match.get('sanction_source')})")
            
            partial_matches = [m for m in matches if m.get('match_type') == 'PARTIAL']
            if partial_matches:
                recommendations.append("⚠️ Enhanced Due Diligence required - Partial matches found")
        
        # Additional recommendations based on risk level
        if risk_level in ['HIGH', 'CRITICAL']:
            recommendations.append("📋 Request additional verification documents")
            recommendations.append("⏰ Schedule monthly monitoring for first 6 months")
            recommendations.append("👥 Escalate to senior compliance officer for review")
        
        elif risk_level == 'MEDIUM':
            recommendations.append("📝 Conduct additional verification checks")
            recommendations.append("🔄 Schedule quarterly review")
        
        else:  # LOW or VERY_LOW
            recommendations.append("✅ Standard monitoring procedures applicable")
        
        # General recommendations
        recommendations.append("🔒 Ensure all customer documents are properly archived")
        recommendations.append("📅 Schedule next review based on risk level")
        
        return recommendations
    
    @staticmethod
    def generate_csv_report(data: List[Dict], output_file: str) -> bool:
        """
        Generate CSV report from data
        
        Args:
            data (list): List of dictionaries to export
            output_file (str): Path to output CSV file
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            import pandas as pd
            
            df = pd.DataFrame(data)
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            logger.info(f"✅ CSV report generated: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error generating CSV report: {e}")
            return False
    
    @staticmethod
    def generate_summary_statistics(statistics: Dict) -> str:
        """
        Generate human-readable summary from statistics
        
        Args:
            statistics (dict): Statistics data
        
        Returns:
            str: Formatted summary
        """
        summary_lines = [
            "📊 KYC SCREENING STATISTICS SUMMARY",
            "=" * 50,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            ""
        ]
        
        # Add key statistics
        if 'total_customers' in statistics:
            summary_lines.append(f"Total Customers Screened: {statistics['total_customers']}")
        
        if 'total_sanctions' in statistics:
            summary_lines.append(f"Sanctions Records: {statistics['total_sanctions']}")
        
        if 'screening_results' in statistics:
            summary_lines.append("\nScreening Results:")
            for result, count in statistics['screening_results'].items():
                summary_lines.append(f"  {result}: {count}")
        
        if 'risk_distribution' in statistics:
            summary_lines.append("\nRisk Level Distribution:")
            for risk, count in statistics['risk_distribution'].items():
                summary_lines.append(f"  {risk}: {count}")
        
        summary_lines.append("\n" + "=" * 50)
        
        return '\n'.join(summary_lines)

# ==================== HELPER FUNCTIONS ====================

def get_current_timestamp() -> str:
    """Get current timestamp in ISO format"""
    return datetime.now().isoformat()

def format_currency(amount: float, currency: str = 'USD') -> str:
    """Format currency amount"""
    return f"{amount:,.2f} {currency}"

def safe_json_dumps(data: Any) -> str:
    """Safely convert data to JSON string"""
    try:
        return json.dumps(data, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error converting to JSON: {e}")
        return str(data)

def mask_sensitive_data(text: str, visible_chars: int = 4) -> str:
    """Mask sensitive data for logging"""
    if not text or len(text) <= visible_chars:
        return "***"
    return text[:visible_chars] + "***"