"""
Mock Salesforce Data Generator

Generates realistic CRM data with proper referential integrity.
This simulates what you'd get from the Salesforce API.

Key concepts for data engineers:
1. Natural keys (Salesforce IDs) vs surrogate keys (we add these in dbt)
2. Referential integrity across tables
3. Realistic data distributions (not uniform random)
4. Temporal patterns that match real business behavior
"""

import os
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
from faker import Faker

# Initialize Faker for realistic names, companies, etc.
fake = Faker()
Faker.seed(42)  # Reproducible data
random.seed(42)


# =============================================================================
# CONFIGURATION
# =============================================================================

# How much data to generate
NUM_USERS = 25          # Sales reps
NUM_ACCOUNTS = 200      # Companies
NUM_CONTACTS = 500      # People at companies
NUM_LEADS = 300         # Prospects not yet qualified
NUM_CAMPAIGNS = 50      # Marketing campaigns
NUM_PRODUCTS = 10       # Products you sell
NUM_OPPORTUNITIES = 800 # Deals
NUM_ACTIVITIES = 2000   # Tasks, calls, emails

# Date range for data
START_DATE = datetime(2023, 1, 1)
END_DATE = datetime(2025, 1, 15)

# Salesforce-style 18-character IDs
def generate_sf_id(prefix: str) -> str:
    """
    Generate a Salesforce-style ID.
    Real SF IDs are 15 or 18 chars, case-sensitive/insensitive.
    We'll use a simplified version for clarity.
    """
    return f"{prefix}{''.join(random.choices('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz', k=15))}"


# =============================================================================
# DATA MODELS (matching Salesforce object structure)
# =============================================================================

@dataclass
class User:
    """Salesforce User object - your sales reps"""
    Id: str
    Name: str
    Email: str
    Username: str
    Department: str
    UserRoleId: str
    ManagerId: str  # Can be None for top-level
    IsActive: bool
    CreatedDate: str

@dataclass
class Account:
    """Salesforce Account object - companies you sell to"""
    Id: str
    Name: str
    Industry: str
    Type: str  # Customer, Prospect, Partner
    NumberOfEmployees: int
    AnnualRevenue: float
    BillingStreet: str
    BillingCity: str
    BillingState: str
    BillingPostalCode: str
    BillingCountry: str
    OwnerId: str  # FK to User
    CreatedDate: str
    LastModifiedDate: str

@dataclass
class Contact:
    """Salesforce Contact object - people at accounts"""
    Id: str
    AccountId: str  # FK to Account
    FirstName: str
    LastName: str
    Email: str
    Phone: str
    Title: str
    Department: str
    LeadSource: str
    OwnerId: str  # FK to User
    CreatedDate: str

@dataclass
class Product:
    """Salesforce Product2 object - what you sell"""
    Id: str
    Name: str
    ProductCode: str
    Family: str
    Description: str
    IsActive: bool
    CreatedDate: str

@dataclass
class PricebookEntry:
    """Salesforce PricebookEntry - product pricing"""
    Id: str
    Product2Id: str  # FK to Product
    UnitPrice: float
    IsActive: bool

@dataclass
class Opportunity:
    """Salesforce Opportunity object - deals in your pipeline"""
    Id: str
    AccountId: str  # FK to Account
    Name: str
    StageName: str
    Amount: float
    Probability: int
    CloseDate: str
    Type: str  # New Business, Renewal, Upsell
    LeadSource: str
    OwnerId: str  # FK to User
    IsClosed: bool
    IsWon: bool
    CreatedDate: str
    LastModifiedDate: str

@dataclass
class OpportunityLineItem:
    """Products attached to opportunities"""
    Id: str
    OpportunityId: str  # FK to Opportunity
    Product2Id: str     # FK to Product
    Quantity: int
    UnitPrice: float
    TotalPrice: float

@dataclass
class Task:
    """Salesforce Task object - activities"""
    Id: str
    WhoId: str        # FK to Contact (optional)
    WhatId: str       # FK to Account or Opportunity
    OwnerId: str      # FK to User
    Subject: str
    Status: str
    Priority: str
    Type: str         # Call, Email, Meeting, Other
    ActivityDate: str
    Description: str
    CallDurationInSeconds: int
    CreatedDate: str

@dataclass
class Campaign:
    """Salesforce Campaign object - marketing campaigns"""
    Id: str
    Name: str
    Type: str              # Email, Webinar, Conference, etc.
    Status: str            # Planned, In Progress, Completed, Aborted
    StartDate: str         # Date (YYYY-MM-DD)
    EndDate: str           # Date (YYYY-MM-DD)
    IsActive: bool
    Description: str
    BudgetedCost: float
    ActualCost: float
    ExpectedRevenue: float
    NumberSent: int        # Number of contacts/leads targeted
    ParentId: str          # FK to parent Campaign (can be None)
    OwnerId: str           # FK to User
    CreatedDate: str
    LastModifiedDate: str
    IsDeleted: bool

