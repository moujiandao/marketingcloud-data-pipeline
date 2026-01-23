"""
PostgreSQL Data Loader

Loads JSON data from Salesforce extraction into PostgreSQL raw schema.

Key Production Patterns:
1. Idempotent loading - Safe to run multiple times
2. Schema separation - Raw data isolated from transformed data
3. UPSERT pattern - INSERT ON CONFLICT for graceful handling
4. Transaction management - Atomic operations
5. Connection pooling - Efficient resource usage
"""

import os
import json
import psycopg2
from psycopg2.extras import execute_values
from typing import List, Dict, Any
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection parameters
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': os.getenv('POSTGRES_PORT', '5432'),
    'database': os.getenv('POSTGRES_DB', 'salesforce_dw'),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', 'postgres')
}


class PostgresLoader:
    """
    Handles loading data into PostgreSQL with proper error handling
    and idempotent operations.
    """

    def __init__(self, config: Dict[str, str]):
        self.config = config
        self.conn = None
        self.cursor = None

    def connect(self):
        """Establish database connection."""
        try:
            self.conn = psycopg2.connect(**self.config)
            self.cursor = self.conn.cursor()
            print(f"✓ Connected to PostgreSQL: {self.config['database']}")
        except Exception as e:
            print(f"✗ Failed to connect to PostgreSQL: {e}")
            raise

    def close(self):
        """Close database connection."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            print("✓ Database connection closed")

    def create_schemas(self):
        """
        Create schemas for data layers.

        Schema separation is critical for:
        - Organizing data by processing stage
        - Access control (different teams need different schemas)
        - Clear data lineage
        """
        schemas = ['raw', 'staging', 'intermediate', 'marts']

        for schema in schemas:
            self.cursor.execute(f"""
                CREATE SCHEMA IF NOT EXISTS {schema};
            """)

        self.conn.commit()
        print(f"✓ Created schemas: {', '.join(schemas)}")

    def create_raw_tables(self):
        """
        Create raw tables matching Salesforce object structure.

        Design decisions:
        - Use TEXT for IDs (Salesforce IDs are 15-18 chars)
        - Use JSONB for flexibility with changing schemas
        - Add metadata columns (loaded_at, source_file)
        - Primary key on Salesforce Id for idempotent loads
        """

        # User table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS raw.users (
                id TEXT PRIMARY KEY,
                name TEXT,
                email TEXT,
                username TEXT,
                department TEXT,
                user_role_id TEXT,
                manager_id TEXT,
                is_active BOOLEAN,
                created_date TIMESTAMP,
                -- Metadata
                loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                raw_data JSONB
            );
        """)

        # Account table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS raw.accounts (
                id TEXT PRIMARY KEY,
                name TEXT,
                industry TEXT,
                type TEXT,
                number_of_employees INTEGER,
                annual_revenue NUMERIC(15,2),
                billing_street TEXT,
                billing_city TEXT,
                billing_state TEXT,
                billing_postal_code TEXT,
                billing_country TEXT,
                owner_id TEXT,
                created_date TIMESTAMP,
                last_modified_date TIMESTAMP,
                -- Metadata
                loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                raw_data JSONB
            );
        """)

        # Contact table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS raw.contacts (
                id TEXT PRIMARY KEY,
                account_id TEXT,
                first_name TEXT,
                last_name TEXT,
                email TEXT,
                phone TEXT,
                title TEXT,
                department TEXT,
                lead_source TEXT,
                owner_id TEXT,
                created_date TIMESTAMP,
                -- Metadata
                loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                raw_data JSONB
            );
        """)

        # Lead table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS raw.leads (
                id TEXT PRIMARY KEY,
                last_name TEXT,
                first_name TEXT,
                company TEXT,
                title TEXT,
                email TEXT,
                phone TEXT,
                status TEXT,
                rating TEXT,
                lead_source TEXT,
                industry TEXT,
                annual_revenue NUMERIC(15,2),
                number_of_employees INTEGER,
                street TEXT,
                city TEXT,
                state TEXT,
                postal_code TEXT,
                country TEXT,
                description TEXT,
                owner_id TEXT,
                is_converted BOOLEAN,
                converted_account_id TEXT,
                converted_contact_id TEXT,
                converted_opportunity_id TEXT,
                converted_date DATE,
                created_date TIMESTAMP,
                last_modified_date TIMESTAMP,
                is_deleted BOOLEAN,
                -- Metadata
                loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                raw_data JSONB
            );
        """)

        # Campaign table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS raw.campaigns (
                id TEXT PRIMARY KEY,
                name TEXT,
                type TEXT,
                status TEXT,
                start_date DATE,
                end_date DATE,
                is_active BOOLEAN,
                description TEXT,
                budgeted_cost NUMERIC(15,2),
                actual_cost NUMERIC(15,2),
                expected_revenue NUMERIC(15,2),
                number_sent INTEGER,
                parent_id TEXT,
                owner_id TEXT,
                created_date TIMESTAMP,
                last_modified_date TIMESTAMP,
                is_deleted BOOLEAN,
                -- Metadata
                loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                raw_data JSONB
            );
        """)

        # CampaignMember table (junction table)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS raw.campaign_members (
                id TEXT PRIMARY KEY,
                campaign_id TEXT,
                lead_id TEXT,
                contact_id TEXT,
                status TEXT,
                has_responded BOOLEAN,
                created_date TIMESTAMP,
                last_modified_date TIMESTAMP,
                -- Metadata
                loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                raw_data JSONB,
                -- Constraint: Either lead_id OR contact_id must be set, not both
                CONSTRAINT campaign_member_check
                    CHECK ((lead_id IS NOT NULL AND contact_id IS NULL) OR
                           (lead_id IS NULL AND contact_id IS NOT NULL))
            );
        """)

        # Product table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS raw.products (
                id TEXT PRIMARY KEY,
                name TEXT,
                product_code TEXT,
                family TEXT,
                description TEXT,
                is_active BOOLEAN,
                created_date TIMESTAMP,
                -- Metadata
                loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                raw_data JSONB
            );
        """)

        # PricebookEntry table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS raw.pricebook_entries (
                id TEXT PRIMARY KEY,
                product2_id TEXT,
                unit_price NUMERIC(15,2),
                is_active BOOLEAN,
                -- Metadata
                loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                raw_data JSONB
            );
        """)

        # Opportunity table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS raw.opportunities (
                id TEXT PRIMARY KEY,
                account_id TEXT,
                name TEXT,
                stage_name TEXT,
                amount NUMERIC(15,2),
                probability INTEGER,
                close_date DATE,
                type TEXT,
                lead_source TEXT,
                owner_id TEXT,
                is_closed BOOLEAN,
                is_won BOOLEAN,
                created_date TIMESTAMP,
                last_modified_date TIMESTAMP,
                -- Metadata
                loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                raw_data JSONB
            );
        """)

        # OpportunityLineItem table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS raw.opportunity_line_items (
                id TEXT PRIMARY KEY,
                opportunity_id TEXT,
                product2_id TEXT,
                quantity INTEGER,
                unit_price NUMERIC(15,2),
                total_price NUMERIC(15,2),
                -- Metadata
                loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                raw_data JSONB
            );
        """)

        # Task table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS raw.tasks (
                id TEXT PRIMARY KEY,
                who_id TEXT,
                what_id TEXT,
                owner_id TEXT,
                subject TEXT,
                status TEXT,
                priority TEXT,
                type TEXT,
                activity_date DATE,
                description TEXT,
                call_duration_in_seconds INTEGER,
                created_date TIMESTAMP,
                -- Metadata
                loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                raw_data JSONB
            );
        """)

        self.conn.commit()
        print("✓ Created raw tables")

    def load_json_file(self, filepath: str, table_name: str, field_mapping: Dict[str, str]):
        """
        Load JSON file into PostgreSQL table using UPSERT pattern.

        Args:
            filepath: Path to JSON file
            table_name: Target table in raw schema
            field_mapping: Map of PostgreSQL column -> JSON field

        UPSERT Pattern:
        INSERT ... ON CONFLICT DO UPDATE is idempotent.
        - First run: Inserts all records
        - Second run: Updates records if they exist
        - No duplicates, no errors
        """

        # Read JSON file
        with open(filepath, 'r') as f:
            data = json.load(f)

        records = data.get('records', [])
        if not records:
            print(f"  ⚠ No records in {filepath}")
            return

        # Build INSERT statement with UPSERT
        columns = list(field_mapping.keys()) + ['raw_data']
        columns_str = ', '.join(columns)
        placeholders = ', '.join(['%s'] * len(columns))

        # ON CONFLICT clause for idempotency
        update_clause = ', '.join([
            f"{col} = EXCLUDED.{col}" for col in columns if col != 'id'
        ])

        insert_sql = f"""
            INSERT INTO raw.{table_name} ({columns_str})
            VALUES %s
            ON CONFLICT (id) DO UPDATE SET
                {update_clause},
                loaded_at = CURRENT_TIMESTAMP
        """

        # Prepare values
        values = []
        for record in records:
            row = []
            for pg_column, json_field in field_mapping.items():
                value = record.get(json_field)
                # Handle NULL values properly
                if value == '' or value == 'null':
                    value = None
                row.append(value)
            # Add raw JSONB
            row.append(json.dumps(record))
            values.append(tuple(row))

        # Execute batch insert
        execute_values(
            self.cursor,
            insert_sql,
            values,
            template=f"({placeholders})",
            page_size=1000  # Batch size for performance
        )

        self.conn.commit()
        print(f"  ✓ Loaded {len(records):,} records into raw.{table_name}")

    def load_all_data(self, data_dir: str):
        """Load all JSON files from data directory."""

        # Define field mappings for each object
        # Format: 'postgres_column': 'SalesforceField'

        mappings = {
            'users.json': {
                'table': 'users',
                'fields': {
                    'id': 'Id',
                    'name': 'Name',
                    'email': 'Email',
                    'username': 'Username',
                    'department': 'Department',
                    'user_role_id': 'UserRoleId',
                    'manager_id': 'ManagerId',
                    'is_active': 'IsActive',
                    'created_date': 'CreatedDate'
                }
            },
            'accounts.json': {
                'table': 'accounts',
                'fields': {
                    'id': 'Id',
                    'name': 'Name',
                    'industry': 'Industry',
                    'type': 'Type',
                    'number_of_employees': 'NumberOfEmployees',
                    'annual_revenue': 'AnnualRevenue',
                    'billing_street': 'BillingStreet',
                    'billing_city': 'BillingCity',
                    'billing_state': 'BillingState',
                    'billing_postal_code': 'BillingPostalCode',
                    'billing_country': 'BillingCountry',
                    'owner_id': 'OwnerId',
                    'created_date': 'CreatedDate',
                    'last_modified_date': 'LastModifiedDate'
                }
            },
            'contacts.json': {
                'table': 'contacts',
                'fields': {
                    'id': 'Id',
                    'account_id': 'AccountId',
                    'first_name': 'FirstName',
                    'last_name': 'LastName',
                    'email': 'Email',
                    'phone': 'Phone',
                    'title': 'Title',
                    'department': 'Department',
                    'lead_source': 'LeadSource',
                    'owner_id': 'OwnerId',
                    'created_date': 'CreatedDate'
                }
            },
            'leads.json': {
                'table': 'leads',
                'fields': {
                    'id': 'Id',
                    'last_name': 'LastName',
                    'first_name': 'FirstName',
                    'company': 'Company',
                    'title': 'Title',
                    'email': 'Email',
                    'phone': 'Phone',
                    'status': 'Status',
                    'rating': 'Rating',
                    'lead_source': 'LeadSource',
                    'industry': 'Industry',
                    'annual_revenue': 'AnnualRevenue',
                    'number_of_employees': 'NumberOfEmployees',
                    'street': 'Street',
                    'city': 'City',
                    'state': 'State',
                    'postal_code': 'PostalCode',
                    'country': 'Country',
                    'description': 'Description',
                    'owner_id': 'OwnerId',
                    'is_converted': 'IsConverted',
                    'converted_account_id': 'ConvertedAccountId',
                    'converted_contact_id': 'ConvertedContactId',
                    'converted_opportunity_id': 'ConvertedOpportunityId',
                    'converted_date': 'ConvertedDate',
                    'created_date': 'CreatedDate',
                    'last_modified_date': 'LastModifiedDate',
                    'is_deleted': 'IsDeleted'
                }
            },
            'campaigns.json': {
                'table': 'campaigns',
                'fields': {
                    'id': 'Id',
                    'name': 'Name',
                    'type': 'Type',
                    'status': 'Status',
                    'start_date': 'StartDate',
                    'end_date': 'EndDate',
                    'is_active': 'IsActive',
                    'description': 'Description',
                    'budgeted_cost': 'BudgetedCost',
                    'actual_cost': 'ActualCost',
                    'expected_revenue': 'ExpectedRevenue',
                    'number_sent': 'NumberSent',
                    'parent_id': 'ParentId',
                    'owner_id': 'OwnerId',
                    'created_date': 'CreatedDate',
                    'last_modified_date': 'LastModifiedDate',
                    'is_deleted': 'IsDeleted'
                }
            },
            'campaign_members.json': {
                'table': 'campaign_members',
                'fields': {
                    'id': 'Id',
                    'campaign_id': 'CampaignId',
                    'lead_id': 'LeadId',
                    'contact_id': 'ContactId',
                    'status': 'Status',
                    'has_responded': 'HasResponded',
                    'created_date': 'CreatedDate',
                    'last_modified_date': 'LastModifiedDate'
                }
            },
            'products.json': {
                'table': 'products',
                'fields': {
                    'id': 'Id',
                    'name': 'Name',
                    'product_code': 'ProductCode',
                    'family': 'Family',
                    'description': 'Description',
                    'is_active': 'IsActive',
                    'created_date': 'CreatedDate'
                }
            },
            'pricebook_entries.json': {
                'table': 'pricebook_entries',
                'fields': {
                    'id': 'Id',
                    'product2_id': 'Product2Id',
                    'unit_price': 'UnitPrice',
                    'is_active': 'IsActive'
                }
            },
            'opportunities.json': {
                'table': 'opportunities',
                'fields': {
                    'id': 'Id',
                    'account_id': 'AccountId',
                    'name': 'Name',
                    'stage_name': 'StageName',
                    'amount': 'Amount',
                    'probability': 'Probability',
                    'close_date': 'CloseDate',
                    'type': 'Type',
                    'lead_source': 'LeadSource',
                    'owner_id': 'OwnerId',
                    'is_closed': 'IsClosed',
                    'is_won': 'IsWon',
                    'created_date': 'CreatedDate',
                    'last_modified_date': 'LastModifiedDate'
                }
            },
            'opportunity_line_items.json': {
                'table': 'opportunity_line_items',
                'fields': {
                    'id': 'Id',
                    'opportunity_id': 'OpportunityId',
                    'product2_id': 'Product2Id',
                    'quantity': 'Quantity',
                    'unit_price': 'UnitPrice',
                    'total_price': 'TotalPrice'
                }
            },
            'tasks.json': {
                'table': 'tasks',
                'fields': {
                    'id': 'Id',
                    'who_id': 'WhoId',
                    'what_id': 'WhatId',
                    'owner_id': 'OwnerId',
                    'subject': 'Subject',
                    'status': 'Status',
                    'priority': 'Priority',
                    'type': 'Type',
                    'activity_date': 'ActivityDate',
                    'description': 'Description',
                    'call_duration_in_seconds': 'CallDurationInSeconds',
                    'created_date': 'CreatedDate'
                }
            }
        }

        print("\nLoading data files:")
        for filename, config in mappings.items():
            filepath = os.path.join(data_dir, filename)
            if not os.path.exists(filepath):
                print(f"  ⚠ File not found: {filename}")
                continue

            self.load_json_file(filepath, config['table'], config['fields'])


def main():
    """Main execution function."""
    print("=" * 60)
    print("POSTGRESQL DATA LOADER")
    print("=" * 60)
    print()

    # Data directory
    data_dir = os.path.join(os.path.dirname(__file__), '../../data/raw')

    # Initialize loader
    loader = PostgresLoader(DB_CONFIG)

    try:
        # Connect to database
        loader.connect()

        # Create schemas
        print("\n1. Creating schemas...")
        loader.create_schemas()

        # Create tables
        print("\n2. Creating raw tables...")
        loader.create_raw_tables()

        # Load data
        print("\n3. Loading data...")
        loader.load_all_data(data_dir)

        print("\n" + "=" * 60)
        print("LOAD COMPLETE")
        print("=" * 60)
        print("\nYou can now query the data:")
        print("  psql salesforce_dw -c 'SELECT COUNT(*) FROM raw.accounts;'")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        raise

    finally:
        loader.close()


if __name__ == '__main__':
    main()
