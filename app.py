import streamlit as st
import sqlite3
import hashlib
import json
from datetime import datetime, timedelta
import requests
import os
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import re
from urllib.parse import urlparse, parse_qs

# Page configuration
st.set_page_config(
    page_title="RealEstateGuru",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'dashboard'
if 'current_module' not in st.session_state:
    st.session_state.current_module = None
if 'show_register' not in st.session_state:
    st.session_state.show_register = False
if 'user_points' not in st.session_state:
    st.session_state.user_points = 0
if 'user_badges' not in st.session_state:
    st.session_state.user_badges = []
if 'quiz_score' not in st.session_state:
    st.session_state.quiz_score = 0
if 'current_question' not in st.session_state:
    st.session_state.current_question = 0
if 'quiz_answers' not in st.session_state:
    st.session_state.quiz_answers = {}
if 'quiz_started' not in st.session_state:
    st.session_state.quiz_started = False

# Database setup
DATABASE_PATH = "realestate_guru.db"

def migrate_database():
    """Migrate existing database to add missing columns"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if points column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'points' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN points INTEGER DEFAULT 0")
            
        if 'badges' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN badges TEXT DEFAULT '[]'")
            
        if 'streak_days' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN streak_days INTEGER DEFAULT 0")
        
        # Check if youtube_url column exists in modules
        cursor.execute("PRAGMA table_info(modules)")
        module_columns = [col[1] for col in cursor.fetchall()]
        
        if 'youtube_url' not in module_columns:
            cursor.execute("ALTER TABLE modules ADD COLUMN youtube_url TEXT")
        
        conn.commit()
        print("Database migration completed successfully")
        
    except Exception as e:
        print(f"Migration error: {e}")
    finally:
        conn.close()
migrate_database()   
def init_database():
    """Initialize database with comprehensive tables and content"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Create users table with all required columns
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'student',
            created_date TEXT NOT NULL,
            last_login TEXT,
            active INTEGER DEFAULT 1,
            points INTEGER DEFAULT 0,
            badges TEXT DEFAULT '[]',
            streak_days INTEGER DEFAULT 0
        )
    """)
    
    # Create modules table with all required columns
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS modules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            difficulty TEXT NOT NULL,
            category TEXT NOT NULL,
            content TEXT,
            youtube_url TEXT,
            order_index INTEGER DEFAULT 0,
            created_date TEXT NOT NULL,
            updated_date TEXT,
            active INTEGER DEFAULT 1
        )
    """)
    
    # Create quizzes table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module_id INTEGER NOT NULL,
            question TEXT NOT NULL,
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT NOT NULL,
            option_d TEXT NOT NULL,
            correct_answer TEXT NOT NULL,
            explanation TEXT,
            created_date TEXT NOT NULL,
            FOREIGN KEY (module_id) REFERENCES modules (id)
        )
    """)
    
    # Create user progress table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            module_id INTEGER NOT NULL,
            progress_percentage REAL DEFAULT 0,
            completed INTEGER DEFAULT 0,
            started_date TEXT,
            completed_date TEXT,
            quiz_score REAL DEFAULT 0,
            quiz_attempts INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (module_id) REFERENCES modules (id)
        )
    """)
    
    # Create user achievements table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            achievement_type TEXT NOT NULL,
            achievement_name TEXT NOT NULL,
            points_earned INTEGER DEFAULT 0,
            earned_date TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    # Create content research table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS content_research (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            content TEXT NOT NULL,
            sources TEXT NOT NULL,
            created_date TEXT NOT NULL,
            status TEXT DEFAULT 'pending'
        )
    """)
    
    # Insert default admin user if doesn't exist
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
    admin_count = cursor.fetchone()[0]
    
    if admin_count == 0:
        admin_password = hashlib.sha256("admin123".encode()).hexdigest()
        cursor.execute("""
            INSERT INTO users (username, email, password, role, created_date, points, badges, streak_days)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, ("admin", "admin@realestateguruapp.com", admin_password, "admin", datetime.now().isoformat(), 1000, '["Admin Master", "System Creator"]', 1))
    
    # Insert comprehensive modules with rich content if they don't exist
    cursor.execute("SELECT COUNT(*) FROM modules")
    module_count = cursor.fetchone()[0]
    
    if module_count == 0:
        # Module 1: Real Estate Fundamentals
        fundamentals_content = """
# Real Estate Fundamentals

## 1. Introduction to Real Estate

Real estate encompasses **land and any permanent structures** attached to it, including buildings, homes, and other improvements. In India, real estate is governed by various central and state laws.

### Key Definitions:
- **Immovable Property**: Land, buildings, and anything attached to the earth
- **Movable Property**: Furniture, fixtures that can be removed
- **Freehold**: Absolute ownership of land and building
- **Leasehold**: Right to use property for specified period

## 2. Market Stakeholders

### Primary Stakeholders:
- **Developers**: Create new properties
- **Buyers/Investors**: Purchase for residence or investment
- **Brokers/Agents**: Facilitate transactions
- **Financial Institutions**: Provide funding
- **Government Bodies**: Regulate and approve

### Regulatory Bodies:
- **RERA**: Real Estate Regulatory Authority
- **Municipal Corporations**: Local approvals
- **State Housing Boards**: Affordable housing
- **SEBI**: REITs regulation

## 3. Property Types

### Residential:
- Apartments/Flats
- Independent Houses/Villas
- Row Houses/Townhouses
- Studio Apartments

### Commercial:
- Office Spaces
- Retail Outlets
- Warehouses
- Mixed-Use Developments

### Industrial:
- Manufacturing Units
- IT Parks
- Special Economic Zones (SEZ)

## 4. Market Dynamics

The Indian real estate market is valued at over **$200 billion** and growing at 6-8% annually. Key growth drivers include urbanization, rising incomes, and government initiatives like Housing for All.

### Current Trends:
- **Affordable Housing**: Government focus on sub-₹30 lakh homes
- **Smart Cities**: 100 smart cities mission
- **Green Buildings**: IGBC and GRIHA certifications
- **PropTech**: Digital platforms transforming transactions

## 5. Investment Basics

### Key Factors to Consider:
- **Location**: Connectivity and infrastructure
- **Legal Clearances**: Proper documentation
- **Builder Reputation**: Track record and credibility
- **Market Timing**: Entry and exit strategies

### Risk Factors:
- **Market Volatility**: Price fluctuations
- **Regulatory Changes**: Policy impacts
- **Liquidity Constraints**: Time to sell
- **Quality Issues**: Construction defects
"""

        # Module 2: Legal Framework & RERA
        rera_content = """
# Legal Framework & RERA

## 1. Real Estate (Regulation and Development) Act, 2016

RERA was enacted to protect homebuyer interests and promote transparency in real estate transactions.

### Key Objectives:
- **Protect Homebuyer Rights**: Timely delivery and quality construction
- **Increase Transparency**: Mandatory project disclosures
- **Establish Accountability**: Developer penalties for non-compliance
- **Boost Investor Confidence**: Structured regulatory framework

## 2. RERA Registration Requirements

### For Developers:
- Projects with **8+ units or 500+ sq.m** must register
- Deposit **70% of receivables** in escrow account
- Submit quarterly progress reports
- Provide 5-year structural warranty

### For Real Estate Agents:
- Mandatory registration with state RERA
- Professional conduct standards
- Commission structure transparency

## 3. Homebuyer Rights Under RERA

### Delivery Rights:
- **Compensation** for delayed possession
- **Interest** on advance payments if project delayed
- **Refund** option with interest if developer fails

### Quality Rights:
- **5-year warranty** on structural defects
- **Right to inspect** during construction
- **Defect liability** for common areas

### Information Rights:
- **Project details** on RERA website
- **Financial information** including approvals
- **Timeline updates** through quarterly reports

## 4. RERA Complaint Process

### Steps to File Complaint:
1. **Gather Documents**: Sale agreement, payment receipts, correspondence
2. **Visit RERA Website**: Access state RERA portal
3. **File Online**: Submit complaint with supporting documents
4. **Pay Fees**: Nominal filing fees required
5. **Attend Hearing**: Appear before RERA authority
6. **Get Order**: Receive binding decision

### Common Complaint Types:
- **Delivery Delays**: Non-adherence to possession timelines
- **Quality Issues**: Construction defects and poor workmanship
- **Hidden Charges**: Undisclosed fees and costs
- **Misleading Advertisements**: False promises and claims

## 5. Penalties and Compliance

### Developer Penalties:
- **Interest Payment**: 10% per annum for delays
- **Project Deregistration**: For serious violations
- **Criminal Action**: For fraudulent practices
- **Compensation Orders**: Monetary relief to buyers

### Compliance Requirements:
- **Quarterly Reports**: Progress and financial updates
- **Escrow Maintenance**: 70% fund allocation
- **Quality Standards**: BIS and approved specifications
- **Timely Completion**: As per registered timeline
"""

        # Module 3: Property Measurements & Standards
        measurements_content = """
# Property Measurements & Standards

## 1. Understanding Property Areas

### Carpet Area:
- **Definition**: Actual usable floor area within walls
- **Includes**: Rooms, kitchen, bathrooms, balconies
- **Excludes**: Walls, common areas, utility shafts
- **Legal Standard**: RERA mandates sales based on carpet area only

### Built-up Area:
- **Formula**: Carpet Area + Wall Thickness + Balcony Area
- **Includes**: Interior walls and columns within apartment
- **Typical Addition**: 10-15% over carpet area
- **Usage**: Internal planning and design calculations

### Super Built-up Area:
- **Formula**: Built-up Area + Proportionate Common Area
- **Includes**: Lobbies, elevators, staircases, amenities
- **Typical Addition**: 25-40% over carpet area
- **Note**: No longer legally valid for sales post-RERA

## 2. BIS Standards for Measurement (IS 3861:2002)

### Measurement Principles:
- **Wall-to-Wall**: Carpet area measured from inner wall faces
- **Balcony Calculation**: 50% weightage in carpet area
- **Common Areas**: Pro-rata distribution basis
- **Accuracy Standards**: ±2% tolerance allowed

### Loading Factor:
- **Definition**: Percentage difference between super built-up and carpet area
- **Formula**: (Super Built-up - Carpet) / Carpet × 100
- **Typical Range**: 15-40% depending on project type
- **Impact**: Affects actual usable space per rupee

## 3. Floor Plan Reading Skills

### Basic Elements:
- **Walls**: Thick black lines showing structure
- **Doors**: Breaks in walls with swing direction
- **Windows**: Double lines with glass indication
- **Fixtures**: Kitchen, bathroom, electrical symbols

### Room Analysis:
- **Dimensions**: Length × Width in feet/meters
- **Proportions**: Square vs. rectangular layouts
- **Natural Light**: Window placement and sizes
- **Ventilation**: Cross-ventilation possibilities

### Common Symbols:
- **WC**: Water closet/toilet
- **K**: Kitchen area
- **BR**: Bedroom
- **LR**: Living room
- **DB**: Distribution board
- **AC**: Air conditioning provision

## 4. Measurement Verification

### For Buyers:
- **Independent Survey**: Hire qualified surveyor
- **Dimension Check**: Verify all room measurements
- **Area Calculations**: Cross-check developer calculations
- **Document Deviations**: Record any differences found

### Red Flags:
- **Area Shortfall**: Actual less than promised
- **Layout Changes**: Unauthorized plan modifications
- **Quality Variations**: Substandard construction materials
- **Hidden Deductions**: Undisclosed area exclusions

## 5. Legal Remedies for Discrepancies

### RERA Provisions:
- **Area Compensation**: Refund for shortfall areas
- **Interest Payment**: On excess amount paid
- **Project Completion**: Force adherence to approved plans
- **Quality Standards**: Ensure BIS compliance

### Calculation Example:
If carpet area promised: 1000 sq.ft
If carpet area delivered: 950 sq.ft
Shortfall: 50 sq.ft (5%)
Compensation: (50/1000) × Total Amount Paid
"""

        # Module 4: Valuation & Finance
        valuation_content = """
# Property Valuation & Finance

## 1. Property Valuation Methods

### Comparative Market Analysis (CMA):
- **Methodology**: Compare with similar recent sales
- **Key Factors**: Location, size, age, amenities, condition
- **Data Sources**: Registration records, broker databases, online platforms
- **Accuracy Range**: ±10-15% in established markets
- **Best Applications**: Residential properties in active markets

### Income Approach:
- **Formula**: Property Value = Net Operating Income ÷ Capitalization Rate
- **Components**: 
  - Gross Rental Income
  - Operating Expenses (maintenance, taxes, management)
  - Capitalization Rate (market-derived)
- **Applications**: Investment properties, commercial buildings
- **Yield Calculations**:
  - Gross Rental Yield = (Annual Rent ÷ Property Price) × 100
  - Net Rental Yield = (Annual Rent - Expenses) ÷ Property Price × 100

### Cost Approach:
- **Formula**: Land Value + Building Cost - Depreciation
- **Components**:
  - Current land rates in the area
  - Construction cost per sq.ft
  - Age-based depreciation (2-3% annually)
- **Applications**: New constructions, unique properties, insurance valuations
- **Depreciation Factors**: Physical deterioration, functional obsolescence, economic factors

## 2. Factors Affecting Property Values

### Location Factors (Weight: 40-50%):
- **Connectivity**: Metro, highways, airports proximity
- **Social Infrastructure**: Schools, hospitals, shopping centers
- **Employment Hubs**: IT parks, business districts, industrial areas
- **Future Development**: Planned infrastructure projects

### Property-Specific Factors (Weight: 30-40%):
- **Size and Layout**: Carpet area, room configuration
- **Floor and Facing**: Higher floors, east/north facing premium
- **Age and Condition**: Newer properties command premium
- **Amenities**: Swimming pool, gym, security, parking

### Market Factors (Weight: 10-20%):
- **Supply-Demand**: Inventory levels vs. absorption rates
- **Interest Rates**: Impact on affordability and demand
- **Government Policies**: Tax benefits, subsidies, regulations
- **Economic Conditions**: Employment levels, income growth

## 3. Home Loan Fundamentals

### Loan-to-Value (LTV) Ratio:
- **Definition**: Loan amount as percentage of property value
- **Typical Ranges**:
  - Properties up to ₹30 lakh: 90% LTV
  - Properties ₹30-75 lakh: 80% LTV
  - Properties above ₹75 lakh: 75% LTV
- **Down Payment**: 100% - LTV ratio
- **Higher LTV Criteria**: First-time buyers, salaried professionals

### Interest Rate Structures:
- **Fixed Rate**: Constant throughout loan tenure (9-11% currently)
- **Floating Rate**: Varies with market conditions (8.5-10.5% currently)
- **Hybrid**: Fixed for initial years, then floating
- **Factors Affecting Rates**: Credit score, income, property type, loan amount

### EMI Calculation:
**Formula**: EMI = P × r × (1+r)^n ÷ ((1+r)^n - 1)
Where:
- P = Principal loan amount
- r = Monthly interest rate (annual rate ÷ 12)
- n = Number of monthly installments

**Example**:
- Loan Amount: ₹50 lakh
- Interest Rate: 9% per annum
- Tenure: 20 years
- Monthly EMI: ₹44,986

## 4. Property Taxation in India

### Stamp Duty:
- **Purpose**: State government revenue
- **Rates**: 3-10% of property value (varies by state)
- **Calculation Base**: Agreement value or circle rate, whichever is higher
- **Payment**: Before registration at sub-registrar office
- **Recent Changes**: Digital stamp duty in many states

### Registration Charges:
- **Rate**: 1-2% of property value
- **Maximum Limit**: ₹30,000 in most states
- **Process**: Simultaneous with stamp duty payment
- **Documents Required**: Sale deed, NOCs, approvals

### Goods and Services Tax (GST):
- **Under Construction**: 5% (with ITC) or 1% (without ITC)
- **Ready Properties**: No GST on resale
- **Commercial Properties**: 12% GST applicable
- **Input Tax Credit**: Available for business purchases

### Capital Gains Tax:
- **Short-term** (within 2 years): Taxed as per income slab
- **Long-term** (after 2 years): 20% with indexation benefit
- **Indexation**: Cost inflation index adjustment for inflation
- **Exemptions**:
  - Section 54: Purchase another house within 2 years
  - Section 54EC: Invest in specified bonds within 6 months

## 5. Investment Analysis Metrics

### Return Calculations:
- **Rental Yield**: (Annual Rent ÷ Property Price) × 100
- **Capital Appreciation**: (Current Value - Purchase Price) ÷ Purchase Price × 100
- **Total Return**: Rental Yield + Capital Appreciation
- **IRR**: Internal Rate of Return considering all cash flows

### Risk Assessment:
- **Market Risk**: Property price volatility
- **Liquidity Risk**: Time and cost to sell
- **Rental Risk**: Vacancy periods, rent collection issues
- **Regulatory Risk**: Policy changes affecting real estate

### Investment Strategies:
- **Buy-to-Let**: Purchase for rental income
- **Fix-and-Flip**: Renovate and resell quickly
- **Long-term Hold**: Capital appreciation over years
- **REITs**: Real Estate Investment Trusts for portfolio diversification
"""

        # Module 5: Land & Development Laws
        development_content = """
# Land & Development Laws

## 1. General Development Control Regulations (GDCR)

### Purpose and Framework:
- **Objective**: Systematic urban development and construction control
- **Scope**: Building specifications, land use, infrastructure norms
- **Authority**: State governments and urban development authorities
- **Compliance**: Mandatory for all development activities

### Key GDCR Components:

#### Setback Requirements:
- **Front Setback**: 3-6 meters based on road width
- **Side Setbacks**: 1.5-3 meters for each side
- **Rear Setback**: 3-6 meters from back boundary
- **Special Cases**: Corner plots, wide roads have different norms

#### Height Restrictions:
- **Residential**: 15-45 meters depending on road width
- **Commercial**: Higher limits with additional approvals
- **Special Buildings**: Airports, defense areas have specific limits
- **Exceptions**: Lift rooms, water tanks excluded from height

#### Parking Requirements:
- **Residential**: 1 space per dwelling unit minimum
- **Commercial**: 1 space per 70-100 sq.m built-up area
- **Visitor Parking**: Additional 20% of required spaces
- **Basement Parking**: Allowed with proper ventilation

## 2. Floor Space Index (FSI) / Floor Area Ratio (FAR)

### Understanding FSI:
- **Definition**: Total floor area of all floors ÷ Plot area
- **Example**: 1000 sq.m plot with FSI 2.0 = 2000 sq.m total construction possible
- **Significance**: Controls building density and urban development
- **Variation**: Different FSI for different zones and cities

### FSI Categories:

#### Basic FSI:
- **Source**: As per zoning regulations
- **Residential Zones**: 1.0-2.5 typically
- **Commercial Zones**: 1.5-4.0 typically
- **Industrial Zones**: 1.0-1.5 typically

#### Premium FSI:
- **Concept**: Additional FSI available against payment
- **Rates**: Market-determined premium charges
- **Utilization**: Subject to infrastructure capacity
- **Limits**: Maximum FSI caps even with premium

#### Incentive FSI:
- **Affordable Housing**: Additional 0.5-1.0 FSI
- **Green Buildings**: LEED/GRIHA certified projects
- **Transit-Oriented Development**: Near metro stations
- **Heritage Conservation**: For preserving old structures

### City-wise FSI Examples:
- **Mumbai**: 1.33 basic, up to 4.0 with premiums and TDR
- **Delhi**: 1.2-3.5 depending on zone and road width
- **Bangalore**: 1.75-2.5 with premiums available
- **Pune**: 1.0-2.0 with premium FSI options
- **Chennai**: 1.5-2.5 depending on location

## 3. Transfer of Development Rights (TDR)

### TDR Concept:
- **Definition**: Transferable certificate representing unused development potential
- **Purpose**: Compensate landowners for public land acquisition
- **Mechanism**: Generate TDR from donor site, utilize at receiver site
- **Validity**: Time-bound usage (typically 10 years)

### TDR Generation Sources:

#### Reservation TDR:
- **Source**: Land acquired for roads, parks, schools
- **Calculation**: Market value ÷ Ready reckoner rate
- **Compensation**: Alternative to monetary payment
- **Utilization**: Designated receiving zones

#### Slum TDR:
- **Source**: Slum rehabilitation projects
- **Benefit**: Incentive for private developers
- **Calculation**: Based on rehabilitated area
- **Conditions**: Minimum FSI consumption requirements

#### Heritage TDR:
- **Source**: Preserving heritage structures
- **Incentive**: Encourage conservation efforts
- **Calculation**: Foregone development potential
- **Usage**: Transfer to modern development zones

#### Amenity TDR:
- **Source**: Providing public amenities
- **Examples**: Community halls, dispensaries, gardens
- **Benefit**: Additional development rights
- **Conditions**: Maintenance obligations

### TDR Utilization Process:
1. **TDR Certificate**: Issued by competent authority
2. **TDR Banking**: Deposited in government TDR bank
3. **Market Transaction**: TDR bought/sold in market
4. **Utilization Application**: Submit for building approval
5. **Verification**: Authority verifies TDR authenticity
6. **Approval**: Building plan approved with TDR usage

## 4. Land Use Zoning and Planning

### Zoning Categories:

#### Residential Zones:
- **R-1**: Low density (detached houses)
- **R-2**: Medium density (row houses, low-rise apartments)
- **R-3**: High density (mid-rise apartments)
- **R-4**: Very high density (high-rise apartments)

#### Commercial Zones:
- **C-1**: Neighborhood commercial (local shops)
- **C-2**: Community commercial (markets, offices)
- **C-3**: City commercial (business districts)
- **C-4**: Regional commercial (malls, corporate offices)

#### Industrial Zones:
- **I-1**: Light industrial (IT parks, electronics)
- **I-2**: General industrial (manufacturing, processing)
- **I-3**: Heavy industrial (chemicals, steel)
- **Special Zones**: SEZ, export promotion zones

#### Mixed-Use Development:
- **Concept**: Combination of residential and commercial
- **Ratios**: Specified percentage for each use
- **Benefits**: Reduced travel, vibrant communities
- **Examples**: Integrated townships, smart cities

### Land Use Conversion:
- **Process**: Application to town planning authority
- **Requirements**: 
  - Feasibility study and impact assessment
  - Public notice and objection period
  - Infrastructure adequacy certificate
  - Environmental clearance if required
- **Charges**: Conversion charges and betterment levy
- **Timeline**: 6-12 months for approval

## 5. Approvals and Clearances

### Statutory Approvals:

#### Building Plan Approval:
- **Authority**: Municipal corporation/development authority
- **Documents**: 
  - Architectural and structural drawings
  - Site plan and survey
  - Ownership documents
  - NOCs from various departments
- **Timeline**: 30-60 days for standard projects
- **Validity**: 3 years with possible extensions

#### Environmental Clearances:
- **EIA**: Environmental Impact Assessment for large projects (>20,000 sq.m)
- **Process**: Impact study, public hearing, expert committee review
- **Timeline**: 6-12 months for complex projects
- **Conditions**: Monitoring and compliance requirements

#### Sectoral Clearances:
- **Fire NOC**: Fire safety and emergency evacuation
- **Airport Authority**: Height clearance near airports
- **Forest Department**: If affecting forest land
- **Pollution Control**: Air and water pollution norms
- **Archaeological Survey**: Near heritage sites

### Utility Connections:

#### Water Supply:
- **Source**: Municipal corporation or water authority
- **Requirements**: Approved building plan, completion certificate
- **Capacity**: Based on number of units and usage norms
- **Charges**: Connection fees and security deposit

#### Electricity Connection:
- **Provider**: State electricity board
- **Load Calculation**: Based on built-up area and usage
- **Infrastructure**: Transformer, distribution network adequacy
- **Timeline**: 15-30 days after application

#### Sewerage and Drainage:
- **Connection**: Municipal sewerage network
- **Treatment**: On-site or centralized STP requirements
- **Storm Water**: Separate drainage for rainwater
- **Compliance**: Pollution control board norms

## 6. Compliance and Penalties

### Common Violations:
- **Unauthorized Construction**: Beyond approved FSI/plans
- **Setback Violations**: Insufficient open spaces
- **Height Violations**: Exceeding permitted limits
- **Land Use Violations**: Non-conforming activities
- **Environmental Non-compliance**: Violation of clearance conditions

### Penalty Structure:
- **Monetary Penalties**: Fines based on violation severity
- **Regularization**: Payment for unauthorized construction
- **Stop Work Orders**: Halt construction activities
- **Demolition**: For serious structural violations
- **Criminal Action**: For fraud and gross violations

### Compliance Benefits:
- **Legal Security**: Clear title and occupancy rights
- **Financing**: Bank loan eligibility
- **Resale Value**: Higher market acceptance
- **Insurance**: Coverage for compliant properties
- **Utility Connections**: Authorized service connections
"""

        modules_data = [
            ('Real Estate Fundamentals', 'Introduction to real estate basics, stakeholders, and market overview', 'Beginner', 'Fundamentals', fundamentals_content, 'https://www.youtube.com/watch?v=dQw4w9WgXcQ', 1),
            ('Legal Framework & RERA', 'Comprehensive guide to RERA, legal compliance, and regulatory framework', 'Intermediate', 'Legal Framework', rera_content, 'https://www.youtube.com/watch?v=dQw4w9WgXcQ', 2),
            ('Property Measurements & Standards', 'Carpet area vs built-up area, BIS standards, and floor plan reading', 'Beginner', 'Measurements', measurements_content, 'https://www.youtube.com/watch?v=dQw4w9WgXcQ', 3),
            ('Valuation & Finance', 'Property valuation methods, home loans, and taxation', 'Intermediate', 'Finance', valuation_content, 'https://www.youtube.com/watch?v=dQw4w9WgXcQ', 4),
            ('Land & Development Laws', 'GDCR, municipal bylaws, FSI/TDR calculations, and zoning', 'Advanced', 'Legal Framework', development_content, 'https://www.youtube.com/watch?v=dQw4w9WgXcQ', 5)
        ]
        
        for module in modules_data:
            cursor.execute("""
                INSERT INTO modules (title, description, difficulty, category, content, youtube_url, order_index, created_date, active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (*module, datetime.now().isoformat()))
    
    # Insert comprehensive quiz questions if they don't exist
    cursor.execute("SELECT COUNT(*) FROM quizzes")
    quiz_count = cursor.fetchone()[0]
    
    if quiz_count == 0:
        quiz_questions = [
            # Real Estate Fundamentals (Module 1) - 20 questions
            (1, "What does real estate primarily encompass?", "Only land", "Land and permanent structures", "Only buildings", "Movable property", "B", "Real estate includes both land and any permanent structures attached to it."),
            (1, "Which regulatory body primarily governs real estate in India?", "SEBI", "RBI", "RERA", "IRDA", "C", "RERA (Real Estate Regulatory Authority) is the primary regulatory body for real estate in India."),
            (1, "What is a freehold property?", "Temporary ownership", "Absolute ownership", "Rental property", "Shared ownership", "B", "Freehold means absolute ownership of both land and building."),
            (1, "Which type of property is NOT mentioned as residential?", "Apartments", "Warehouses", "Villas", "Studio Apartments", "B", "Warehouses are commercial/industrial properties, not residential."),
            (1, "What is the approximate value of the Indian real estate market?", "$100 billion", "$200 billion", "$300 billion", "$400 billion", "B", "The Indian real estate market is valued at over $200 billion."),
            (1, "What does PropTech refer to?", "Property Technology", "Professional Technology", "Proper Technology", "Protected Technology", "A", "PropTech refers to Property Technology - digital platforms transforming real estate transactions."),
            (1, "Which government initiative focuses on affordable housing?", "Smart Cities", "Housing for All", "Digital India", "Make in India", "B", "Housing for All is the government initiative focusing on affordable housing."),
            (1, "What is a Special Economic Zone (SEZ)?", "Residential area", "Commercial area", "Industrial area with special benefits", "Agricultural area", "C", "SEZ is an industrial area with special economic benefits and policies."),
            (1, "Which organization regulates REITs in India?", "RERA", "RBI", "SEBI", "IRDA", "C", "SEBI (Securities and Exchange Board of India) regulates REITs."),
            (1, "What is the typical annual growth rate of Indian real estate market?", "2-4%", "6-8%", "10-12%", "15-20%", "B", "The Indian real estate market typically grows at 6-8% annually."),
            (1, "What does IGBC certification indicate?", "Legal compliance", "Green building standards", "Fire safety", "Structural integrity", "B", "IGBC (Indian Green Building Council) certification indicates green building standards."),
            (1, "Which factor is most important for real estate investment?", "Color of building", "Location", "Number of rooms", "Building height", "B", "Location is the most critical factor for real estate investment success."),
            (1, "What is a row house?", "Independent house", "Apartment", "Attached house in a row", "Commercial space", "C", "A row house is an attached house in a series of connected houses."),
            (1, "Which risk factor affects real estate investment?", "Market volatility", "Weather conditions", "Currency exchange", "Stock market", "A", "Market volatility is a major risk factor affecting real estate investments."),
            (1, "What does 'under construction' mean?", "Completed project", "Project in building phase", "Demolished project", "Planned project", "B", "Under construction refers to projects currently in the building phase."),
            (1, "Which document proves property ownership?", "Electricity bill", "Sale deed", "Ration card", "Driving license", "B", "Sale deed is the primary document proving property ownership."),
            (1, "What is carpet area?", "Total project area", "Usable floor area", "Common area", "Parking area", "B", "Carpet area is the actual usable floor area within the walls of an apartment."),
            (1, "Which sector contributes most to real estate demand?", "Agriculture", "IT/Services", "Mining", "Textile", "B", "IT and Services sector contributes significantly to real estate demand in India."),
            (1, "What is a township?", "Small town", "Integrated development", "Village", "City district", "B", "A township is an integrated development with residential, commercial, and social infrastructure."),
            (1, "Which approval is mandatory before construction?", "Neighbor consent", "Building plan approval", "Bank approval", "Insurance approval", "B", "Building plan approval from competent authority is mandatory before construction."),

            # Legal Framework & RERA (Module 2) - 20 questions
            (2, "In which year was RERA enacted?", "2015", "2016", "2017", "2018", "B", "RERA (Real Estate Regulation and Development Act) was enacted in 2016."),
            (2, "What percentage of receivables must developers deposit in escrow account?", "50%", "60%", "70%", "80%", "C", "Developers must deposit 70% of receivables in escrow account under RERA."),
            (2, "How many years of structural warranty must developers provide?", "3 years", "5 years", "7 years", "10 years", "B", "Developers must provide 5-year structural warranty under RERA."),
            (2, "Projects with how many units must register under RERA?", "5+ units", "6+ units", "7+ units", "8+ units", "D", "Projects with 8 or more units or 500+ sq.m must register under RERA."),
            (2, "What is the minimum area threshold for RERA registration?", "300 sq.m", "400 sq.m", "500 sq.m", "600 sq.m", "C", "Projects with 500 sq.m or more must register under RERA."),
            (2, "What interest rate applies for delayed possession compensation?", "8% per annum", "10% per annum", "12% per annum", "15% per annum", "B", "RERA mandates 10% per annum interest for delayed possession compensation."),
            (2, "How often must developers submit progress reports?", "Monthly", "Quarterly", "Half-yearly", "Annually", "B", "Developers must submit quarterly progress reports under RERA."),
            (2, "What is the full form of MoHUA?", "Ministry of Home and Urban Affairs", "Ministry of Housing and Urban Affairs", "Ministry of Health and Urban Affairs", "Ministry of Housing and Urban Applications", "B", "MoHUA stands for Ministry of Housing and Urban Affairs."),
            (2, "Who can file complaints under RERA?", "Only buyers", "Only agents", "Buyers and agents", "Anyone", "C", "Both homebuyers and real estate agents can file complaints under RERA."),
            (2, "What is the penalty for non-registration under RERA?", "Warning", "Fine up to 10% of project cost", "Imprisonment", "Project closure", "B", "Non-registration under RERA can result in fine up to 10% of estimated project cost."),
            (2, "Which authority handles RERA appeals?", "High Court", "Supreme Court", "RERA Appellate Tribunal", "Consumer Court", "C", "RERA Appellate Tribunal handles appeals against RERA authority orders."),
            (2, "What information must be displayed on RERA website?", "Project details only", "Financial information only", "Complete project and financial details", "Marketing materials", "C", "Complete project and financial information must be displayed on RERA website."),
            (2, "Can developers change approved plans without permission?", "Yes, always", "No, never", "Yes, with RERA approval", "Yes, with buyer consent", "C", "Developers cannot change approved plans without proper RERA approval."),
            (2, "What is the time limit for possession delay complaints?", "1 year", "2 years", "3 years", "5 years", "C", "Complaints for possession delay can be filed within 3 years under RERA."),
            (2, "Which document is most important for RERA complaint?", "Aadhaar card", "Sale agreement", "Bank statement", "Income certificate", "B", "Sale agreement is the most important document for filing RERA complaints."),
            (2, "What happens if developer fails to get RERA registration?", "Project continues", "Project must stop", "Warning issued", "Fine imposed", "B", "Projects must stop if developer fails to get mandatory RERA registration."),
            (2, "Can real estate agents work without RERA registration?", "Yes", "No", "Sometimes", "Only for resale", "B", "Real estate agents cannot work without RERA registration."),
            (2, "What is defect liability period under RERA?", "2 years", "3 years", "5 years", "10 years", "C", "Defect liability period is 5 years for structural defects under RERA."),
            (2, "Who appoints RERA authority members?", "Central Government", "State Government", "High Court", "Supreme Court", "B", "State Government appoints RERA authority members."),
            (2, "What is the maximum composition of RERA authority?", "3 members", "5 members", "7 members", "9 members", "B", "RERA authority can have maximum 5 members including chairperson."),

            # Property Measurements & Standards (Module 3) - 20 questions  
            (3, "What is carpet area?", "Total project area", "Actual usable floor area", "Common area", "Parking area", "B", "Carpet area is the actual usable floor area within the apartment walls."),
            (3, "Which standard governs property measurement in India?", "IS 3861:2002", "IS 1234:2000", "IS 5678:2005", "IS 9999:2010", "A", "IS 3861:2002 is the BIS standard for measurement of building areas."),
            (3, "What is loading factor?", "Weight capacity", "Difference between super built-up and carpet area", "Floor strength", "Electrical load", "B", "Loading factor is the percentage difference between super built-up and carpet area."),
            (3, "Post-RERA, property sales are based on which area?", "Super built-up area", "Built-up area", "Carpet area", "Saleable area", "C", "Post-RERA, property sales must be based on carpet area only."),
            (3, "What percentage is typically added to carpet area for built-up area?", "5-10%", "10-15%", "20-25%", "30-35%", "B", "Built-up area typically adds 10-15% to carpet area for wall thickness."),
            (3, "Balcony area gets what weightage in carpet area calculation?", "25%", "50%", "75%", "100%", "B", "Balcony area gets 50% weightage in carpet area calculation under BIS standards."),
            (3, "What does 'WC' represent in floor plans?", "Water Cooler", "Wall Cabinet", "Water Closet", "Window Corner", "C", "WC represents Water Closet (toilet) in floor plans."),
            (3, "What is the typical tolerance allowed in area measurement?", "±1%", "±2%", "±5%", "±10%", "B", "±2% tolerance is typically allowed in area measurements under BIS standards."),
            (3, "Which area includes proportionate common areas?", "Carpet area", "Built-up area", "Super built-up area", "Usable area", "C", "Super built-up area includes proportionate common areas like lobbies, elevators."),
            (3, "What should buyers do to verify measurements?", "Trust developer", "Hire independent surveyor", "Use online tools", "Ask neighbors", "B", "Buyers should hire independent surveyor to verify property measurements."),
            (3, "Which symbol represents kitchen in floor plans?", "K", "Kit", "C", "Cook", "A", "K represents kitchen in architectural floor plans."),
            (3, "What is the remedy for area shortfall under RERA?", "No remedy", "Proportionate refund", "Interest payment", "Both B and C", "D", "RERA provides both proportionate refund and interest for area shortfall."),
            (3, "How are common areas typically distributed?", "Equally among all units", "Based on carpet area proportion", "Based on number of rooms", "Based on floor level", "B", "Common areas are distributed based on carpet area proportion of each unit."),
            (3, "What does DB stand for in electrical plans?", "Door Bell", "Distribution Board", "Double Bedroom", "Data Board", "B", "DB stands for Distribution Board in electrical plans."),
            (3, "Which measurement is most important for buyers?", "Super built-up area", "Built-up area", "Carpet area", "Total area", "C", "Carpet area is most important as it represents actual usable space."),
            (3, "What technology helps in accurate measurement?", "GPS", "Laser measurement devices", "Mobile apps", "Calculators", "B", "Laser measurement devices provide high accuracy in property measurement."),
            (3, "Cross-ventilation is important for which aspect?", "Security", "Privacy", "Air circulation", "Sound proofing", "C", "Cross-ventilation is important for natural air circulation in properties."),
            (3, "What does CAD stand for in architectural drawings?", "Computer Aided Design", "Central Air Distribution", "Construction And Development", "Carpet Area Diagram", "A", "CAD stands for Computer Aided Design used in architectural drawings."),
            (3, "Which direction facing is generally preferred in India?", "South", "West", "North or East", "Southwest", "C", "North or East facing properties are generally preferred in India."),
            (3, "What is the standard ceiling height in residential buildings?", "8 feet", "9-10 feet", "12 feet", "15 feet", "B", "Standard ceiling height in residential buildings is 9-10 feet."),

            # Valuation & Finance (Module 4) - 20 questions
            (4, "What does CMA stand for in property valuation?", "Certified Market Analysis", "Comparative Market Analysis", "Commercial Market Assessment", "Current Market Appraisal", "B", "CMA stands for Comparative Market Analysis - comparing with similar properties."),
            (4, "What is the income approach formula for valuation?", "Income ÷ Expenses", "Net Income ÷ Cap Rate", "Gross Income × 12", "Rental Yield ÷ 100", "B", "Income approach formula is Net Operating Income ÷ Capitalization Rate."),
            (4, "What is LTV ratio?", "Loan-to-Value ratio", "Long-term-Value ratio", "Legal-title-Verification ratio", "Land-to-Value ratio", "A", "LTV is Loan-to-Value ratio - loan amount as percentage of property value."),
            (4, "What is the current LTV limit for properties up to ₹30 lakh?", "75%", "80%", "85%", "90%", "D", "LTV limit is 90% for properties up to ₹30 lakh for eligible borrowers."),
            (4, "What is the EMI formula component 'P'?", "Percentage", "Principal", "Payment", "Period", "B", "P represents Principal loan amount in EMI calculation formula."),
            (4, "What is the current GST rate on under-construction properties?", "1% or 5%", "5% or 12%", "12% or 18%", "18% or 28%", "A", "GST on under-construction properties is 1% (without ITC) or 5% (with ITC)."),
            (4, "How many years constitute long-term capital gains for property?", "1 year", "2 years", "3 years", "5 years", "B", "Property held for more than 2 years qualifies for long-term capital gains."),
            (4, "What is Section 54 exemption for?", "Stamp duty", "Registration", "Capital gains tax", "Income tax", "C", "Section 54 provides capital gains tax exemption for purchasing another house."),
            (4, "What is rental yield formula?", "Monthly rent × 12 ÷ Property price", "Annual rent ÷ Property price × 100", "Property price ÷ Annual rent", "Monthly rent ÷ Property price", "B", "Rental yield = (Annual rent ÷ Property price) × 100."),
            (4, "Which factor has highest weight in property valuation?", "Age of property", "Location", "Size", "Amenities", "B", "Location typically has the highest weight (40-50%) in property valuation."),
            (4, "What is cap rate?", "Capital rate", "Capitalization rate", "Capacity rate", "Capital gains rate", "B", "Cap rate is capitalization rate used in income approach valuation."),
            (4, "What is stamp duty calculated on?", "Agreement value only", "Market value only", "Higher of agreement or circle rate", "Registration value", "C", "Stamp duty is calculated on higher of agreement value or circle rate."),
            (4, "What is the benefit of indexation in capital gains?", "Reduces tax", "Increases tax", "No impact", "Eliminates tax", "A", "Indexation adjusts purchase price for inflation, reducing taxable capital gains."),
            (4, "Which type of interest rate remains constant?", "Fixed rate", "Floating rate", "Variable rate", "Flexible rate", "A", "Fixed interest rate remains constant throughout the loan tenure."),
            (4, "What does IRR stand for?", "Interest Rate Return", "Internal Rate of Return", "Investment Risk Ratio", "Income Ratio Return", "B", "IRR stands for Internal Rate of Return considering all cash flows."),
            (4, "What is the typical down payment percentage?", "10-25%", "25-50%", "50-75%", "75-90%", "A", "Down payment is typically 10-25% (100% - LTV ratio)."),
            (4, "Which risk affects property liquidity?", "Market risk", "Credit risk", "Liquidity risk", "Interest rate risk", "C", "Liquidity risk affects how quickly property can be sold in the market."),
            (4, "What is cost approach depreciation rate annually?", "1-2%", "2-3%", "5-10%", "10-15%", "B", "Annual depreciation rate for buildings is typically 2-3% in cost approach."),
            (4, "Which document is required for home loan?", "Driving license", "Voter ID", "ITR and salary slips", "Ration card", "C", "ITR (Income Tax Returns) and salary slips are required for home loan."),
            (4, "What is CIBIL score requirement for home loans?", "500+", "600+", "700+", "750+", "D", "CIBIL score of 750+ is preferred for home loans for better rates."),

            # Land & Development Laws (Module 5) - 20 questions
            (5, "What does FSI stand for?", "Floor Space Index", "Floor Size Index", "Floor Structure Index", "Floor Safety Index", "A", "FSI stands for Floor Space Index - ratio of total floor area to plot area."),
            (5, "What does TDR stand for?", "Total Development Rights", "Transfer of Development Rights", "Temporary Development Rights", "Technical Development Rights", "B", "TDR stands for Transfer of Development Rights."),
            (5, "What is the purpose of GDCR?", "Tax collection", "Urban development control", "Property registration", "Loan processing", "B", "GDCR (General Development Control Regulations) controls urban development."),
            (5, "What is typical FSI for residential zones?", "0.5-1.0", "1.0-2.5", "3.0-4.0", "5.0-6.0", "B", "Typical FSI for residential zones ranges from 1.0-2.5."),
            (5, "How is FSI calculated?", "Total floor area ÷ Plot area", "Plot area ÷ Total floor area", "Built-up area ÷ Carpet area", "Carpet area ÷ Built-up area", "A", "FSI = Total floor area of all floors ÷ Plot area."),
            (5, "What is front setback requirement typically?", "1-2 meters", "3-6 meters", "8-10 meters", "12-15 meters", "B", "Front setback requirement is typically 3-6 meters based on road width."),
            (5, "Which authority issues building plan approval?", "State government", "Central government", "Municipal corporation", "High court", "C", "Municipal corporation or development authority issues building plan approval."),
            (5, "What is EIA?", "Economic Impact Assessment", "Environmental Impact Assessment", "Engineering Impact Assessment", "Educational Impact Assessment", "B", "EIA stands for Environmental Impact Assessment."),
            (5, "For which project size is EIA mandatory?", "5,000 sq.m", "10,000 sq.m", "20,000 sq.m", "50,000 sq.m", "C", "EIA is mandatory for projects above 20,000 sq.m built-up area."),
            (5, "What is the validity period of building plan approval?", "1 year", "2 years", "3 years", "5 years", "C", "Building plan approval is typically valid for 3 years."),
            (5, "What does CRZ stand for?", "Coastal Regulation Zone", "Central Regulation Zone", "Commercial Regulation Zone", "Construction Regulation Zone", "A", "CRZ stands for Coastal Regulation Zone."),
            (5, "Which clearance is needed near airports?", "Forest clearance", "Airport Authority clearance", "Railway clearance", "Defense clearance", "B", "Airport Authority clearance is needed for height restrictions near airports."),
            (5, "What is premium FSI?", "Basic FSI", "Additional FSI against payment", "Reduced FSI", "Free FSI", "B", "Premium FSI is additional FSI available against payment of premium."),
            (5, "How long is TDR typically valid?", "5 years", "10 years", "15 years", "20 years", "B", "TDR is typically valid for 10 years from date of issue."),
            (5, "What is slum TDR?", "TDR for slum dwellers", "TDR from slum rehabilitation", "TDR for poor people", "TDR for rural areas", "B", "Slum TDR is generated from slum rehabilitation projects."),
            (5, "Which zone allows mixed-use development?", "Residential only", "Commercial only", "Industrial only", "Mixed-use zones", "D", "Mixed-use zones specifically allow combination of residential and commercial."),
            (5, "What is land use conversion?", "Changing ownership", "Changing area", "Changing permitted use", "Changing price", "C", "Land use conversion means changing the permitted use of land."),
            (5, "What is betterment levy?", "Development charge", "Maintenance charge", "Service charge", "All of the above", "A", "Betterment levy is a development charge for land use conversion."),
            (5, "Which penalty applies for unauthorized construction?", "Warning only", "Fine and possible demolition", "Imprisonment only", "No penalty", "B", "Unauthorized construction can attract fines and possible demolition."),
            (5, "What is heritage TDR for?", "Old buildings", "Preserving heritage structures", "Historical documents", "Ancient artifacts", "B", "Heritage TDR incentivizes preservation of heritage structures.")
        ]
        
        for question in quiz_questions:
            cursor.execute("""
                INSERT INTO quizzes (module_id, question, option_a, option_b, option_c, option_d, correct_answer, explanation, created_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (*question, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()

def get_db_connection():
    """Get database connection"""
    return sqlite3.connect(DATABASE_PATH)

# Enhanced CSS Styling with Fixed Images and Gamification
st.markdown("""
<style>
.main-header {
    background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
    padding: 1rem;
    border-radius: 10px;
    color: white;
    text-align: center;
    margin-bottom: 2rem;
}

.module-card {
    background: white;
    padding: 1.5rem;
    border-radius: 10px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin-bottom: 1rem;
    border-left: 4px solid #2a5298;
}

.feature-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 2rem;
    border-radius: 15px;
    color: white;
    text-align: center;
    margin-bottom: 1rem;
    box-shadow: 0 8px 32px rgba(0,0,0,0.2);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.2);
}

.feature-card h3 {
    margin-bottom: 1rem;
    font-size: 1.2rem;
    font-weight: 600;
}

.feature-card p {
    font-size: 0.9rem;
    opacity: 0.9;
    line-height: 1.5;
}

.progress-bar {
    background: #f0f0f0;
    border-radius: 10px;
    height: 20px;
    overflow: hidden;
}

.progress-fill {
    background: linear-gradient(90deg, #4CAF50, #45a049);
    height: 100%;
    transition: width 0.3s ease;
}

.chat-container {
    background: #f8f9fa;
    border-radius: 10px;
    padding: 1rem;
    margin: 1rem 0;
    max-height: 400px;
    overflow-y: auto;
}

.sidebar-logo {
    text-align: center;
    padding: 1rem;
    background: #2a5298;
    color: white;
    border-radius: 10px;
    margin-bottom: 1rem;
}

.metric-card {
    background: white;
    padding: 1rem;
    border-radius: 10px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    text-align: center;
}

.content-viewer {
    background: white;
    padding: 2rem;
    border-radius: 10px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin: 1rem 0;
}

.badge {
    background: linear-gradient(45deg, #FFD700, #FFA500);
    color: white;
    padding: 0.3rem 0.8rem;
    border-radius: 20px;
    font-size: 0.8rem;
    margin: 0.2rem;
    display: inline-block;
}

.points-display {
    background: linear-gradient(45deg, #4CAF50, #45a049);
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 25px;
    font-weight: bold;
    text-align: center;
}

.quiz-question {
    background: #f8f9fa;
    padding: 1.5rem;
    border-radius: 10px;
    margin: 1rem 0;
    border-left: 4px solid #2a5298;
}

.quiz-option {
    background: white;
    padding: 0.8rem;
    margin: 0.5rem 0;
    border-radius: 8px;
    border: 2px solid #e0e0e0;
    cursor: pointer;
    transition: all 0.3s ease;
}

.quiz-option:hover {
    border-color: #2a5298;
    background: #f0f2f6;
}

.youtube-container {
    position: relative;
    width: 100%;
    height: 0;
    padding-bottom: 56.25%; /* 16:9 aspect ratio */
    margin: 1rem 0;
}

.youtube-container iframe {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    border-radius: 10px;
}

.achievement-card {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    padding: 1rem;
    border-radius: 10px;
    color: white;
    margin: 0.5rem 0;
    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
}

.level-indicator {
    background: linear-gradient(45deg, #667eea, #764ba2);
    color: white;
    padding: 0.5rem;
    border-radius: 15px;
    text-align: center;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# Enhanced DeepSeek Chat Integration
class DeepSeekChat:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.deepseek.com/v1/chat/completions"
        
    def get_response(self, user_input, context="real estate education"):
        """Get response from DeepSeek API"""
        
        system_prompt = """You are an expert Real Estate Education Assistant specializing in Indian real estate laws, regulations, and practices. You provide accurate, helpful, and educational responses about:

- RERA (Real Estate Regulation and Development Act) compliance
- Property valuation methods and techniques
- Legal documentation and procedures
- Investment strategies and market analysis
- Construction and technical aspects
- Taxation and financial planning
- Property measurements and standards
- Dispute resolution and consumer rights

Always provide practical, actionable advice while mentioning relevant legal frameworks and current market conditions in India."""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            "temperature": 0.7,
            "max_tokens": 1000,
            "stream": False
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result['choices'][0]['message']['content']
            
        except requests.exceptions.Timeout:
            return "Sorry, the request timed out. Please try again."
        except requests.exceptions.RequestException as e:
            return f"Sorry, I'm having trouble connecting to the AI service. Please try again later."
        except Exception as e:
            return "Sorry, something went wrong. Please try again."
    
    def generate_quiz_questions(self, module_title, difficulty, count=5):
        """Generate quiz questions using AI"""
        prompt = f"""
        Generate {count} multiple-choice questions for the module "{module_title}" with difficulty level "{difficulty}".
        
        Each question should:
        1. Be relevant to Indian real estate context
        2. Have 4 options (A, B, C, D)
        3. Have one correct answer
        4. Include a brief explanation
        
        Format the response as JSON:
        {{
            "questions": [
                {{
                    "question": "Question text here",
                    "option_a": "First option",
                    "option_b": "Second option", 
                    "option_c": "Third option",
                    "option_d": "Fourth option",
                    "correct_answer": "B",
                    "explanation": "Brief explanation"
                }}
            ]
        }}
        """
        
        response = self.get_response(prompt, context="quiz generation")
        
        try:
            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {"questions": []}
        except:
            return {"questions": []}
    
    def improve_content(self, current_content, improvement_request):
        """Use AI to improve module content"""
        prompt = f"""
        Current content:
        {current_content[:1000]}...
        
        Improvement request: {improvement_request}
        
        Please provide improved content that:
        1. Maintains the educational structure
        2. Includes the requested improvements
        3. Stays relevant to Indian real estate context
        4. Uses proper markdown formatting
        
        Return only the improved content.
        """
        
        return self.get_response(prompt, context="content improvement")

# Enhanced Content Research Module
class ContentResearcher:
    def __init__(self):
        self.available_topics = [
            "RERA compliance updates",
            "Property valuation methods", 
            "Real estate market trends",
            "Legal framework changes",
            "Construction technology",
            "Green building standards",
            "Investment strategies",
            "Taxation updates",
            "Documentation processes",
            "Dispute resolution"
        ]
        
        # Mock knowledge base with detailed content
        self._knowledge_base = {
            "RERA compliance updates": {
                "key_points": [
                    "RERA Amendment Act 2023 introduces stricter penalties for non-compliance",
                    "New online dispute resolution mechanism launched in Maharashtra and Karnataka",
                    "Mandatory quarterly progress reports now required on state RERA portals",
                    "Enhanced buyer protection measures in case of project delays and quality issues",
                    "Digital approval processes implemented for faster project registrations"
                ],
                "sources": [
                    {"title": "RERA Amendment Act 2023 - Key Changes", "url": "https://mohua.gov.in/rera-updates", "date": "2023-12-15"},
                    {"title": "MoHUA Guidelines on RERA Implementation", "url": "https://rera.karnataka.gov.in", "date": "2023-11-20"}
                ]
            },
            "Property valuation methods": {
                "key_points": [
                    "Comparative Market Analysis (CMA) remains the most widely used method in India",
                    "Income approach gaining popularity for rental property investments",
                    "Cost approach essential for new construction and insurance valuations",
                    "Automated Valuation Models (AVMs) being adopted by major banks",
                    "Location intelligence and GIS data improving valuation accuracy"
                ],
                "sources": [
                    {"title": "Property Valuation Standards in India", "url": "https://rbi.org.in/valuation-guidelines", "date": "2023-10-30"},
                    {"title": "Bank Valuation Norms Update", "url": "https://housing.com/valuation-guide", "date": "2023-09-15"}
                ]
            }
        }
    
    def run_research(self, selected_topics):
        """Research selected topics and return structured content"""
        results = {}
        
        for topic in selected_topics:
            if topic in self._knowledge_base:
                results[topic] = self._knowledge_base[topic].copy()
            else:
                # Generate generic content for topics not in knowledge base
                results[topic] = {
                    "key_points": [
                        f"Latest developments in {topic} show significant impact on Indian real estate",
                        f"Regulatory changes in {topic} affecting property transactions",
                        f"Market trends indicate growing importance of {topic}",
                        f"Industry experts recommend staying updated on {topic}",
                        f"Future outlook for {topic} remains positive with new initiatives"
                    ],
                    "sources": [
                        {"title": f"Industry Report on {topic}", "url": "https://realestate-india.com/reports", "date": datetime.now().strftime("%Y-%m-%d")},
                        {"title": f"Expert Analysis - {topic}", "url": "https://propertyguide.in/analysis", "date": datetime.now().strftime("%Y-%m-%d")}
                    ]
                }
            
            results[topic]["last_updated"] = datetime.now().isoformat()
        
        return results

# Gamification Functions
def award_points(user_id, points, reason):
    """Award points to user"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Update user points
        cursor.execute("UPDATE users SET points = points + ? WHERE id = ?", (points, user_id))
        
        # Record achievement
        cursor.execute("""
            INSERT INTO user_achievements (user_id, achievement_type, achievement_name, points_earned, earned_date)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, "points", reason, points, datetime.now().isoformat()))
        
        conn.commit()
    except Exception as e:
        print(f"Error awarding points: {e}")
    finally:
        conn.close()

def award_badge(user_id, badge_name):
    """Award badge to user"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get current badges
        cursor.execute("SELECT badges FROM users WHERE id = ?", (user_id,))
        result = cursor.fetchone()
        
        if result:
            badges = json.loads(result[0]) if result[0] else []
            if badge_name not in badges:
                badges.append(badge_name)
                
                # Update badges
                cursor.execute("UPDATE users SET badges = ? WHERE id = ?", (json.dumps(badges), user_id))
                
                # Record achievement
                cursor.execute("""
                    INSERT INTO user_achievements (user_id, achievement_type, achievement_name, points_earned, earned_date)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, "badge", badge_name, 0, datetime.now().isoformat()))
                
                conn.commit()
    except Exception as e:
        print(f"Error awarding badge: {e}")
    finally:
        conn.close()

def get_user_stats(user_id):
    """Get user statistics for gamification"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT points, badges, streak_days FROM users WHERE id = ?", (user_id,))
        result = cursor.fetchone()
        
        if result:
            return {
                'points': result[0] or 0,
                'badges': json.loads(result[1]) if result[1] else [],
                'streak_days': result[2] or 0
            }
    except Exception as e:
        print(f"Error getting user stats: {e}")
    finally:
        conn.close()
    
    return {'points': 0, 'badges': [], 'streak_days': 0}

# YouTube Functions
def extract_youtube_id(url):
    """Extract YouTube video ID from URL"""
    if not url:
        return None
    
    # Handle various YouTube URL formats
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#]+)',
        r'youtube\.com/watch\?.*v=([^&\n?#]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None

def embed_youtube_video(video_url):
    """Embed YouTube video in Streamlit"""
    video_id = extract_youtube_id(video_url)
    if video_id:
        embed_url = f"https://www.youtube.com/embed/{video_id}"
        st.markdown(f"""
        <div class="youtube-container">
            <iframe src="{embed_url}" frameborder="0" allowfullscreen></iframe>
        </div>
        """, unsafe_allow_html=True)
        return True
    return False

# Authentication functions with fixed column references
def authenticate_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    try:
        cursor.execute("""
            SELECT id, username, role, points, badges FROM users 
            WHERE username = ? AND password = ? AND active = 1
        """, (username, hashed_password))
        
        user = cursor.fetchone()
        
        if user:
            st.session_state.user_id = user[0]
            st.session_state.username = user[1]
            st.session_state.user_role = user[2]
            st.session_state.user_points = user[3] or 0
            st.session_state.user_badges = json.loads(user[4]) if user[4] else []
            return True
    except Exception as e:
        print(f"Authentication error: {e}")
    finally:
        conn.close()
    
    return False

def register_user(username, email, password, user_type):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if username or email already exists
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = ? OR email = ?", (username, email))
        if cursor.fetchone()[0] > 0:
            return False
            
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        cursor.execute("""
            INSERT INTO users (username, email, password, role, created_date, points, badges, streak_days)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (username, email, hashed_password, user_type, datetime.now().isoformat(), 100, '["Welcome Learner"]', 1))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Registration error: {e}")
        return False
    finally:
        conn.close()

def create_user_by_admin(username, email, password, role):
    """Admin function to create new users"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if username or email already exists
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = ? OR email = ?", (username, email))
        if cursor.fetchone()[0] > 0:
            return False, "Username or email already exists"
            
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        cursor.execute("""
            INSERT INTO users (username, email, password, role, created_date, points, badges, streak_days)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (username, email, hashed_password, role, datetime.now().isoformat(), 100, '["New Member"]', 0))
        
        conn.commit()
        return True, "User created successfully"
    except Exception as e:
        return False, f"Error creating user: {str(e)}"
    finally:
        conn.close()

# Module and Content Functions
def get_available_modules():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT id, title, description, difficulty, category, youtube_url
            FROM modules 
            WHERE active = 1
            ORDER BY order_index
        """)
        
        modules = cursor.fetchall()
        
        return [
            {
                'id': module[0],
                'title': module[1],
                'description': module[2],
                'difficulty': module[3],
                'category': module[4],
                'youtube_url': module[5]
            }
            for module in modules
        ]
    except Exception as e:
        print(f"Error getting modules: {e}")
        return []
    finally:
        conn.close()

def get_module_content(module_id):
    """Get full content of a specific module"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT title, description, content, difficulty, category, youtube_url
            FROM modules 
            WHERE id = ? AND active = 1
        """, (module_id,))
        
        result = cursor.fetchone()
        
        if result:
            return {
                'title': result[0],
                'description': result[1],
                'content': result[2],
                'difficulty': result[3],
                'category': result[4],
                'youtube_url': result[5]
            }
    except Exception as e:
        print(f"Error getting module content: {e}")
    finally:
        conn.close()
    
    return None

def update_module_content(module_id, title, description, content, youtube_url):
    """Update module content"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE modules 
            SET title = ?, description = ?, content = ?, youtube_url = ?, updated_date = ?
            WHERE id = ?
        """, (title, description, content, youtube_url, datetime.now().isoformat(), module_id))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating module: {e}")
        return False
    finally:
        conn.close()

def add_module(title, description, difficulty, category, content="", youtube_url=""):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO modules (title, description, difficulty, category, content, youtube_url, created_date, active)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        """, (title, description, difficulty, category, content, youtube_url, datetime.now().isoformat()))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error adding module: {e}")
        return False
    finally:
        conn.close()

def delete_module(module_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("UPDATE modules SET active = 0 WHERE id = ?", (module_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting module: {e}")
        return False
    finally:
        conn.close()

# Quiz Functions
def get_quiz_questions(module_id):
    """Get quiz questions for a module"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT id, question, option_a, option_b, option_c, option_d, correct_answer, explanation
            FROM quizzes
            WHERE module_id = ?
            ORDER BY id
        """, (module_id,))
        
        questions = cursor.fetchall()
        
        return [
            {
                'id': q[0],
                'question': q[1],
                'options': {'A': q[2], 'B': q[3], 'C': q[4], 'D': q[5]},
                'correct_answer': q[6],
                'explanation': q[7]
            }
            for q in questions
        ]
    except Exception as e:
        print(f"Error getting quiz questions: {e}")
        return []
    finally:
        conn.close()

def add_quiz_question(module_id, question, option_a, option_b, option_c, option_d, correct_answer, explanation):
    """Add a new quiz question"""
    conn = get_db_connection()
    cursor = conn.cursor()
        
    try:
        cursor.execute("""
            INSERT INTO quizzes (module_id, question, option_a, option_b, option_c, option_d, correct_answer, explanation, created_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (module_id, question, option_a, option_b, option_c, option_d, correct_answer, explanation, datetime.now().isoformat()))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error adding quiz question: {e}")
        return False
    finally:
        conn.close()

def save_quiz_result(user_id, module_id, score, total_questions):
    """Save quiz result and award points/badges"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        percentage = (score / total_questions) * 100
        
        # Update or insert progress
        cursor.execute("""
            INSERT OR REPLACE INTO user_progress 
            (user_id, module_id, quiz_score, quiz_attempts, started_date)
            VALUES (?, ?, ?, 
                    COALESCE((SELECT quiz_attempts FROM user_progress WHERE user_id = ? AND module_id = ?), 0) + 1,
                    ?)
        """, (user_id, module_id, percentage, user_id, module_id, datetime.now().isoformat()))
        
        conn.commit()
        
        # Award points based on performance
        if percentage >= 90:
            award_points(user_id, 100, f"Excellent Quiz Performance ({percentage:.1f}%)")
            if percentage == 100:
                award_badge(user_id, "Perfect Score")
        elif percentage >= 80:
            award_points(user_id, 75, f"Good Quiz Performance ({percentage:.1f}%)")
        elif percentage >= 70:
            award_points(user_id, 50, f"Passing Quiz Score ({percentage:.1f}%)")
        
        # Award completion badge
        award_badge(user_id, "Quiz Taker")
        
    except Exception as e:
        print(f"Error saving quiz result: {e}")
    finally:
        conn.close()

# Data Visualization Functions
def create_user_progress_chart(user_id):
    """Create user progress visualization"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT m.title, COALESCE(p.quiz_score, 0) as score
            FROM modules m
            LEFT JOIN user_progress p ON m.id = p.module_id AND p.user_id = ?
            WHERE m.active = 1
            ORDER BY m.order_index
        """, (user_id,))
        
        data = cursor.fetchall()
        
        if data:
            df = pd.DataFrame(data, columns=['Module', 'Score'])
            
            fig = px.bar(
                df, 
                x='Module', 
                y='Score',
                title='Your Module Progress',
                color='Score',
                color_continuous_scale='viridis'
            )
            
            fig.update_layout(
                xaxis_tickangle=-45,
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        print(f"Error creating progress chart: {e}")
    finally:
        conn.close()

def create_admin_analytics_charts():
    """Create admin analytics visualizations"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # User registration over time
        cursor.execute("""
            SELECT DATE(created_date) as date, COUNT(*) as registrations
            FROM users
            WHERE role != 'admin'
            GROUP BY DATE(created_date)
            ORDER BY date
        """)
        
        reg_data = cursor.fetchall()
        
        if reg_data:
            df_reg = pd.DataFrame(reg_data, columns=['Date', 'Registrations'])
            df_reg['Date'] = pd.to_datetime(df_reg['Date'])
            
            fig1 = px.line(
                df_reg,
                x='Date',
                y='Registrations',
                title='User Registrations Over Time',
                markers=True
            )
            
            st.plotly_chart(fig1, use_container_width=True)
        
        # Module completion rates
        cursor.execute("""
            SELECT m.title, COUNT(p.user_id) as completions
            FROM modules m
            LEFT JOIN user_progress p ON m.id = p.module_id AND p.quiz_score >= 70
            WHERE m.active = 1
            GROUP BY m.id, m.title
            ORDER BY completions DESC
        """)
        
        completion_data = cursor.fetchall()
        
        if completion_data:
            df_comp = pd.DataFrame(completion_data, columns=['Module', 'Completions'])
            
            fig2 = px.pie(
                df_comp,
                values='Completions',
                names='Module',
                title='Module Completion Distribution'
            )
            
            st.plotly_chart(fig2, use_container_width=True)
    except Exception as e:
        print(f"Error creating admin charts: {e}")
    finally:
        conn.close()

# Main UI Functions
def show_login_form():
    st.subheader("🔐 Login")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            if authenticate_user(username, password):
                st.session_state.authenticated = True
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid credentials")
    
    st.divider()
    
    if st.button("Register New Account"):
        st.session_state.show_register = True
        st.rerun()

def show_registration_form():
    st.subheader("📝 Register")
    
    with st.form("register_form"):
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        user_type = st.selectbox("User Type", ["student", "professional"])
        submitted = st.form_submit_button("Register")
        
        if submitted:
            if not username or not email or not password:
                st.error("Please fill all fields")
            elif password != confirm_password:
                st.error("Passwords don't match")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters")
            elif register_user(username, email, password, user_type):
                st.success("Registration successful! You've earned 100 points and your first badge! Please login.")
                st.session_state.show_register = False
                st.rerun()
            else:
                st.error("Registration failed - Username or email already exists")
    
    if st.button("Back to Login"):
        st.session_state.show_register = False
        st.rerun()

def show_navigation():
    st.markdown('<div class="sidebar-logo"><h3>🏠 RealEstateGuru</h3></div>', unsafe_allow_html=True)
    
    # User info with gamification
    st.write(f"Welcome, **{st.session_state.username}**!")
    st.write(f"Role: *{st.session_state.user_role.title()}*")
    
    # Show points and badges
    if st.session_state.user_role != 'admin':
        user_stats = get_user_stats(st.session_state.user_id)
        st.markdown(f'<div class="points-display">🏆 {user_stats["points"]} Points</div>', unsafe_allow_html=True)
        
        if user_stats['badges']:
            st.write("**Badges:**")
            for badge in user_stats['badges']:
                st.markdown(f'<span class="badge">🏅 {badge}</span>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    if st.session_state.user_role == 'admin':
        st.subheader("Admin Panel")
        
        if st.button("📊 Dashboard", use_container_width=True):
            st.session_state.current_page = "admin_dashboard"
            st.rerun()
        
        if st.button("📚 Content Management", use_container_width=True):
            st.session_state.current_page = "content_management"
            st.rerun()
        
        if st.button("👥 User Management", use_container_width=True):
            st.session_state.current_page = "user_management"
            st.rerun()
        
        if st.button("❓ Quiz Management", use_container_width=True):
            st.session_state.current_page = "quiz_management"
            st.rerun()
        
        if st.button("🔍 Content Research", use_container_width=True):
            st.session_state.current_page = "content_research"
            st.rerun()
        
        if st.button("📈 Analytics", use_container_width=True):
            st.session_state.current_page = "analytics"
            st.rerun()
    else:
        st.subheader("Learning Modules")
        modules = get_available_modules()
        
        for module in modules:
            difficulty_emoji = {"Beginner": "🟢", "Intermediate": "🟡", "Advanced": "🔴"}
            emoji = difficulty_emoji.get(module['difficulty'], "📚")
            
            if st.button(f"{emoji} {module['title']}", key=f"module_{module['id']}", use_container_width=True):
                st.session_state.current_module = module['id']
                st.session_state.current_page = "module_content"
                st.rerun()
        
        st.divider()
        
        if st.button("📊 My Progress", use_container_width=True):
            st.session_state.current_page = "progress"
            st.rerun()
        
        if st.button("🏆 Take Quiz", use_container_width=True):
            st.session_state.current_page = "quiz"
            st.rerun()
        
        if st.button("🎖️ Achievements", use_container_width=True):
            st.session_state.current_page = "achievements"
            st.rerun()
    
    st.divider()
    
    if st.button("🤖 AI Assistant", use_container_width=True):
        st.session_state.current_page = "ai_assistant"
        st.rerun()
    
    if st.button("🚪 Logout", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

def show_welcome_page():
    st.markdown('<div class="main-header"><h1>Welcome to RealEstateGuru</h1><p>Your Complete Real Estate Education Platform with Gamification & AI</p></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3>🎯 Learn & Earn Points</h3>
            <p>Complete modules, take quizzes, and earn points and badges while mastering real estate concepts with our comprehensive curriculum.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3>🎥 Video Learning</h3>
            <p>Watch curated YouTube videos embedded in each module for enhanced learning experience with visual explanations.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <h3>🤖 AI-Powered</h3>
            <p>Get AI assistance, auto-generated quizzes, and content improvements using advanced DeepSeek AI technology.</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Key Features")
        st.markdown("""
        - 📚 **Rich Content**: 5 comprehensive modules with 20+ quizzes each
        - 🎮 **Gamification**: Points, badges, and achievements system
        - 📱 **Responsive Design**: Learn on any device with optimized interface
        - 🏅 **Certification Ready**: Prepare for real estate certifications
        - 📊 **Progress Analytics**: Visual charts showing your learning journey
        """)
    
    with col2:
        st.subheader("🚀 Advanced Features")
        st.markdown("""
        - 🤖 **AI Assistant**: Get instant help and generate custom content
        - 📈 **Real-time Analytics**: Live progress tracking and performance metrics
        - 🎥 **Video Integration**: YouTube videos embedded directly in modules
        - 👥 **Complete Admin Tools**: Full content and user management system
        - ✏️ **Content Editing**: Full CRUD operations for all content
        """)
    
    st.markdown("---")
    st.info("💡 **Get Started**: Register as a student to start earning points and badges, or login as admin (`admin`/`admin123`) to manage content and users.")

def show_user_dashboard():
    st.markdown('<div class="main-header"><h1>Your Learning Dashboard</h1></div>', unsafe_allow_html=True)
    
    # Gamification metrics
    user_stats = get_user_stats(st.session_state.user_id)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("🏆 Points", user_stats['points'], "Keep learning!")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("🏅 Badges", len(user_stats['badges']), "Achievements unlocked")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("🔥 Streak", user_stats['streak_days'], "Days in a row")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("📚 Modules", "5", "100+ Quiz Questions")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Progress chart
    st.subheader("📈 Your Progress Analytics")
    create_user_progress_chart(st.session_state.user_id)
    
    st.markdown("---")
    
    # Available Modules
    st.subheader("📚 Available Learning Modules")
    
    modules = get_available_modules()
    
    for module in modules:
        difficulty_color = {"Beginner": "🟢", "Intermediate": "🟡", "Advanced": "🔴"}
        color = difficulty_color.get(module['difficulty'], "📚")
        
        with st.expander(f"{color} {module['title']} ({module['difficulty']})"):
            st.write(f"**Category:** {module['category']}")
            st.write(f"**Description:** {module['description']}")
            
            if module['youtube_url']:
                st.write("📹 **Video Available**")
            
            # Show quiz count
            quiz_count = len(get_quiz_questions(module['id']))
            st.write(f"❓ **Quiz Questions:** {quiz_count}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button(f"📖 Study", key=f"study_{module['id']}"):
                    st.session_state.current_module = module['id']
                    st.session_state.current_page = "module_content"
                    st.rerun()
            
            with col2:
                if st.button(f"🏆 Quiz", key=f"quiz_{module['id']}"):
                    st.session_state.current_module = module['id']
                    st.session_state.current_page = "quiz"
                    st.rerun()
            
            with col3:
                st.info("Earn points & badges!")

def show_module_content():
    """Display detailed content of a specific module with video"""
    module_id = st.session_state.get('current_module')
    if not module_id:
        st.error("No module selected")
        return
    
    module = get_module_content(module_id)
    if not module:
        st.error("Module not found")
        return
    
    # Module header
    st.markdown(f'<div class="main-header"><h1>{module["title"]}</h1><p>{module["description"]}</p></div>', unsafe_allow_html=True)
    
    # Module info and navigation
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.info(f"**Difficulty:** {module['difficulty']}")
    with col2:
        st.info(f"**Category:** {module['category']}")
    with col3:
        if st.button("🏆 Take Quiz"):
            st.session_state.current_page = "quiz"
            st.rerun()
    with col4:
        if st.button("← Back"):
            st.session_state.current_page = "dashboard"
            st.session_state.current_module = None
            st.rerun()
    
    st.markdown("---")
    
    # YouTube video if available
    if module['youtube_url']:
        st.subheader("📹 Module Video")
        if embed_youtube_video(module['youtube_url']):
            # Award points for watching video
            award_points(st.session_state.user_id, 10, f"Watched video: {module['title']}")
        else:
            st.error("Invalid YouTube URL")
    
    # Module content
    if module['content']:
        st.subheader("📖 Module Content")
        st.markdown('<div class="content-viewer">', unsafe_allow_html=True)
        st.markdown(module['content'])
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Award points for reading content
        if st.button("✅ Mark as Read (+20 points)", use_container_width=True):
            award_points(st.session_state.user_id, 20, f"Completed reading: {module['title']}")
            award_badge(st.session_state.user_id, "Content Reader")
            st.success("Great! You've earned 20 points for reading this module!")
            st.rerun()
    else:
        st.warning("No content available for this module yet.")

def show_quiz():
    """Enhanced quiz system with gamification"""
    module_id = st.session_state.get('current_module')
    if not module_id:
        st.error("No module selected")
        return
    
    # Get module info
    module = get_module_content(module_id)
    if not module:
        st.error("Module not found")
        return
    
    st.markdown(f'<div class="main-header"><h1>🏆 Quiz: {module["title"]}</h1></div>', unsafe_allow_html=True)
    
    # Get quiz questions
    questions = get_quiz_questions(module_id)
    
    if not questions:
        st.warning("No quiz questions available for this module yet.")
        if st.button("← Back to Module"):
            st.session_state.current_page = "module_content"
            st.rerun()
        return
    
    # Quiz logic
    if not st.session_state.quiz_started:
        # Quiz start screen
        st.subheader(f"📋 Quiz Information")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Questions", len(questions))
        with col2:
            st.metric("Points per Question", "10")
        with col3:
            st.metric("Passing Score", "70%")
        
        st.markdown("---")
        st.write("**Instructions:**")
        st.write("- Answer all questions to the best of your ability")
        st.write("- You can review your answers before submitting")
        st.write("- Minimum 70% required to pass")
        st.write("- Earn bonus points for high scores!")
        
        if st.button("🚀 Start Quiz", use_container_width=True):
            st.session_state.quiz_started = True
            st.session_state.current_question = 0
            st.session_state.quiz_answers = {}
            st.session_state.quiz_score = 0
            st.rerun()
    
    else:
        # Quiz questions
        total_questions = len(questions)
        current_q = st.session_state.current_question
        
        if current_q < total_questions:
            question = questions[current_q]
            
            st.subheader(f"Question {current_q + 1} of {total_questions}")
            st.progress((current_q + 1) / total_questions)
            
            st.markdown(f'<div class="quiz-question"><h4>{question["question"]}</h4></div>', unsafe_allow_html=True)
            
            # Answer options
            selected_answer = st.radio(
                "Choose your answer:",
                options=list(question['options'].keys()),
                format_func=lambda x: f"{x}. {question['options'][x]}",
                key=f"q_{current_q}"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                if current_q > 0:
                    if st.button("← Previous"):
                        st.session_state.current_question -= 1
                        st.rerun()
            
            with col2:
                if st.button("Next →" if current_q < total_questions - 1 else "Submit Quiz"):
                    # Save answer
                    st.session_state.quiz_answers[current_q] = selected_answer
                    
                    if current_q < total_questions - 1:
                        st.session_state.current_question += 1
                        st.rerun()
                    else:
                        # Calculate score and finish quiz
                        correct_answers = 0
                        for i, question in enumerate(questions):
                            if st.session_state.quiz_answers.get(i) == question['correct_answer']:
                                correct_answers += 1
                        
                        st.session_state.quiz_score = correct_answers
                        st.session_state.current_question = total_questions
                        st.rerun()
        
        else:
            # Quiz results
            correct_answers = st.session_state.quiz_score
            percentage = (correct_answers / total_questions) * 100
            
            st.subheader("🎉 Quiz Completed!")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Score", f"{correct_answers}/{total_questions}")
            with col2:
                st.metric("Percentage", f"{percentage:.1f}%")
            with col3:
                if percentage >= 70:
                    st.success("PASSED! 🎉")
                else:
                    st.error("Try Again")
            
            # Save results and award points
            save_quiz_result(st.session_state.user_id, module_id, correct_answers, total_questions)
            
            # Points calculation
            base_points = correct_answers * 10
            bonus_points = 0
            
            if percentage >= 90:
                bonus_points = 50
            elif percentage >= 80:
                bonus_points = 25
            
            total_points = base_points + bonus_points
            
            st.success(f"🏆 You earned {total_points} points! ({base_points} base + {bonus_points} bonus)")
            
            # Review answers
            st.subheader("📋 Answer Review")
            
            for i, question in enumerate(questions):
                user_answer = st.session_state.quiz_answers.get(i, 'Not answered')
                correct = user_answer == question['correct_answer']
                
                with st.expander(f"Question {i+1} - {'✅ Correct' if correct else '❌ Incorrect'}"):
                    st.write(f"**Question:** {question['question']}")
                    st.write(f"**Your Answer:** {user_answer}. {question['options'].get(user_answer, 'Not selected')}")
                    st.write(f"**Correct Answer:** {question['correct_answer']}. {question['options'][question['correct_answer']]}")
                    if question['explanation']:
                        st.write(f"**Explanation:** {question['explanation']}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Retake Quiz"):
                    st.session_state.quiz_started = False
                    st.session_state.current_question = 0
                    st.session_state.quiz_answers = {}
                    st.session_state.quiz_score = 0
                    st.rerun()
            
            with col2:
                if st.button("← Back to Module"):
                    st.session_state.quiz_started = False
                    st.session_state.current_page = "module_content"
                    st.rerun()

def show_achievements():
    """Show user achievements and gamification elements"""
    st.markdown('<div class="main-header"><h1>🎖️ Your Achievements</h1></div>', unsafe_allow_html=True)
    
    user_stats = get_user_stats(st.session_state.user_id)
    
    # Overall stats
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h2>🏆 {user_stats['points']}</h2>
            <p>Total Points</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h2>🏅 {len(user_stats['badges'])}</h2>
            <p>Badges Earned</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h2>🔥 {user_stats['streak_days']}</h2>
            <p>Day Streak</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Badges
    st.subheader("🏅 Your Badges")
    
    if user_stats['badges']:
        cols = st.columns(3)
        for i, badge in enumerate(user_stats['badges']):
            with cols[i % 3]:
                st.markdown(f"""
                <div class="achievement-card">
                    <center>
                        <h2>🏅</h2>
                        <h4>{badge}</h4>
                    </center>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No badges earned yet. Complete modules and quizzes to earn badges!")
    
    st.markdown("---")
    
    # Recent achievements
    st.subheader("📈 Recent Activity")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT achievement_name, points_earned, earned_date
            FROM user_achievements
            WHERE user_id = ?
            ORDER BY earned_date DESC
            LIMIT 10
        """, (st.session_state.user_id,))
        
        achievements = cursor.fetchall()
        
        if achievements:
            for achievement in achievements:
                points_text = f"(+{achievement[1]} points)" if achievement[1] > 0 else ""
                st.markdown(f"""
                <div class="module-card">
                    <strong>{achievement[0]}</strong> {points_text}
                    <br><small>{achievement[2]}</small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No recent activity. Start learning to see your progress here!")
    except Exception as e:
        print(f"Error showing achievements: {e}")
    finally:
        conn.close()

def show_admin_dashboard():
    st.markdown('<div class="main-header"><h1>Admin Dashboard</h1></div>', unsafe_allow_html=True)
    
    # System Overview with real data
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT COUNT(*) FROM users WHERE active = 1")
        user_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM modules WHERE active = 1")
        module_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM quizzes")
        quiz_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(points) FROM users WHERE role != 'admin'")
        total_points = cursor.fetchone()[0] or 0
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Users", user_count, "Active users")
        
        with col2:
            st.metric("Modules", module_count, "Published")
        
        with col3:
            st.metric("Quiz Questions", quiz_count, "Available")
        
        with col4:
            st.metric("Total Points Earned", total_points, "By all users")
        
        st.markdown("---")
        
        # Analytics charts
        st.subheader("📊 System Analytics")
        create_admin_analytics_charts()
        
        st.markdown("---")
        
        # Quick Actions
        st.subheader("🚀 Quick Actions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📚 Manage Content", use_container_width=True):
                st.session_state.current_page = "content_management"
                st.rerun()
        
        with col2:
            if st.button("👥 Add User", use_container_width=True):
                st.session_state.current_page = "user_management"
                st.rerun()
        
        with col3:
            if st.button("❓ Add Quiz", use_container_width=True):
                st.session_state.current_page = "quiz_management"
                st.rerun()
    except Exception as e:
        print(f"Error in admin dashboard: {e}")
        st.error("Error loading dashboard data")
    finally:
        conn.close()

def show_content_management():
    st.markdown('<div class="main-header"><h1>Content Management</h1></div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📚 Edit Modules", "➕ Add Module", "🤖 AI Content Tools"])
    
    with tab1:
        st.subheader("Edit Existing Modules")
        
        modules = get_available_modules()
        
        for module in modules:
            difficulty_color = {"Beginner": "🟢", "Intermediate": "🟡", "Advanced": "🔴"}
            color = difficulty_color.get(module['difficulty'], "📚")
            
            with st.expander(f"{color} {module['title']} ({module['difficulty']})"):
                # Get full module data
                full_module = get_module_content(module['id'])
                
                if full_module:
                    with st.form(f"edit_module_{module['id']}"):
                        title = st.text_input("Title", value=full_module['title'])
                        description = st.text_area("Description", value=full_module['description'], height=100)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            difficulty = st.selectbox("Difficulty", ["Beginner", "Intermediate", "Advanced"], 
                                                    index=["Beginner", "Intermediate", "Advanced"].index(full_module['difficulty']))
                        with col2:
                            category = st.selectbox("Category", [
                                "Fundamentals", "Legal Framework", "Property Measurements",
                                "Valuation & Finance", "Technical & Construction", "Transactions & Documentation",
                                "Property Management", "Brokerage & Agency", "Digital Tools", "Case Studies", "Sustainability"
                            ])
                        
                        youtube_url = st.text_input("YouTube URL", value=full_module['youtube_url'] or "", 
                                                  help="Enter YouTube video URL for this module")
                        
                        content = st.text_area("Module Content (Markdown)", value=full_module['content'] or "", 
                                             height=300, help="Use Markdown formatting for better presentation")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.form_submit_button("💾 Update Module"):
                                if update_module_content(module['id'], title, description, content, youtube_url):
                                    st.success("Module updated successfully!")
                                    st.rerun()
                                else:
                                    st.error("Failed to update module")
                        
                        with col2:
                            if st.form_submit_button("🗑️ Delete Module"):
                                if delete_module(module['id']):
                                    st.success("Module deleted!")
                                    st.rerun()
                                else:
                                    st.error("Failed to delete module")
    
    with tab2:
        st.subheader("Add New Module")
        
        with st.form("add_module_form"):
            title = st.text_input("Module Title")
            description = st.text_area("Description", height=100)
            
            col1, col2 = st.columns(2)
            with col1:
                difficulty = st.selectbox("Difficulty Level", ["Beginner", "Intermediate", "Advanced"])
            with col2:
                category = st.selectbox("Category", [
                    "Fundamentals", "Legal Framework", "Property Measurements",
                    "Valuation & Finance", "Technical & Construction", "Transactions & Documentation",
                    "Property Management", "Brokerage & Agency", "Digital Tools", "Case Studies", "Sustainability"
                ])
            
            youtube_url = st.text_input("YouTube URL", help="Enter YouTube video URL for this module")
            content = st.text_area("Module Content (Markdown)", height=300, 
                                 placeholder="Enter detailed content for this module. You can use Markdown formatting.")
            
            if st.form_submit_button("➕ Add Module"):
                if title and description:
                    if add_module(title, description, difficulty, category, content, youtube_url):
                        st.success("Module added successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to add module")
                else:
                    st.error("Please fill in at least title and description")
    
    with tab3:
        st.subheader("🤖 AI Content Enhancement Tools")
        
        # Get DeepSeek API key
        try:
            api_key = st.secrets.get("DEEPSEEK_API_KEY", "sk-54bd3323c4d14bf08b941f0bff7a47d5")
        except:
            api_key = "sk-54bd3323c4d14bf08b941f0bff7a47d5"
        
        deepseek_chat = DeepSeekChat(api_key)
        
        st.write("**Improve Existing Content with AI:**")
        
        modules = get_available_modules()
        selected_module = st.selectbox("Select Module to Improve", 
                                     [f"{m['id']}: {m['title']}" for m in modules])
        
        if selected_module:
            module_id = int(selected_module.split(':')[0])
            improvement_request = st.text_area("What improvements would you like?", 
                                             placeholder="e.g., Add more examples, simplify language, include recent updates...")
            
            if st.button("✨ Improve Content with AI"):
                if improvement_request:
                    with st.spinner("AI is improving the content..."):
                        current_module = get_module_content(module_id)
                        if current_module:
                            improved_content = deepseek_chat.improve_content(
                                current_module['content'], 
                                improvement_request
                            )
                            
                            st.subheader("🎯 AI-Improved Content:")
                            st.markdown(improved_content)
                            
                            if st.button("✅ Apply Improvements"):
                                if update_module_content(module_id, current_module['title'], 
                                                       current_module['description'], improved_content, 
                                                       current_module['youtube_url']):
                                    st.success("Content updated with AI improvements!")
                                    st.rerun()

def show_user_management():
    st.markdown('<div class="main-header"><h1>User Management</h1></div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["👥 Manage Users", "➕ Add New User"])
    
    with tab1:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id, username, email, role, created_date, last_login, active, points, badges
                FROM users
                ORDER BY created_date DESC
            """)
            
            users = cursor.fetchall()
            
            # User statistics
            col1, col2, col3 = st.columns(3)
            
            total_users = len(users)
            active_users = len([u for u in users if u[6] == 1])
            admin_users = len([u for u in users if u[3] == 'admin'])
            
            with col1:
                st.metric("Total Users", total_users)
            with col2:
                st.metric("Active Users", active_users)
            with col3:
                st.metric("Admin Users", admin_users)
            
            st.markdown("---")
            
            st.subheader(f"All Users ({total_users})")
            
            for user in users:
                role_emoji = {"admin": "👑", "student": "📚", "professional": "💼"}
                emoji = role_emoji.get(user[3], "👤")
                status = "🟢 Active" if user[6] else "🔴 Inactive"
                
                badges = json.loads(user[8]) if user[8] else []
                
                with st.expander(f"{emoji} {user[1]} ({user[3]}) - {status} - 🏆 {user[7] or 0} points"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Email:** {user[2]}")
                        st.write(f"**Role:** {user[3].title()}")
                        st.write(f"**Joined:** {user[4]}")
                        st.write(f"**Points:** {user[7] or 0}")
                    
                    with col2:
                        st.write(f"**Last Login:** {user[5] or 'Never'}")
                        st.write(f"**Status:** {'Active' if user[6] else 'Inactive'}")
                        st.write(f"**Badges:** {len(badges)}")
                        
                        if badges:
                            for badge in badges[:3]:  # Show first 3 badges
                                st.markdown(f'<span class="badge">🏅 {badge}</span>', unsafe_allow_html=True)
                    
                    # Admin actions
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if user[3] != 'admin':  # Don't allow deactivating admin users
                            if st.button(f"{'Deactivate' if user[6] else 'Activate'}", key=f"toggle_{user[0]}"):
                                cursor.execute("UPDATE users SET active = ? WHERE id = ?", (0 if user[6] else 1, user[0]))
                                conn.commit()
                                st.success(f"User {'deactivated' if user[6] else 'activated'} successfully!")
                                st.rerun()
                        else:
                            st.info("Admin user")
                    
                    with col2:
                        points_to_award = st.number_input(f"Award Points", min_value=0, max_value=1000, value=50, key=f"points_{user[0]}")
                        if st.button("🏆 Award", key=f"award_{user[0]}"):
                            award_points(user[0], points_to_award, "Admin Awarded Points")
                            st.success(f"Awarded {points_to_award} points!")
                            st.rerun()
                    
                    with col3:
                        badge_options = ["Excellence", "Top Performer", "Quick Learner", "Dedicated Student", "Expert Level"]
                        selected_badge = st.selectbox("Award Badge", badge_options, key=f"badge_{user[0]}")
                        if st.button("🏅 Badge", key=f"badge_btn_{user[0]}"):
                            award_badge(user[0], selected_badge)
                            st.success(f"Badge '{selected_badge}' awarded!")
                            st.rerun()
        except Exception as e:
            st.error(f"Error loading users: {e}")
        finally:
            conn.close()
    
    with tab2:
        st.subheader("Add New User")
        
        with st.form("add_user_form"):
            username = st.text_input("Username")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            role = st.selectbox("Role", ["student", "professional", "admin"])
            
            if st.form_submit_button("➕ Create User"):
                if username and email and password:
                    success, message = create_user_by_admin(username, email, password, role)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.error("Please fill all fields")

def show_quiz_management():
    st.markdown('<div class="main-header"><h1>❓ Quiz Management</h1></div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📝 Manage Questions", "➕ Add Questions", "🤖 AI Generate"])
    
    with tab1:
        st.subheader("Existing Quiz Questions")
        
        modules = get_available_modules()
        
        for module in modules:
            questions = get_quiz_questions(module['id'])
            
            with st.expander(f"📚 {module['title']} ({len(questions)} questions)"):
                if questions:
                    for i, question in enumerate(questions, 1):
                        st.write(f"**Q{i}:** {question['question']}")
                        st.write(f"**Options:** A) {question['options']['A']}, B) {question['options']['B']}, C) {question['options']['C']}, D) {question['options']['D']}")
                        st.write(f"**Correct:** {question['correct_answer']}")
                        if question['explanation']:
                            st.write(f"**Explanation:** {question['explanation']}")
                        st.markdown("---")
                else:
                    st.info("No questions available for this module")
    
    with tab2:
        st.subheader("Add New Quiz Question")
        
        modules = get_available_modules()
        selected_module = st.selectbox("Select Module", 
                                     [(m['id'], m['title']) for m in modules],
                                     format_func=lambda x: x[1])
        
        if selected_module:
            with st.form("add_question_form"):
                question = st.text_area("Question", height=100)
                
                col1, col2 = st.columns(2)
                with col1:
                    option_a = st.text_input("Option A")
                    option_c = st.text_input("Option C")
                with col2:
                    option_b = st.text_input("Option B")
                    option_d = st.text_input("Option D")
                
                correct_answer = st.selectbox("Correct Answer", ["A", "B", "C", "D"])
                explanation = st.text_area("Explanation (Optional)", height=80)
                
                if st.form_submit_button("➕ Add Question"):
                    if question and option_a and option_b and option_c and option_d:
                        if add_quiz_question(
        selected_module[0],
        q['question'],
        q['option_a'],
        q['option_b'],
        q['option_c'],
        q['option_d'],
        q['correct_answer'],
        q['explanation']
):
    st.success(f"Question {i} added successfully!")
    st.rerun()

                        else:
                            st.error("Failed to add question")
                    else:
                        st.error("Please fill all required fields")
    
    with tab3:
        st.subheader("🤖 AI Question Generator")
        
        # Get DeepSeek API key
        try:
            api_key = st.secrets.get("DEEPSEEK_API_KEY", "sk-54bd3323c4d14bf08b941f0bff7a47d5")
        except:
            api_key = "sk-54bd3323c4d14bf08b941f0bff7a47d5"
        
        deepseek_chat = DeepSeekChat(api_key)
        
        modules = get_available_modules()
        selected_module = st.selectbox("Select Module for AI Generation", 
                                     [(m['id'], m['title']) for m in modules],
                                     format_func=lambda x: x[1])
        
        if selected_module:
            module_data = next(m for m in modules if m['id'] == selected_module[0])
            
            col1, col2 = st.columns(2)
            with col1:
                difficulty = st.selectbox("Question Difficulty", ["Beginner", "Intermediate", "Advanced"])
            with col2:
                question_count = st.number_input("Number of Questions", min_value=1, max_value=10, value=5)
            
            if st.button("🤖 Generate Questions with AI"):
                with st.spinner("AI is generating quiz questions..."):
                    result = deepseek_chat.generate_quiz_questions(
                        module_data['title'], 
                        difficulty, 
                        question_count
                    )
                    
                    if result and 'questions' in result:
                        st.subheader(f"🎯 Generated {len(result['questions'])} Questions:")
                        
                        for i, q in enumerate(result['questions'], 1):
                            with st.expander(f"Question {i}"):
                                st.write(f"**Question:** {q['question']}")
                                st.write(f"**A)** {q['option_a']}")
                                st.write(f"**B)** {q['option_b']}")
                                st.write(f"**C)** {q['option_c']}")
                                st.write(f"**D)** {q['option_d']}")
                                st.write(f"**Correct Answer:** {q['correct_answer']}")
                                st.write(f"**Explanation:** {q['explanation']}")
                                
                                if st.button(f"✅ Add Question {i}", key=f"add_ai_q_{i}"):
                                    if add_quiz_question(
    selected_module[0],
    q['question'],
    q['option_a'],
    q['option_b'],
    q['option_c'],
    q['option_d'],
    q['correct_answer'],
    q['explanation']
):

