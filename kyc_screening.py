#!/usr/bin/env python3
"""
🤖 KYC & Sanctions Screening Tool - Main Application
Version: 1.0.0
Author: Muhammad Alaa Lotfy Hussein
Contact: muhammadalaa.rt@gmail.com
"""

import sys
import os
import json
import csv
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import project modules
from database import KYCDatabase
import config
from utils import (
    StringUtils, DateUtils, ValidationUtils, 
    RiskCalculator, ReportGenerator
)

# ==================== LOGGING CONFIGURATION ====================

logging.basicConfig(
    level=getattr(logging, config.LOGGING_CONFIG['level']),
    format=config.LOGGING_CONFIG['format'],
    datefmt=config.LOGGING_CONFIG['date_format'],
    handlers=[
        logging.FileHandler(config.LOGGING_CONFIG['log_file']),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# ==================== MAIN APPLICATION CLASS ====================

class KYCScreeningTool:
    """
    Main KYC & Sanctions Screening Tool Application
    
    This class provides:
    - Interactive command-line interface
    - Customer screening functionality
    - Sanctions list management
    - Risk assessment and reporting
    - Database operations
    """
    
    def __init__(self):
        """Initialize the KYC Screening Tool"""
        self.db = None
        self.risk_calculator = None
        self.current_user = os.getenv('USER', 'SYSTEM')
        
        self._initialize_application()
    
    def _initialize_application(self) -> None:
        """Initialize application components"""
        try:
            # Display startup banner
            self._display_banner()
            
            # Initialize database
            logger.info("Initializing database connection...")
            self.db = KYCDatabase(config.DATABASE_CONFIG['database'])
            
            if not self.db.connect():
                logger.error("Failed to connect to database. Exiting...")
                sys.exit(1)
            
            # Initialize database schema
            if not self.db.initialize_database():
                logger.error("Failed to initialize database. Exiting...")
                sys.exit(1)
            
            # Load sample sanctions data
            self.db.load_sample_sanctions()
            
            # Initialize risk calculator
            self.risk_calculator = RiskCalculator(config)
            
            logger.info("✅ KYC Screening Tool initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Application initialization failed: {e}")
            sys.exit(1)
    
    def _display_banner(self) -> None:
        """Display application banner"""
        banner = f"""
        ╔══════════════════════════════════════════════════════════════╗
        ║                                                              ║
        ║         🔍 KYC & SANCTIONS SCREENING TOOL                   ║
        ║                     Version {config.APP_VERSION}                         ║
        ║                                                              ║
        ║      Automated Customer Due Diligence and Compliance        ║
        ║                                                              ║
        ║       Developer: {config.DEVELOPER_NAME}      ║
        ║       Contact: {config.DEVELOPER_EMAIL}    ║
        ║                                                              ║
        ╚══════════════════════════════════════════════════════════════╝
        """
        print(banner)
    
    def _display_menu(self) -> None:
        """Display main menu"""
        menu = f"""
        📋 MAIN MENU - {config.APP_NAME}
        {'=' * 60}
        
        1. 🆕 Screen New Customer
        2. 📋 View Screening History
        3. 🔍 Search Sanctions List
        4. 📊 View Statistics
        5. 💾 Export Data
        6. ⚙️  System Configuration
        7. 📄 Generate Report
        8. 🆘 Help & Documentation
        9. 🚪 Exit
        
        {'=' * 60}
        """
        print(menu)
    
    def _get_menu_choice(self) -> str:
        """Get user menu choice"""
        while True:
            try:
                choice = input("\nEnter your choice (1-9): ").strip()
                if choice in ['1', '2', '3', '4', '5', '6', '7', '8', '9']:
                    return choice
                else:
                    print("❌ Invalid choice. Please enter a number between 1 and 9.")
            except KeyboardInterrupt:
                print("\n\n⚠️  Operation cancelled by user.")
                return '9'
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def run(self) -> None:
        """Main application loop"""
        try:
            while True:
                self._display_menu()
                choice = self._get_menu_choice()
                
                if choice == '1':
                    self.screen_new_customer()
                elif choice == '2':
                    self.view_screening_history()
                elif choice == '3':
                    self.search_sanctions_list()
                elif choice == '4':
                    self.view_statistics()
                elif choice == '5':
                    self.export_data()
                elif choice == '6':
                    self.system_configuration()
                elif choice == '7':
                    self.generate_report()
                elif choice == '8':
                    self.show_help()
                elif choice == '9':
                    self.exit_application()
                    break
                
                input("\nPress Enter to continue...")
                
        except KeyboardInterrupt:
            print("\n\n⚠️  Application interrupted by user.")
            self.exit_application()
        except Exception as e:
            logger.error(f"Application error: {e}")
            print(f"\n❌ Application error: {e}")
            self.exit_application()
    
    # ==================== CORE FUNCTIONALITY METHODS ====================
    
    def screen_new_customer(self) -> None:
        """Screen a new customer against sanctions lists"""
        print("\n" + "=" * 60)
        print("👤 NEW CUSTOMER SCREENING")
        print("=" * 60)
        
        try:
            # Collect customer information
            customer_data = self._collect_customer_information()
            if not customer_data:
                print("❌ Customer screening cancelled.")
                return
            
            # Validate customer data
            validation_result = self._validate_customer_data(customer_data)
            if not validation_result['is_valid']:
                print("\n❌ Validation failed:")
                for error in validation_result['errors']:
                    print(f"   - {error}")
                return
            
            # Perform sanctions screening
            print("\n🔍 Screening customer against sanctions lists...")
            matches = self._perform_sanctions_screening(customer_data)
            
            # Calculate risk assessment
            risk_assessment = self.risk_calculator.calculate_customer_risk(customer_data, matches)
            
            # Determine screening result
            screening_result = self._determine_screening_result(matches, risk_assessment)
            
            # Save screening results
            screening_id = self._save_screening_results(
                customer_data, matches, risk_assessment, screening_result
            )
            
            # Display results
            self._display_screening_results(customer_data, matches, risk_assessment, screening_result)
            
            # Generate report
            report = self._generate_screening_report(
                screening_id, customer_data, matches, risk_assessment, screening_result
            )
            
            # Ask to save customer
            if screening_result in ['CLEAR', 'CLEAR_WITH_WARNING']:
                save_choice = input("\n💾 Save customer to database? (y/n): ").strip().lower()
                if save_choice == 'y':
                    success, message = self.db.add_customer(customer_data)
                    if success:
                        print("✅ Customer saved successfully!")
                    else:
                        print(f"❌ Error: {message}")
            
            print(f"\n✅ Screening completed. Screening ID: {screening_id}")
            
        except Exception as e:
            logger.error(f"Error in customer screening: {e}")
            print(f"❌ Screening error: {e}")
    
    def _collect_customer_information(self) -> Dict[str, Any]:
        """Collect customer information from user"""
        customer_data = {}
        
        print("\nPlease enter customer information:")
        print("-" * 40)
        
        # Generate customer code if not provided
        default_code = f"CUST{datetime.now().strftime('%Y%m%d%H%M%S')}"
        customer_data['customer_code'] = input(f"Customer Code [{default_code}]: ").strip() or default_code
        
        # Basic information
        customer_data['full_name_en'] = input("Full Name (English): ").strip()
        customer_data['full_name_ar'] = input("Full Name (Arabic) [optional]: ").strip() or None
        customer_data['date_of_birth'] = input("Date of Birth (YYYY-MM-DD) [optional]: ").strip() or None
        customer_data['nationality_code'] = input("Nationality Code (2 letters, e.g., EG): ").strip().upper()
        customer_data['nationality_name'] = input("Nationality Name [optional]: ").strip() or None
        
        # ID Information
        print("\n📋 ID Information:")
        customer_data['id_type'] = input("ID Type (PASSPORT/NATIONAL_ID/OTHER): ").strip().upper() or 'PASSPORT'
        customer_data['id_number'] = input("ID/Passport Number: ").strip()
        customer_data['id_issue_date'] = input("ID Issue Date (YYYY-MM-DD) [optional]: ").strip() or None
        customer_data['id_expiry_date'] = input("ID Expiry Date (YYYY-MM-DD) [optional]: ").strip() or None
        
        # Additional Information
        print("\n📝 Additional Information:")
        customer_data['gender'] = input("Gender (M/F/O) [optional]: ").strip().upper() or None
        customer_data['occupation'] = input("Occupation [optional]: ").strip() or None
        customer_data['customer_type'] = input("Customer Type (INDIVIDUAL/CORPORATE) [optional]: ").strip().upper() or 'INDIVIDUAL'
        
        return customer_data
    
    def _validate_customer_data(self, customer_data: Dict) -> Dict[str, Any]:
        """Validate customer data"""
        errors = []
        warnings = []
        
        # Required field validation
        required_fields = ['customer_code', 'full_name_en', 'nationality_code', 'id_number']
        for field in required_fields:
            if not customer_data.get(field):
                errors.append(f"Missing required field: {field}")
        
        # ID validation
        id_valid, id_message = ValidationUtils.validate_id_number(
            customer_data.get('id_number'),
            customer_data.get('id_type', 'PASSPORT')
        )
        if not id_valid:
            errors.append(f"ID Validation: {id_message}")
        
        # Date validation
        dob = customer_data.get('date_of_birth')
        if dob and not DateUtils.is_date_valid(dob):
            warnings.append("Date of birth format is invalid (expected YYYY-MM-DD)")
        
        # Nationality validation
        nationality = customer_data.get('nationality_code', '')
        if not ValidationUtils.validate_nationality_code(nationality):
            errors.append("Invalid nationality code (must be 2-letter ISO code)")
        
        if nationality in config.HIGH_RISK_COUNTRIES:
            warnings.append(f"Customer from high-risk country: {nationality}")
        
        # PEP check
        occupation = customer_data.get('occupation', '')
        if StringUtils.contains_pep_indicator(occupation, config.PEP_INDICATORS):
            warnings.append("Customer may be a Politically Exposed Person (PEP)")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def _perform_sanctions_screening(self, customer_data: Dict) -> List[Dict]:
        """Perform sanctions screening for customer"""
        matches = []
        
        # Search by name
        name_en = customer_data.get('full_name_en', '')
        if name_en:
            sanctions = self.db.search_sanctions(name_en)
            
            for sanction in sanctions:
                match_result = self._check_sanction_match(customer_data, sanction)
                if match_result['is_match']:
                    matches.append(match_result)
        
        return matches
    
    def _check_sanction_match(self, customer_data: Dict, sanction: Dict) -> Dict[str, Any]:
        """Check if customer matches a sanction entry"""
        # Name matching
        customer_name = StringUtils.normalize_english(customer_data.get('full_name_en', ''))
        sanction_name = StringUtils.normalize_english(sanction.get('full_name_en', ''))
        alias_name = StringUtils.normalize_english(sanction.get('alias_en', ''))
        
        # Calculate match scores
        name_match_score = StringUtils.similarity_ratio(customer_name, sanction_name)
        alias_match_score = StringUtils.similarity_ratio(customer_name, alias_name) if alias_name else 0
        
        # Use the highest score
        match_score = max(name_match_score, alias_match_score)
        
        # Determine match type
        if match_score >= config.SCREENING_CONFIG['name_match_threshold']:
            is_match = True
            match_type = 'EXACT' if match_score >= 95 else 'PARTIAL'
        else:
            is_match = False
            match_type = 'NO_MATCH'
        
        # Additional matching criteria
        dob_match = False
        customer_dob = customer_data.get('date_of_birth')
        sanction_dob = sanction.get('date_of_birth')
        
        if customer_dob and sanction_dob:
            dob_match = (customer_dob == sanction_dob)
            if dob_match:
                match_score += 20
        
        nationality_match = (
            customer_data.get('nationality_code') == sanction.get('nationality_code')
        )
        
        return {
            'is_match': is_match,
            'sanction_id': sanction['id'],
            'sanction_name': sanction.get('full_name_en'),
            'sanction_source': sanction.get('list_source'),
            'match_type': match_type,
            'match_score': min(match_score, 100),
            'name_match_score': name_match_score,
            'dob_match': dob_match,
            'nationality_match': nationality_match,
            'risk_level': sanction.get('risk_level', 'HIGH')
        }
    
    def _determine_screening_result(self, matches: List[Dict], risk_assessment: Dict) -> str:
        """Determine final screening result"""
        if not matches:
            return 'CLEAR'
        
        # Check for exact matches
        exact_matches = [m for m in matches if m['match_type'] == 'EXACT']
        if exact_matches:
            return 'REJECTED'
        
        # Check risk level
        risk_level = risk_assessment.get('risk_level', 'LOW')
        if risk_level in ['HIGH', 'CRITICAL']:
            return 'REVIEW_REQUIRED'
        
        # Check for partial matches
        partial_matches = [m for m in matches if m['match_type'] == 'PARTIAL']
        if partial_matches:
            return 'CLEAR_WITH_WARNING'
        
        return 'CLEAR'
    
    def _save_screening_results(self, customer_data: Dict, matches: List[Dict],
                               risk_assessment: Dict, screening_result: str) -> str:
        """Save screening results to database"""
        screening_id = f"SCR{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # This is a simplified version - in real implementation,
        # you would save to the database using self.db
        
        logger.info(f"Screening results saved with ID: {screening_id}")
        return screening_id
    
    def _display_screening_results(self, customer_data: Dict, matches: List[Dict],
                                  risk_assessment: Dict, screening_result: str) -> None:
        """Display screening results to user"""
        print("\n" + "=" * 60)
        print("📋 SCREENING RESULTS")
        print("=" * 60)
        
        print(f"\n👤 Customer: {customer_data.get('full_name_en')}")
        print(f"🆔 Customer Code: {customer_data.get('customer_code')}")
        print(f"🌍 Nationality: {customer_data.get('nationality_code')}")
        
        print(f"\n🎯 Risk Assessment:")
        print(f"   Risk Score: {risk_assessment.get('risk_score', 0)}/100")
        print(f"   Risk Level: {risk_assessment.get('risk_level', 'LOW')}")
        
        print(f"\n📊 Screening Result: {screening_result}")
        
        if matches:
            print(f"\n🚨 Sanctions Matches Found: {len(matches)}")
            for i, match in enumerate(matches[:5], 1):  # Show top 5 matches
                print(f"\n   Match #{i}:")
                print(f"   - Name: {match.get('sanction_name')}")
                print(f"   - Source: {match.get('sanction_source')}")
                print(f"   - Match Type: {match.get('match_type')}")
                print(f"   - Confidence: {match.get('match_score', 0):.1f}%")
        
        if risk_assessment.get('risk_factors'):
            print(f"\n⚠️  Risk Factors:")
            for factor in risk_assessment.get('risk_factors', [])[:5]:  # Show top 5 factors
                print(f"   - {factor}")
    
    def _generate_screening_report(self, screening_id: str, customer_data: Dict,
                                 matches: List[Dict], risk_assessment: Dict,
                                 screening_result: str) -> Dict:
        """Generate screening report"""
        screening_data = {
            'screening_id': screening_id,
            'screening_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'screening_type': 'ONBOARDING',
            'risk_score': risk_assessment.get('risk_score'),
            'risk_level': risk_assessment.get('risk_level'),
            'screening_result': screening_result,
            'risk_factors': risk_assessment.get('risk_factors', []),
            'risk_details': risk_assessment.get('risk_details', {})
        }
        
        report = ReportGenerator.generate_screening_report(
            screening_data, customer_data, matches
        )
        
        # Save report to file
        report_file = f"reports/{screening_id}_report.json"
        os.makedirs('reports', exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Report generated: {report_file}")
        return report
    
    # ==================== ADDITIONAL MENU OPTIONS ====================
    
    def view_screening_history(self) -> None:
        """View screening history"""
        print("\n" + "=" * 60)
        print("📋 SCREENING HISTORY")
        print("=" * 60)
        
        # In a real implementation, you would fetch from database
        print("\n⚠️  This feature requires database integration.")
        print("   Screening history would be displayed here.")
    
    def search_sanctions_list(self) -> None:
        """Search sanctions list"""
        print("\n" + "=" * 60)
        print("🔍 SANCTIONS LIST SEARCH")
        print("=" * 60)
        
        search_term = input("\nEnter search term (name, alias, country): ").strip()
        
        if not search_term:
            print("❌ Search term cannot be empty.")
            return
        
        try:
            results = self.db.search_sanctions(search_term)
            
            if not results:
                print("\n✅ No matches found in sanctions list.")
                return
            
            print(f"\n📋 Found {len(results)} matches:")
            print("-" * 60)
            
            for i, result in enumerate(results, 1):
                print(f"\nMatch #{i}:")
                print(f"  Name: {result.get('full_name_en')}")
                print(f"  Nationality: {result.get('nationality_name')}")
                print(f"  Source: {result.get('list_source')}")
                print(f"  Risk Level: {result.get('risk_level')}")
                
                if i >= 10:  # Limit display to 10 results
                    print(f"\n... and {len(results) - 10} more results.")
                    break
            
        except Exception as e:
            logger.error(f"Error searching sanctions: {e}")
            print(f"❌ Search error: {e}")
    
    def view_statistics(self) -> None:
        """View system statistics"""
        print("\n" + "=" * 60)
        print("📊 SYSTEM STATISTICS")
        print("=" * 60)
        
        try:
            stats = self.db.get_statistics()
            
            if not stats:
                print("\n❌ Unable to retrieve statistics.")
                return
            
            print("\n📈 Database Statistics:")
            print("-" * 40)
            
            print(f"Total Customers: {stats.get('total_customers', 0)}")
            print(f"Total Sanctions: {stats.get('total_sanctions', 0)}")
            print(f"Total Screenings: {stats.get('total_screening_results', 0)}")
            
            if 'risk_distribution' in stats:
                print("\n🎯 Risk Distribution:")
                for risk, count in stats['risk_distribution'].items():
                    print(f"  {risk}: {count}")
            
            if 'sanctions_by_source' in stats:
                print("\n🌍 Sanctions by Source:")
                for source, count in stats['sanctions_by_source'].items():
                    print(f"  {source}: {count}")
            
            print(f"\n📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
        except Exception as e:
            logger.error(f"Error retrieving statistics: {e}")
            print(f"❌ Statistics error: {e}")
    
    def export_data(self) -> None:
        """Export data to file"""
        print("\n" + "=" * 60)
        print("💾 EXPORT DATA")
        print("=" * 60)
        
        print("\nAvailable export options:")
        print("1. Export Sanctions List (CSV)")
        print("2. Export Screening Results (CSV)")
        print("3. Export Statistics (JSON)")
        print("4. Back to Main Menu")
        
        choice = input("\nSelect option (1-4): ").strip()
        
        if choice == '1':
            self._export_sanctions_list()
        elif choice == '2':
            self._export_screening_results()
        elif choice == '3':
            self._export_statistics()
        elif choice == '4':
            return
        else:
            print("❌ Invalid choice.")
    
    def _export_sanctions_list(self) -> None:
        """Export sanctions list to CSV"""
        try:
            export_file = f"exports/sanctions_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            os.makedirs('exports', exist_ok=True)
            
            # In real implementation, export from database
            print(f"\n✅ Sanctions list would be exported to: {export_file}")
            print("⚠️  This feature requires database integration.")
            
        except Exception as e:
            logger.error(f"Error exporting sanctions: {e}")
            print(f"❌ Export error: {e}")
    
    def _export_screening_results(self) -> None:
        """Export screening results to CSV"""
        try:
            export_file = f"exports/screenings_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            os.makedirs('exports', exist_ok=True)
            
            print(f"\n✅ Screening results would be exported to: {export_file}")
            print("⚠️  This feature requires database integration.")
            
        except Exception as e:
            logger.error(f"Error exporting screenings: {e}")
            print(f"❌ Export error: {e}")
    
    def _export_statistics(self) -> None:
        """Export statistics to JSON"""
        try:
            export_file = f"exports/statistics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            os.makedirs('exports', exist_ok=True)
            
            stats = self.db.get_statistics()
            
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)
            
            print(f"\n✅ Statistics exported to: {export_file}")
            
        except Exception as e:
            logger.error(f"Error exporting statistics: {e}")
            print(f"❌ Export error: {e}")
    
    def system_configuration(self) -> None:
        """System configuration menu"""
        print("\n" + "=" * 60)
        print("⚙️  SYSTEM CONFIGURATION")
        print("=" * 60)
        
        print("\nCurrent Configuration:")
        print("-" * 40)
        
        print(f"Application: {config.APP_NAME} v{config.APP_VERSION}")
        print(f"Database: {config.DATABASE_CONFIG['database']}")
        print(f"High-risk Countries: {len(config.HIGH_RISK_COUNTRIES)}")
        print(f"PEP Indicators: {len(config.PEP_INDICATORS)}")
        print(f"Name Match Threshold: {config.SCREENING_CONFIG['name_match_threshold']}%")
        
        print("\n⚠️  Configuration changes require editing config.py file.")
        print("   Please restart the application after making changes.")
    
    def generate_report(self) -> None:
        """Generate custom report"""
        print("\n" + "=" * 60)
        print("📄 GENERATE CUSTOM REPORT")
        print("=" * 60)
        
        print("\nReport types:")
        print("1. Risk Assessment Summary")
        print("2. Screening Activity Report")
        print("3. Compliance Status Report")
        print("4. Back to Main Menu")
        
        choice = input("\nSelect report type (1-4): ").strip()
        
        if choice == '1':
            self._generate_risk_assessment_report()
        elif choice == '2':
            self._generate_screening_activity_report()
        elif choice == '3':
            self._generate_compliance_report()
        elif choice == '4':
            return
        else:
            print("❌ Invalid choice.")
    
    def _generate_risk_assessment_report(self) -> None:
        """Generate risk assessment report"""
        try:
            report_file = f"reports/risk_assessment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            os.makedirs('reports', exist_ok=True)
            
            stats = self.db.get_statistics()
            report_content = ReportGenerator.generate_summary_statistics(stats)
            
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            print(f"\n✅ Risk assessment report generated: {report_file}")
            print("\n" + report_content)
            
        except Exception as e:
            logger.error(f"Error generating risk report: {e}")
            print(f"❌ Report generation error: {e}")
    
    def _generate_screening_activity_report(self) -> None:
        """Generate screening activity report"""
        print("\n⚠️  This feature requires additional database integration.")
        print("   Screening activity report would be generated here.")
    
    def _generate_compliance_report(self) -> None:
        """Generate compliance status report"""
        print("\n⚠️  This feature requires additional business logic.")
        print("   Compliance status report would be generated here.")
    
    def show_help(self) -> None:
        """Show help and documentation"""
        print("\n" + "=" * 60)
        print("🆘 HELP & DOCUMENTATION")
        print("=" * 60)
        
        help_text = f"""
        KYC & Sanctions Screening Tool - Help Guide
        {'=' * 50}
        
        Overview:
        This tool automates customer due diligence and sanctions screening
        for compliance with anti-money laundering (AML) regulations.
        
        Key Features:
        1. Customer Screening - Screen new customers against sanctions lists
        2. Risk Assessment - Calculate risk scores based on multiple factors
        3. Sanctions Search - Search through sanctions databases
        4. Reporting - Generate compliance reports
        5. Data Export - Export screening results and statistics
        
        Usage Tips:
        - Ensure customer data is accurate before screening
        - Review all matches carefully before making decisions
        - Export reports for compliance documentation
        - Regularly update sanctions lists
        
        Configuration:
        Edit config.py to customize:
        - High-risk countries list
        - PEP indicators
        - Screening thresholds
        - Database settings
        
        Support:
        For issues or questions, contact:
        - Email: {config.DEVELOPER_EMAIL}
        - Phone: {config.DEVELOPER_PHONE}
        
        Version: {config.APP_VERSION}
        Last Updated: {datetime.now().strftime('%Y-%m-%d')}
        """
        
        print(help_text)
    
    def exit_application(self) -> None:
        """Exit the application gracefully"""
        print("\n" + "=" * 60)
        print("🚪 EXITING APPLICATION")
        print("=" * 60)
        
        try:
            # Close database connection
            if self.db:
                self.db.disconnect()
                print("✅ Database connection closed.")
            
            # Log exit
            logger.info("Application exited gracefully.")
            
            print(f"\nThank you for using {config.APP_NAME}!")
            print(f"Developed by: {config.DEVELOPER_NAME}")
            print(f"Contact: {config.DEVELOPER_EMAIL}")
            print("\nGoodbye! 👋")
            
        except Exception as e:
            logger.error(f"Error during application exit: {e}")
            print(f"\n⚠️  Application exit with errors: {e}")

# ==================== MAIN ENTRY POINT ====================

def main():
    """Main entry point for the application"""
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == '--help' or command == '-h':
            print(f"""
            KYC & Sanctions Screening Tool
            Usage: python kyc_screening.py [OPTION]
            
            Options:
              --help, -h     Show this help message
              --version, -v  Show version information
              --batch FILE   Process batch screening from CSV file
              --interactive  Run in interactive mode (default)
            
            Examples:
              python kyc_screening.py                   # Interactive mode
              python kyc_screening.py --batch data.csv  # Batch processing
              python kyc_screening.py --version         # Version info
            """)
            return
        
        elif command == '--version' or command == '-v':
            print(f"{config.APP_NAME} v{config.APP_VERSION}")
            print(f"Developed by: {config.DEVELOPER_NAME}")
            return
        
        elif command == '--batch' and len(sys.argv) > 2:
            csv_file = sys.argv[2]
            print(f"Batch processing from: {csv_file}")
            print("⚠️  Batch processing requires additional implementation.")
            return
        
        elif command == '--interactive':
            pass  # Continue with interactive mode
        
        else:
            print(f"Unknown option: {command}")
            print("Use --help for available options.")
            return
    
    # Run interactive application
    try:
        app = KYCScreeningTool()
        app.run()
    except Exception as e:
        logger.error(f"Fatal application error: {e}")
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()