@dataclass
class CampaignMember:
    """
    Salesforce CampaignMember object - junction between Campaign and Lead/Contact

    CRITICAL: Either ContactId OR LeadId must be populated, never both.
    This represents a person's membership in a campaign.
    """
    Id: str
    CampaignId: str        # FK to Campaign (required)
    LeadId: str            # FK to Lead (optional - either this OR ContactId)
    ContactId: str         # FK to Contact (optional - either this OR LeadId)
    Status: str            # Sent, Responded, etc. (campaign-specific)
    HasResponded: bool
    CreatedDate: str
    LastModifiedDate: str

@dataclass
class Lead:
    """
    Salesforce Lead object - prospects not yet qualified

    Leads are converted to Account/Contact/Opportunity when qualified.
    """
    Id: str
    LastName: str
    FirstName: str
    Company: str           # Required field
    Title: str
    Email: str
    Phone: str
    Status: str            # Open, Contacted, Qualified, Unqualified, etc.
    Rating: str            # Hot, Warm, Cold
    LeadSource: str        # Web, Referral, etc.
    Industry: str
    AnnualRevenue: float
    NumberOfEmployees: int
    Street: str
    City: str
    State: str
    PostalCode: str
    Country: str
    Description: str
    OwnerId: str           # FK to User
    # Conversion tracking fields
    IsConverted: bool
    ConvertedAccountId: str   # FK to Account (populated after conversion)
    ConvertedContactId: str   # FK to Contact (populated after conversion)
    ConvertedOpportunityId: str  # FK to Opportunity (populated after conversion)
    ConvertedDate: str     # When lead was converted
    CreatedDate: str
    LastModifiedDate: str
    IsDeleted: bool


# =============================================================================
# REFERENCE DATA (realistic values)
# =============================================================================

INDUSTRIES = [
    'Technology', 'Healthcare', 'Financial Services', 'Manufacturing',
    'Retail', 'Education', 'Media', 'Professional Services',
    'Energy', 'Transportation', 'Real Estate', 'Hospitality'
]

# Weighted distribution - most companies are in a few industries
INDUSTRY_WEIGHTS = [0.20, 0.15, 0.15, 0.10, 0.10, 0.08, 0.05, 0.05, 0.04, 0.03, 0.03, 0.02]

ACCOUNT_TYPES = ['Prospect', 'Customer', 'Partner']
ACCOUNT_TYPE_WEIGHTS = [0.50, 0.40, 0.10]

DEPARTMENTS = ['Sales', 'Sales', 'Sales', 'Sales Development', 'Account Management']

TITLES = [
    'CEO', 'CTO', 'CFO', 'VP Engineering', 'VP Sales', 'VP Marketing',
    'Director of IT', 'Director of Operations', 'Product Manager',
    'Engineering Manager', 'Software Engineer', 'Data Analyst',
    'Marketing Manager', 'Sales Manager', 'Account Executive'
]

LEAD_SOURCES = [
    'Web', 'Referral', 'Partner', 'Conference', 'Advertisement',
    'Cold Call', 'Email Campaign', 'Social Media'
]
LEAD_SOURCE_WEIGHTS = [0.25, 0.20, 0.15, 0.12, 0.10, 0.08, 0.05, 0.05]

# Opportunity stages with probabilities (standard Salesforce)
STAGES = [
    ('Prospecting', 10),
    ('Qualification', 20),
    ('Needs Analysis', 40),
    ('Value Proposition', 60),
    ('Negotiation', 80),
    ('Closed Won', 100),
    ('Closed Lost', 0)
]

OPPORTUNITY_TYPES = ['New Business', 'Renewal', 'Upsell', 'Cross-sell']
OPPORTUNITY_TYPE_WEIGHTS = [0.45, 0.30, 0.15, 0.10]

TASK_TYPES = ['Call', 'Email', 'Meeting', 'Demo', 'Follow-up', 'Other']
TASK_STATUSES = ['Not Started', 'In Progress', 'Completed', 'Deferred']
TASK_PRIORITIES = ['High', 'Normal', 'Low']

PRODUCT_FAMILIES = ['Software', 'Services', 'Support', 'Training']

