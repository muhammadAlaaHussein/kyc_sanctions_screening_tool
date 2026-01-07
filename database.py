#!/usr/bin/env python3
"""
Database Module for KYC & Sanctions Screening Tool
Version: 1.0.0
"""

import sqlite3
import pandas as pd
import json
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Tuple, Any
import config

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOGGING_CONFIG['level']),
    format=config.LOGGING_CONFIG['format'],
    datefmt=config.LOGGING_CONFIG['date_format']
)
logger = logging.getLogger(__name__)

class KYCDatabase:
    """
    Database management class for KYC Screening Tool
    
    This class handles all database operations including:
    - Database connection management
    - Table creation and initialization
    - Data insertion, retrieval, and updates
    - Sanctions list management
    - Screening results storage
    """
    
    def __init__(self, db_path: str = None):
        """
        Initialize the database connection
        
        Args:
            db_path (str): Path to the SQLite database file
        """
        self.db_path = db_path or config.DATABASE_CONFIG['database']
        self.conn = None
        self.cursor = None
        self.connected = False
        
    def connect(self) -> bool:
        """
        Establish connection to the database
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # Enable dictionary-like access
            self.cursor = self.conn.cursor()
            self.conn.execute("PRAGMA foreign_keys = ON")
            self.conn.execute("PRAGMA journal_mode = WAL")
            
            self.connected = True
            logger.info(f"✅ Successfully connected to database: {self.db_path}")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"❌ Database connection error: {e}")
            self.connected = False
            return False
    
    def disconnect(self) -> None:
        """Close the database connection"""
        if self.conn:
            self.conn.close()
            self.connected = False
            logger.info("✅ Database connection closed")
    
    def initialize_database(self) -> bool:
        """
        Initialize database with all required tables
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        if not self.connected:
            logger.error("❌ Cannot initialize database: No active connection")
            return False
        
        try:
            # ========== CUSTOMERS TABLE ==========
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_code VARCHAR(20) UNIQUE NOT NULL,
                    full_name_ar VARCHAR(100),
                    full_name_en VARCHAR(100) NOT NULL,
                    date_of_birth DATE,
                    nationality_code CHAR(2) NOT NULL,
                    nationality_name VARCHAR(50),
                    id_type VARCHAR(20) NOT NULL,
                    id_number VARCHAR(50) UNIQUE NOT NULL,
                    id_issue_date DATE,
                    id_expiry_date DATE,
                    gender CHAR(1),
                    occupation VARCHAR(100),
                    customer_type VARCHAR(20) DEFAULT 'INDIVIDUAL',
                    risk_category VARCHAR(20) DEFAULT 'LOW',
                    pep_flag BOOLEAN DEFAULT 0,
                    kyc_status VARCHAR(20) DEFAULT 'PENDING',
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    CHECK (gender IN ('M', 'F', 'O')),
                    CHECK (risk_category IN ('VERY_LOW', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
                    CHECK (kyc_status IN ('PENDING', 'IN_PROGRESS', 'COMPLETED', 'REJECTED', 'ON_HOLD'))
                )
            ''')
            
            # ========== ADDRESSES TABLE ==========
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS addresses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_code VARCHAR(20) NOT NULL,
                    address_type VARCHAR(20) NOT NULL,
                    country_code CHAR(2) NOT NULL,
                    city VARCHAR(50) NOT NULL,
                    street VARCHAR(200),
                    postal_code VARCHAR(20),
                    is_primary BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (customer_code) REFERENCES customers(customer_code) ON DELETE CASCADE,
                    CHECK (address_type IN ('RESIDENTIAL', 'BUSINESS', 'MAILING', 'OTHER'))
                )
            ''')
            
            # ========== CONTACTS TABLE ==========
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_code VARCHAR(20) NOT NULL,
                    contact_type VARCHAR(20) NOT NULL,
                    contact_value VARCHAR(100) NOT NULL,
                    is_primary BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (customer_code) REFERENCES customers(customer_code) ON DELETE CASCADE,
                    CHECK (contact_type IN ('EMAIL', 'PHONE', 'MOBILE', 'FAX', 'WEBSITE'))
                )
            ''')
            
            # ========== SANCTIONS TABLE ==========
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS sanctions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    list_source VARCHAR(20) NOT NULL,
                    list_type VARCHAR(30),
                    reference_id VARCHAR(50),
                    full_name_ar VARCHAR(200),
                    full_name_en VARCHAR(200) NOT NULL,
                    alias_ar VARCHAR(200),
                    alias_en VARCHAR(200),
                    nationality_code CHAR(2),
                    nationality_name VARCHAR(50),
                    date_of_birth DATE,
                    place_of_birth VARCHAR(100),
                    id_type VARCHAR(20),
                    id_number VARCHAR(100),
                    designation VARCHAR(200),
                    reason TEXT,
                    effective_date DATE,
                    expiry_date DATE,
                    un_resolution VARCHAR(50),
                    eu_regulation VARCHAR(50),
                    ofac_id VARCHAR(50),
                    risk_level VARCHAR(20) DEFAULT 'HIGH',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    CHECK (list_source IN ('OFAC', 'UN', 'EU', 'UK', 'AU', 'CA', 'OTHER')),
                    CHECK (list_type IN ('INDIVIDUAL', 'ENTITY', 'VESSEL', 'AIRCRAFT')),
                    CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL'))
                )
            ''')
            
            # ========== SCREENING RESULTS TABLE ==========
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS screening_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    screening_id VARCHAR(30) UNIQUE NOT NULL,
                    customer_code VARCHAR(20) NOT NULL,
                    screening_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    screening_type VARCHAR(20) NOT NULL,
                    total_matches INTEGER DEFAULT 0,
                    exact_matches INTEGER DEFAULT 0,
                    partial_matches INTEGER DEFAULT 0,
                    highest_match_score DECIMAL(5,2),
                    risk_score INTEGER DEFAULT 0,
                    risk_level VARCHAR(20),
                    screening_result VARCHAR(20) NOT NULL,
                    reviewed_by VARCHAR(50),
                    review_date TIMESTAMP,
                    review_notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (customer_code) REFERENCES customers(customer_code) ON DELETE CASCADE,
                    CHECK (screening_type IN ('ONBOARDING', 'PERIODIC', 'AD_HOC', 'BATCH')),
                    CHECK (risk_level IN ('VERY_LOW', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
                    CHECK (screening_result IN ('CLEAR', 'CLEAR_WITH_WARNING', 'REVIEW_REQUIRED', 'REJECTED', 'PENDING'))
                )
            ''')
            
            # ========== SANCTION MATCHES TABLE ==========
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS sanction_matches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    screening_id VARCHAR(30) NOT NULL,
                    customer_code VARCHAR(20) NOT NULL,
                    sanction_id INTEGER NOT NULL,
                    match_type VARCHAR(20) NOT NULL,
                    match_score DECIMAL(5,2) NOT NULL,
                    name_match_score DECIMAL(5,2),
                    dob_match_score DECIMAL(5,2),
                    nationality_match_score DECIMAL(5,2),
                    id_match_score DECIMAL(5,2),
                    matched_fields TEXT,
                    match_details TEXT,
                    risk_level VARCHAR(20),
                    recommended_action VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (screening_id) REFERENCES screening_results(screening_id) ON DELETE CASCADE,
                    FOREIGN KEY (sanction_id) REFERENCES sanctions(id) ON DELETE CASCADE,
                    CHECK (match_type IN ('EXACT', 'PARTIAL', 'FUZZY', 'NO_MATCH')),
                    CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL'))
                )
            ''')
            
            # ========== AUDIT LOG TABLE ==========
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action_type VARCHAR(50) NOT NULL,
                    entity_type VARCHAR(50),
                    entity_id VARCHAR(50),
                    user_id VARCHAR(50),
                    ip_address VARCHAR(50),
                    user_agent TEXT,
                    details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            self.conn.commit()
            logger.info("✅ Database tables created successfully")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"❌ Error creating database tables: {e}")
            self.conn.rollback()
            return False
    
    def load_sample_sanctions(self) -> bool:
        """
        Load sample sanctions data for demonstration purposes
        
        Returns:
            bool: True if data loaded successfully, False otherwise
        """
        if not self.connected:
            logger.error("❌ Cannot load sample data: No active connection")
            return False
        
        try:
            # Check if sanctions table already has data
            self.cursor.execute("SELECT COUNT(*) FROM sanctions")
            count = self.cursor.fetchone()[0]
            
            if count > 0:
                logger.info(f"✅ Sanctions table already contains {count} records")
                return True
            
            # Sample sanctions data
            sample_sanctions = [
                # OFAC SDN List entries
                ('OFAC', 'INDIVIDUAL', 'SDN12345', 'أحمد علي المصري', 'Ahmed Ali Al-Masri',
                 'أحمد المصري', 'Ahmed Al-Masri', 'EG', 'Egypt', '1980-05-15', 'Cairo',
                 'PASSPORT', 'A12345678', 'Terrorism Financing', 'Involved in terrorism financing activities',
                 '2020-01-15', None, None, None, 'SDN12345', 'HIGH'),
                
                ('OFAC', 'INDIVIDUAL', 'SDN12346', 'محمد حسن', 'Mohamed Hassan',
                 '', '', 'SY', 'Syria', '1975-11-22', 'Damascus',
                 'PASSPORT', 'S78901234', 'Supporting Regime', 'Supporting human rights violations',
                 '2019-03-10', None, None, None, 'SDN12346', 'HIGH'),
                
                # UN Sanctions List entries
                ('UN', 'INDIVIDUAL', 'UN12345', 'إيفان بتروف', 'Ivan Petrov',
                 'إيفان الروسي', 'Ivan the Russian', 'RU', 'Russia', '1970-08-30', 'Moscow',
                 'PASSPORT', 'R34567890', 'Arms Trafficking', 'Illegal arms trade',
                 '2021-06-20', None, 'UNSCR 2374', None, None, 'HIGH'),
                
                # EU Consolidated List entries
                ('EU', 'ENTITY', 'EU12345', 'مجموعة الإرهاب أ', 'Terror Group A',
                 'تنظيم أ', 'Group A', 'SY', 'Syria', None, None,
                 None, None, 'Terrorist Organization', 'Terrorism activities',
                 '2018-09-05', None, None, 'EU Regulation 2020/123', None, 'HIGH'),
                
                ('EU', 'INDIVIDUAL', 'EU12346', 'خوان كارلوس', 'Juan Carlos',
                 '', '', 'MX', 'Mexico', '1965-04-12', 'Mexico City',
                 'PASSPORT', 'M56789012', 'Drug Trafficking', 'Narcotics distribution network',
                 '2022-02-28', None, None, 'EU Regulation 2021/456', None, 'HIGH'),
            ]
            
            # Insert sample data
            self.cursor.executemany('''
                INSERT INTO sanctions 
                (list_source, list_type, reference_id, full_name_ar, full_name_en,
                 alias_ar, alias_en, nationality_code, nationality_name, date_of_birth,
                 place_of_birth, id_type, id_number, designation, reason,
                 effective_date, expiry_date, un_resolution, eu_regulation, ofac_id, risk_level)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', sample_sanctions)
            
            self.conn.commit()
            logger.info(f"✅ Successfully loaded {len(sample_sanctions)} sample sanctions")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"❌ Error loading sample sanctions: {e}")
            self.conn.rollback()
            return False
    
    def add_customer(self, customer_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Add a new customer to the database
        
        Args:
            customer_data (dict): Dictionary containing customer information
        
        Returns:
            tuple: (success, message) where success is bool and message is str
        """
        if not self.connected:
            return False, "Database not connected"
        
        try:
            # Validate required fields
            required_fields = ['customer_code', 'full_name_en', 'nationality_code', 'id_number']
            for field in required_fields:
                if field not in customer_data or not customer_data[field]:
                    return False, f"Missing required field: {field}"
            
            # Check for duplicate ID number
            self.cursor.execute(
                "SELECT COUNT(*) FROM customers WHERE id_number = ?",
                (customer_data['id_number'],)
            )
            if self.cursor.fetchone()[0] > 0:
                return False, "ID number already exists in database"
            
            # Check for duplicate customer code
            self.cursor.execute(
                "SELECT COUNT(*) FROM customers WHERE customer_code = ?",
                (customer_data['customer_code'],)
            )
            if self.cursor.fetchone()[0] > 0:
                return False, "Customer code already exists"
            
            # Prepare data for insertion
            columns = []
            values = []
            placeholders = []
            
            for key, value in customer_data.items():
                if value is not None:
                    columns.append(key)
                    values.append(value)
                    placeholders.append('?')
            
            # Build and execute insert query
            query = f'''
                INSERT INTO customers ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
            '''
            
            self.cursor.execute(query, values)
            customer_id = self.cursor.lastrowid
            
            # Log the action
            self._log_audit_action(
                action_type='CREATE_CUSTOMER',
                entity_type='CUSTOMER',
                entity_id=customer_data['customer_code'],
                details=f"Added new customer: {customer_data.get('full_name_en')}"
            )
            
            self.conn.commit()
            logger.info(f"✅ Customer added successfully: {customer_data.get('full_name_en')}")
            return True, "Customer added successfully"
            
        except sqlite3.Error as e:
            self.conn.rollback()
            error_msg = f"Database error: {str(e)}"
            logger.error(f"❌ Error adding customer: {error_msg}")
            return False, error_msg
    
    def get_customer(self, customer_code: str) -> Optional[Dict]:
        """
        Retrieve customer information by customer code
        
        Args:
            customer_code (str): Unique customer identifier
        
        Returns:
            dict: Customer information or None if not found
        """
        if not self.connected:
            return None
        
        try:
            self.cursor.execute('''
                SELECT * FROM customers WHERE customer_code = ?
            ''', (customer_code,))
            
            row = self.cursor.fetchone()
            if row:
                return dict(row)
            return None
            
        except sqlite3.Error as e:
            logger.error(f"❌ Error retrieving customer: {e}")
            return None
    
    def search_sanctions(self, search_term: str, threshold: int = 70) -> List[Dict]:
        """
        Search sanctions list by name or alias
        
        Args:
            search_term (str): Search term (name, alias, etc.)
            threshold (int): Minimum match threshold (0-100)
        
        Returns:
            list: List of matching sanctions
        """
        if not self.connected:
            return []
        
        try:
            query = '''
                SELECT * FROM sanctions 
                WHERE full_name_en LIKE ? 
                   OR full_name_ar LIKE ? 
                   OR alias_en LIKE ? 
                   OR alias_ar LIKE ?
                ORDER BY risk_level DESC, full_name_en
                LIMIT 50
            '''
            
            search_pattern = f"%{search_term}%"
            self.cursor.execute(query, (search_pattern, search_pattern, 
                                       search_pattern, search_pattern))
            
            results = []
            for row in self.cursor.fetchall():
                results.append(dict(row))
            
            logger.info(f"🔍 Found {len(results)} sanctions for search term: '{search_term}'")
            return results
            
        except sqlite3.Error as e:
            logger.error(f"❌ Error searching sanctions: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics
        
        Returns:
            dict: Dictionary containing various statistics
        """
        stats = {}
        
        if not self.connected:
            return stats
        
        try:
            # Basic counts
            tables = ['customers', 'sanctions', 'screening_results', 'sanction_matches']
            for table in tables:
                self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[f'total_{table}'] = self.cursor.fetchone()[0]
            
            # Customer risk distribution
            self.cursor.execute('''
                SELECT risk_category, COUNT(*) as count 
                FROM customers 
                GROUP BY risk_category
            ''')
            stats['risk_distribution'] = dict(self.cursor.fetchall())
            
            # Sanctions by source
            self.cursor.execute('''
                SELECT list_source, COUNT(*) as count 
                FROM sanctions 
                GROUP BY list_source
            ''')
            stats['sanctions_by_source'] = dict(self.cursor.fetchall())
            
            # Screening results distribution
            self.cursor.execute('''
                SELECT screening_result, COUNT(*) as count 
                FROM screening_results 
                GROUP BY screening_result
            ''')
            stats['screening_results'] = dict(self.cursor.fetchall())
            
            # Recent activity
            self.cursor.execute('''
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM customers
                WHERE created_at >= DATE('now', '-30 days')
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            ''')
            stats['recent_activity'] = dict(self.cursor.fetchall())
            
            return stats
            
        except sqlite3.Error as e:
            logger.error(f"❌ Error getting statistics: {e}")
            return {}
    
    def export_to_csv(self, table_name: str, output_file: str) -> bool:
        """
        Export a table to CSV file
        
        Args:
            table_name (str): Name of the table to export
            output_file (str): Path to output CSV file
        
        Returns:
            bool: True if export successful, False otherwise
        """
        if not self.connected:
            return False
        
        try:
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", self.conn)
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            logger.info(f"✅ Exported {table_name} to {output_file}")
            return True
        except Exception as e:
            logger.error(f"❌ Error exporting to CSV: {e}")
            return False
    
    def _log_audit_action(self, action_type: str, entity_type: str = None, 
                         entity_id: str = None, details: str = None) -> None:
        """
        Log an action to the audit log
        
        Args:
            action_type (str): Type of action performed
            entity_type (str): Type of entity affected
            entity_id (str): ID of entity affected
            details (str): Additional details
        """
        try:
            self.cursor.execute('''
                INSERT INTO audit_log (action_type, entity_type, entity_id, details)
                VALUES (?, ?, ?, ?)
            ''', (action_type, entity_type, entity_id, details))
        except Exception as e:
            logger.error(f"❌ Error logging audit action: {e}")
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()

# Utility function for quick database access
def get_database_connection():
    """Get a database connection for quick operations"""
    db = KYCDatabase()
    if db.connect():
        return db
    return None