CAMPAIGN_TYPES = [
    'Email', 'Webinar', 'Conference', 'Trade Show',
    'Direct Mail', 'Advertisement', 'Telemarketing', 'Partners'
]
CAMPAIGN_TYPE_WEIGHTS = [0.25, 0.20, 0.15, 0.10, 0.10, 0.08, 0.07, 0.05]

CAMPAIGN_STATUSES = ['Planned', 'In Progress', 'Completed', 'Aborted']

CAMPAIGN_MEMBER_STATUSES = ['Sent', 'Responded', 'Attended', 'No Show']

LEAD_STATUSES = [
    'Open - Not Contacted', 'Working - Contacted', 'Closed - Converted',
    'Closed - Not Converted'
]

LEAD_RATINGS = ['Hot', 'Warm', 'Cold']


# =============================================================================
# DATA GENERATORS
# =============================================================================

def random_date(start: datetime, end: datetime) -> datetime:
    """Generate a random date between start and end."""
    delta = end - start
    random_days = random.randint(0, delta.days)
    return start + timedelta(days=random_days)


def random_date_weighted_quarter_end(start: datetime, end: datetime) -> datetime:
    """
    Generate dates with quarter-end bias (hockey stick effect).
    Real sales data clusters at quarter ends.
    """
    date = random_date(start, end)
    # 30% chance to move to quarter end
    if random.random() < 0.30:
        month = date.month
        # Find quarter end month
        quarter_end_month = ((month - 1) // 3 + 1) * 3
        # Last week of quarter
        if quarter_end_month == 12:
            date = date.replace(month=12, day=random.randint(20, 31))
        else:
            date = date.replace(month=quarter_end_month, day=random.randint(20, 28))
    return date


def generate_users() -> List[User]:
    """Generate sales team users with manager hierarchy."""
    users = []

    # Create a manager first
    manager_id = generate_sf_id('005')
    manager = User(
        Id=manager_id,
        Name=fake.name(),
        Email=fake.company_email(),
        Username=fake.user_name() + '@company.com',
        Department='Sales',
        UserRoleId=generate_sf_id('00E'),
        ManagerId=None,  # Top level
        IsActive=True,
        CreatedDate=(START_DATE - timedelta(days=365)).isoformat()
    )
    users.append(manager)

    # Create sales reps reporting to manager
    for i in range(NUM_USERS - 1):
        user = User(
            Id=generate_sf_id('005'),
            Name=fake.name(),
            Email=fake.company_email(),
            Username=fake.user_name() + '@company.com',
            Department=random.choice(DEPARTMENTS),
            UserRoleId=generate_sf_id('00E'),
            ManagerId=manager_id,
            IsActive=random.random() > 0.1,  # 10% inactive
            CreatedDate=random_date(START_DATE - timedelta(days=365), END_DATE).isoformat()
        )
        users.append(user)

    return users


def generate_accounts(users: List[User]) -> List[Account]:
    """Generate company accounts owned by users."""
    accounts = []
    active_users = [u for u in users if u.IsActive]

    for i in range(NUM_ACCOUNTS):
        # Company size distribution (log-normal - many small, few large)
        employees = int(max(10, random.lognormvariate(5, 1.5)))
        employees = min(employees, 100000)  # Cap at 100k

        # Revenue correlates with employees
        revenue = employees * random.uniform(50000, 200000)

        created = random_date(START_DATE, END_DATE)

        account = Account(
            Id=generate_sf_id('001'),
            Name=fake.company(),
            Industry=random.choices(INDUSTRIES, weights=INDUSTRY_WEIGHTS)[0],
            Type=random.choices(ACCOUNT_TYPES, weights=ACCOUNT_TYPE_WEIGHTS)[0],
            NumberOfEmployees=employees,
            AnnualRevenue=round(revenue, 2),
            BillingStreet=fake.street_address(),
            BillingCity=fake.city(),
            BillingState=fake.state_abbr(),
            BillingPostalCode=fake.postcode(),
            BillingCountry='USA',
            OwnerId=random.choice(active_users).Id,
            CreatedDate=created.isoformat(),
            LastModifiedDate=(created + timedelta(days=random.randint(0, 30))).isoformat()
        )
        accounts.append(account)

    return accounts


def generate_contacts(accounts: List[Account], users: List[User]) -> List[Contact]:
    """Generate contacts at accounts."""
    contacts = []
    active_users = [u for u in users if u.IsActive]

    for account in accounts:
        # Larger accounts have more contacts
        num_contacts = random.randint(1, min(5, max(1, account.NumberOfEmployees // 100)))

        for i in range(num_contacts):
            contact = Contact(
                Id=generate_sf_id('003'),
                AccountId=account.Id,
                FirstName=fake.first_name(),
                LastName=fake.last_name(),
                Email=fake.company_email(),
                Phone=fake.phone_number(),
                Title=random.choice(TITLES),
                Department=random.choice(['Engineering', 'IT', 'Operations', 'Finance', 'Marketing', 'Sales']),
                LeadSource=random.choices(LEAD_SOURCES, weights=LEAD_SOURCE_WEIGHTS)[0],
                OwnerId=account.OwnerId,  # Same owner as account
                CreatedDate=account.CreatedDate  # Created with account
            )
            contacts.append(contact)

    return contacts


def generate_products() -> tuple[List[Product], List[PricebookEntry]]:
    """Generate products and their price book entries."""
    products = []
    pricebook_entries = []

    product_names = [
        ('Enterprise Platform', 'Software', 'ENT-001', 50000),
        ('Professional Suite', 'Software', 'PRO-001', 15000),
        ('Starter Package', 'Software', 'STR-001', 5000),
        ('Implementation Services', 'Services', 'SVC-IMP', 25000),
        ('Custom Development', 'Services', 'SVC-DEV', 10000),
        ('Premium Support', 'Support', 'SUP-PRM', 12000),
        ('Standard Support', 'Support', 'SUP-STD', 5000),
        ('Admin Training', 'Training', 'TRN-ADM', 2000),
        ('Developer Training', 'Training', 'TRN-DEV', 3000),
        ('Data Migration', 'Services', 'SVC-MIG', 8000),
    ]

    for name, family, code, base_price in product_names:
        product_id = generate_sf_id('01t')

        product = Product(
            Id=product_id,
            Name=name,
            ProductCode=code,
            Family=family,
            Description=f"{name} - {family} offering",
            IsActive=True,
            CreatedDate=START_DATE.isoformat()
        )
        products.append(product)

        # Price book entry
        pbe = PricebookEntry(
            Id=generate_sf_id('01u'),
            Product2Id=product_id,
            UnitPrice=base_price,
            IsActive=True
        )
        pricebook_entries.append(pbe)

    return products, pricebook_entries


def generate_opportunities(
    accounts: List[Account],
    users: List[User],
    products: List[Product],
    pricebook_entries: List[PricebookEntry]
) -> tuple[List[Opportunity], List[OpportunityLineItem]]:
    """
    Generate opportunities with realistic distributions.

    Key insight: Deal amounts follow a log-normal distribution.
    Most deals are small, few are large. This is critical for
    realistic pipeline analytics.
    """
    opportunities = []
    line_items = []
    active_users = [u for u in users if u.IsActive]

    # Create price lookup
    product_prices = {pbe.Product2Id: pbe.UnitPrice for pbe in pricebook_entries}

    for i in range(NUM_OPPORTUNITIES):
        account = random.choice(accounts)
        created_date = random_date(START_DATE, END_DATE - timedelta(days=30))

        # Deal size based on account size (log-normal)
        base_amount = random.lognormvariate(9, 1.2)  # Mean ~$10k, long tail
        # Larger accounts = larger deals
        size_multiplier = 1 + (account.NumberOfEmployees / 10000)
        amount = round(base_amount * size_multiplier, 2)
        amount = max(1000, min(amount, 500000))  # Bound between $1k and $500k

        # Determine stage and closed status
        # Older opportunities more likely to be closed
        days_old = (END_DATE - created_date).days

        if days_old > 180:  # Old deals
            if random.random() < 0.8:  # 80% are closed
                stage, prob = random.choice([STAGES[5], STAGES[6]])  # Won or Lost
                is_closed = True
                is_won = (stage == 'Closed Won')
            else:
                stage, prob = random.choice(STAGES[:5])
                is_closed = False
                is_won = False
        elif days_old > 90:  # Medium age
            if random.random() < 0.5:  # 50% closed
                stage, prob = random.choice([STAGES[5], STAGES[6]])
                is_closed = True
                is_won = (stage == 'Closed Won')
            else:
                stage, prob = random.choice(STAGES[2:5])  # Later stages
                is_closed = False
                is_won = False
        else:  # New deals
            stage, prob = random.choice(STAGES[:4])  # Earlier stages
            is_closed = False
            is_won = False

        # Win rate varies by deal size (smaller deals close faster)
        if is_closed and amount > 100000:
            # Large deals have lower win rate
            if random.random() < 0.3:
                stage = 'Closed Lost'
                is_won = False
                prob = 0

        # Close date
        if is_closed:
            close_date = created_date + timedelta(days=random.randint(30, 180))
        else:
            close_date = random_date_weighted_quarter_end(
                datetime.now(),
                datetime.now() + timedelta(days=180)
            )

        opp_id = generate_sf_id('006')

        opportunity = Opportunity(
            Id=opp_id,
            AccountId=account.Id,
            Name=f"{account.Name} - {random.choice(['New', 'Expansion', 'Renewal'])}",
            StageName=stage,
            Amount=amount,
            Probability=prob,
            CloseDate=close_date.strftime('%Y-%m-%d'),
            Type=random.choices(OPPORTUNITY_TYPES, weights=OPPORTUNITY_TYPE_WEIGHTS)[0],
            LeadSource=random.choices(LEAD_SOURCES, weights=LEAD_SOURCE_WEIGHTS)[0],
            OwnerId=random.choice(active_users).Id,
            IsClosed=is_closed,
            IsWon=is_won,
            CreatedDate=created_date.isoformat(),
            LastModifiedDate=(created_date + timedelta(days=random.randint(1, 60))).isoformat()
        )
        opportunities.append(opportunity)

        # Generate line items (products on this deal)
        num_products = random.randint(1, 3)
        selected_products = random.sample(products, min(num_products, len(products)))

        remaining_amount = amount
        for j, product in enumerate(selected_products):
            if j == len(selected_products) - 1:
                # Last item gets remaining amount
                item_amount = remaining_amount
            else:
                item_amount = round(remaining_amount * random.uniform(0.2, 0.5), 2)
                remaining_amount -= item_amount

            unit_price = product_prices.get(product.Id, 10000)
            quantity = max(1, int(item_amount / unit_price))

            line_item = OpportunityLineItem(
                Id=generate_sf_id('00k'),
                OpportunityId=opp_id,
                Product2Id=product.Id,
                Quantity=quantity,
                UnitPrice=unit_price,
                TotalPrice=round(quantity * unit_price, 2)
            )
            line_items.append(line_item)

    return opportunities, line_items


def generate_activities(
    accounts: List[Account],
    contacts: List[Contact],
    opportunities: List[Opportunity],
    users: List[User]
) -> List[Task]:
    """
    Generate activity data (tasks, calls, emails).

    Pattern: More activities on accounts with opportunities,
    clustering around opportunity close dates.
    """
    tasks = []
    active_users = [u for u in users if u.IsActive]

    # Create lookup for contacts by account
    contacts_by_account = {}
    for contact in contacts:
        if contact.AccountId not in contacts_by_account:
            contacts_by_account[contact.AccountId] = []
        contacts_by_account[contact.AccountId].append(contact)

    # Create lookup for opportunities by account
    opps_by_account = {}
    for opp in opportunities:
        if opp.AccountId not in opps_by_account:
            opps_by_account[opp.AccountId] = []
        opps_by_account[opp.AccountId].append(opp)

    # Generate activities weighted toward accounts with opps
    for i in range(NUM_ACTIVITIES):
        # 70% of activities on accounts with opportunities
        if random.random() < 0.7 and opps_by_account:
            account = random.choice([a for a in accounts if a.Id in opps_by_account])
        else:
            account = random.choice(accounts)

        # Get a contact if available
        contact = None
        if account.Id in contacts_by_account:
            contact = random.choice(contacts_by_account[account.Id])

        # Activity date - cluster around opportunity dates if exists
        if account.Id in opps_by_account:
            opp = random.choice(opps_by_account[account.Id])
            base_date = datetime.fromisoformat(opp.CreatedDate.replace('Z', ''))
            activity_date = base_date + timedelta(days=random.randint(-30, 90))
        else:
            activity_date = random_date(START_DATE, END_DATE)

        task_type = random.choice(TASK_TYPES)

        # Call duration only for calls
        duration = 0
        if task_type == 'Call':
            duration = random.randint(60, 3600)  # 1-60 minutes

        subjects = {
            'Call': ['Discovery call', 'Follow-up call', 'Demo prep call', 'Pricing discussion'],
            'Email': ['Sent proposal', 'Follow-up email', 'Meeting confirmation', 'Contract review'],
            'Meeting': ['On-site meeting', 'Quarterly review', 'Executive briefing', 'Technical deep dive'],
            'Demo': ['Product demo', 'Technical demo', 'POC review', 'Feature walkthrough'],
            'Follow-up': ['Post-meeting follow-up', 'Check-in', 'Next steps', 'Status update'],
            'Other': ['Research', 'Internal sync', 'Admin task', 'Documentation']
        }

        task = Task(
            Id=generate_sf_id('00T'),
            WhoId=contact.Id if contact else None,
            WhatId=account.Id,
            OwnerId=random.choice(active_users).Id,
            Subject=random.choice(subjects.get(task_type, subjects['Other'])),
            Status=random.choice(TASK_STATUSES),
            Priority=random.choice(TASK_PRIORITIES),
            Type=task_type,
            ActivityDate=activity_date.strftime('%Y-%m-%d'),
            Description=fake.sentence(),
            CallDurationInSeconds=duration,
            CreatedDate=activity_date.isoformat()
        )
        tasks.append(task)

    return tasks


def generate_campaigns(users: List[User]) -> List[Campaign]:
    """
    Generate marketing campaigns owned by users.

    Pattern: Mix of completed past campaigns and active/planned future ones.
    Larger campaigns have higher budgets and expected revenue.
    """
    campaigns = []
    active_users = [u for u in users if u.IsActive]

    # Generate parent campaigns first (10% are parent campaigns)
    num_parent_campaigns = max(1, NUM_CAMPAIGNS // 10)
    parent_campaign_ids = []

    for i in range(num_parent_campaigns):
        campaign_id = generate_sf_id('701')
        parent_campaign_ids.append(campaign_id)

        created_date = random_date(START_DATE - timedelta(days=180), END_DATE - timedelta(days=90))
        start_date = created_date + timedelta(days=random.randint(7, 30))
        end_date = start_date + timedelta(days=random.randint(30, 180))

        # Determine if campaign is completed
        is_completed = end_date < datetime.now()
        if is_completed:
            status = random.choice(['Completed', 'Aborted']) if random.random() < 0.9 else 'Completed'
        elif start_date > datetime.now():
            status = 'Planned'
        else:
            status = 'In Progress'

        # Budget based on campaign type
        budgeted_cost = random.randint(5000, 100000)
        actual_cost = budgeted_cost * random.uniform(0.7, 1.2) if is_completed else 0
        expected_revenue = budgeted_cost * random.uniform(2, 8)  # 2-8x ROI target

        campaign = Campaign(
            Id=campaign_id,
            Name=f"Q{random.randint(1,4)} {random.choice(['2024', '2025'])} {random.choice(['Growth', 'Awareness', 'Demand Gen', 'Product Launch'])}",
            Type=random.choices(CAMPAIGN_TYPES, weights=CAMPAIGN_TYPE_WEIGHTS)[0],
            Status=status,
            StartDate=start_date.strftime('%Y-%m-%d'),
            EndDate=end_date.strftime('%Y-%m-%d'),
            IsActive=(status == 'In Progress'),
            Description=fake.sentence(),
            BudgetedCost=round(budgeted_cost, 2),
            ActualCost=round(actual_cost, 2),
            ExpectedRevenue=round(expected_revenue, 2),
            NumberSent=random.randint(100, 5000),
            ParentId=None,  # Parent campaigns have no parent
            OwnerId=random.choice(active_users).Id,
            CreatedDate=created_date.isoformat(),
            LastModifiedDate=(created_date + timedelta(days=random.randint(1, 30))).isoformat(),
            IsDeleted=False
        )
        campaigns.append(campaign)

    # Generate child campaigns (rest are children)
    for i in range(NUM_CAMPAIGNS - num_parent_campaigns):
        campaign_id = generate_sf_id('701')

        created_date = random_date(START_DATE, END_DATE - timedelta(days=30))
        start_date = created_date + timedelta(days=random.randint(7, 30))
        duration = random.randint(7, 90)
        end_date = start_date + timedelta(days=duration)

        is_completed = end_date < datetime.now()
        if is_completed:
            status = random.choice(['Completed', 'Aborted']) if random.random() < 0.9 else 'Completed'
        elif start_date > datetime.now():
            status = 'Planned'
        else:
            status = 'In Progress'

        campaign_type = random.choices(CAMPAIGN_TYPES, weights=CAMPAIGN_TYPE_WEIGHTS)[0]

        # Smaller budgets for child campaigns
        budgeted_cost = random.randint(1000, 50000)
        actual_cost = budgeted_cost * random.uniform(0.7, 1.2) if is_completed else 0
        expected_revenue = budgeted_cost * random.uniform(2, 8)

        campaign = Campaign(
            Id=campaign_id,
            Name=f"{campaign_type} - {fake.catch_phrase()}",
            Type=campaign_type,
            Status=status,
            StartDate=start_date.strftime('%Y-%m-%d'),
            EndDate=end_date.strftime('%Y-%m-%d'),
            IsActive=(status == 'In Progress'),
            Description=fake.sentence(),
            BudgetedCost=round(budgeted_cost, 2),
            ActualCost=round(actual_cost, 2),
            ExpectedRevenue=round(expected_revenue, 2),
            NumberSent=random.randint(50, 2000),
            ParentId=random.choice(parent_campaign_ids) if random.random() < 0.5 else None,
            OwnerId=random.choice(active_users).Id,
            CreatedDate=created_date.isoformat(),
            LastModifiedDate=(created_date + timedelta(days=random.randint(1, 30))).isoformat(),
            IsDeleted=False
        )
        campaigns.append(campaign)

    return campaigns


def generate_leads(users: List[User]) -> List[Lead]:
    """
    Generate leads (prospects not yet in the system as accounts/contacts).

    Key pattern: Some leads are converted (have ConvertedAccountId, etc.),
    most are still being worked.
    """
    leads = []
    active_users = [u for u in users if u.IsActive]

    for i in range(NUM_LEADS):
        created_date = random_date(START_DATE, END_DATE)

        # 30% of leads are converted (became customers)
        is_converted = random.random() < 0.30

        if is_converted:
            status = 'Closed - Converted'
            converted_date = created_date + timedelta(days=random.randint(7, 90))
            # We'll populate these with real IDs in a post-processing step
            # For now, generate placeholder IDs
            converted_account_id = generate_sf_id('001')
            converted_contact_id = generate_sf_id('003')
            converted_opportunity_id = generate_sf_id('006') if random.random() < 0.8 else None
        else:
            status = random.choice(LEAD_STATUSES[:2])  # Open or Working
            converted_date = None
            converted_account_id = None
            converted_contact_id = None
            converted_opportunity_id = None

        # Company size (log-normal like accounts)
        employees = int(max(10, random.lognormvariate(4, 1.5)))
        employees = min(employees, 50000)
        revenue = employees * random.uniform(50000, 200000)

        lead = Lead(
            Id=generate_sf_id('00Q'),
            FirstName=fake.first_name(),
            LastName=fake.last_name(),
            Company=fake.company(),
            Title=random.choice(TITLES),
            Email=fake.company_email(),
            Phone=fake.phone_number(),
            Status=status,
            Rating=random.choice(LEAD_RATINGS),
            LeadSource=random.choices(LEAD_SOURCES, weights=LEAD_SOURCE_WEIGHTS)[0],
            Industry=random.choices(INDUSTRIES, weights=INDUSTRY_WEIGHTS)[0],
            AnnualRevenue=round(revenue, 2),
            NumberOfEmployees=employees,
            Street=fake.street_address(),
            City=fake.city(),
            State=fake.state_abbr(),
            PostalCode=fake.postcode(),
            Country='USA',
            Description=fake.sentence(),
            OwnerId=random.choice(active_users).Id,
            IsConverted=is_converted,
            ConvertedAccountId=converted_account_id,
            ConvertedContactId=converted_contact_id,
            ConvertedOpportunityId=converted_opportunity_id,
            ConvertedDate=converted_date.strftime('%Y-%m-%d') if converted_date else None,
            CreatedDate=created_date.isoformat(),
            LastModifiedDate=(created_date + timedelta(days=random.randint(1, 30))).isoformat(),
            IsDeleted=False
        )
        leads.append(lead)

    return leads


def generate_campaign_members(
    campaigns: List[Campaign],
    leads: List[Lead],
    contacts: List[Contact]
) -> List[CampaignMember]:
    """
    Generate campaign memberships.

    CRITICAL PATTERN: Each member must have EITHER LeadId OR ContactId, never both.
    This junction table links people (leads/contacts) to campaigns.

    Pattern: Completed campaigns have more members. Email campaigns have
    highest member counts.
    """
    campaign_members = []

    # Create lookup for unconverted leads (these are still leads, not contacts)
    unconverted_leads = [l for l in leads if not l.IsConverted]

    for campaign in campaigns:
        # Determine number of members based on campaign type and status
        if campaign.Status == 'Completed':
            base_members = campaign.NumberSent
        else:
            base_members = int(campaign.NumberSent * random.uniform(0.3, 0.7))

        # Adjust by type (Email campaigns have more members)
        if campaign.Type == 'Email':
            num_members = min(base_members, len(contacts) + len(unconverted_leads))
        elif campaign.Type == 'Webinar':
            num_members = min(int(base_members * 0.5), len(contacts) + len(unconverted_leads))
        else:
            num_members = min(int(base_members * 0.3), len(contacts) + len(unconverted_leads))

        # Split between contacts (70%) and leads (30%)
        num_contacts = int(num_members * 0.70)
        num_leads = num_members - num_contacts

        # Add contacts to campaign
        selected_contacts = random.sample(contacts, min(num_contacts, len(contacts)))
        for contact in selected_contacts:
            created = datetime.fromisoformat(campaign.CreatedDate.replace('Z', ''))

            # Response rate varies by campaign type
            if campaign.Type in ['Email', 'Webinar']:
                has_responded = random.random() < 0.15  # 15% response rate
            elif campaign.Type == 'Conference':
                has_responded = random.random() < 0.40  # 40% attendance
            else:
                has_responded = random.random() < 0.10

            if has_responded:
                status = random.choice(['Responded', 'Attended'])
            else:
                status = 'Sent'

            member = CampaignMember(
                Id=generate_sf_id('00v'),
                CampaignId=campaign.Id,
                LeadId=None,  # This is a contact, not a lead
                ContactId=contact.Id,
                Status=status,
                HasResponded=has_responded,
                CreatedDate=created.isoformat(),
                LastModifiedDate=(created + timedelta(days=random.randint(0, 7))).isoformat()
            )
            campaign_members.append(member)

        # Add leads to campaign
        selected_leads = random.sample(unconverted_leads, min(num_leads, len(unconverted_leads)))
        for lead in selected_leads:
            created = datetime.fromisoformat(campaign.CreatedDate.replace('Z', ''))

            has_responded = random.random() < 0.12  # Leads respond slightly less

            if has_responded:
                status = random.choice(['Responded', 'Attended'])
            else:
                status = 'Sent'

            member = CampaignMember(
                Id=generate_sf_id('00v'),
                CampaignId=campaign.Id,
                LeadId=lead.Id,
                ContactId=None,  # This is a lead, not a contact
                Status=status,
                HasResponded=has_responded,
                CreatedDate=created.isoformat(),
                LastModifiedDate=(created + timedelta(days=random.randint(0, 7))).isoformat()
            )
            campaign_members.append(member)

    return campaign_members


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def save_to_json(data: List[Any], filename: str, output_dir: str) -> None:
    """Save data to JSON file (simulating Salesforce API response format)."""
    filepath = os.path.join(output_dir, filename)
    records = [asdict(record) for record in data]

    # Salesforce API response format
    output = {
        "totalSize": len(records),
        "done": True,
        "records": records
    }

    with open(filepath, 'w') as f:
        json.dump(output, f, indent=2, default=str)

    print(f"  Saved {len(records)} records to {filename}")


def main():
    """Generate all mock Salesforce data."""
    output_dir = os.path.join(os.path.dirname(__file__), '../../data/raw')
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 60)
    print("MOCK SALESFORCE DATA GENERATOR")
    print("=" * 60)
    print(f"\nGenerating data for date range: {START_DATE.date()} to {END_DATE.date()}")
    print(f"Output directory: {output_dir}\n")

    # Generate in dependency order (referential integrity)
    print("Generating Users...")
    users = generate_users()
    save_to_json(users, 'users.json', output_dir)

    print("Generating Accounts...")
    accounts = generate_accounts(users)
    save_to_json(accounts, 'accounts.json', output_dir)

    print("Generating Contacts...")
    contacts = generate_contacts(accounts, users)
    save_to_json(contacts, 'contacts.json', output_dir)

    print("Generating Leads...")
    leads = generate_leads(users)
    save_to_json(leads, 'leads.json', output_dir)

    print("Generating Campaigns...")
    campaigns = generate_campaigns(users)
    save_to_json(campaigns, 'campaigns.json', output_dir)

    print("Generating Products...")
    products, pricebook_entries = generate_products()
    save_to_json(products, 'products.json', output_dir)
    save_to_json(pricebook_entries, 'pricebook_entries.json', output_dir)

    print("Generating Opportunities...")
    opportunities, line_items = generate_opportunities(accounts, users, products, pricebook_entries)
    save_to_json(opportunities, 'opportunities.json', output_dir)
    save_to_json(line_items, 'opportunity_line_items.json', output_dir)

    print("Generating Campaign Members...")
    campaign_members = generate_campaign_members(campaigns, leads, contacts)
    save_to_json(campaign_members, 'campaign_members.json', output_dir)

    print("Generating Activities...")
    tasks = generate_activities(accounts, contacts, opportunities, users)
    save_to_json(tasks, 'tasks.json', output_dir)

    print("\n" + "=" * 60)
    print("DATA GENERATION COMPLETE")
    print("=" * 60)
    print(f"""
Summary:
  Users:              {len(users):,}
  Accounts:           {len(accounts):,}
  Contacts:           {len(contacts):,}
  Leads:              {len(leads):,}
  Campaigns:          {len(campaigns):,}
  Campaign Members:   {len(campaign_members):,}
  Products:           {len(products):,}
  Opportunities:      {len(opportunities):,}
  Line Items:         {len(line_items):,}
  Activities:         {len(tasks):,}

Files written to: {output_dir}
""")


if __name__ == '__main__':
    main()
