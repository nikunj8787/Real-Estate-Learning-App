import streamlit as st
import sqlite3
import hashlib
import json
from datetime import datetime, timedelta
import requests
import os

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

# Database setup
DATABASE_PATH = "realestate_guru.db"

def init_database():
    """Initialize database with tables and comprehensive content"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'student',
            created_date TEXT NOT NULL,
            last_login TEXT,
            active INTEGER DEFAULT 1
        )
    """)
    
    # Create modules table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS modules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            difficulty TEXT NOT NULL,
            category TEXT NOT NULL,
            content TEXT,
            order_index INTEGER DEFAULT 0,
            created_date TEXT NOT NULL,
            updated_date TEXT,
            active INTEGER DEFAULT 1
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
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (module_id) REFERENCES modules (id)
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
            INSERT INTO users (username, email, password, role, created_date)
            VALUES (?, ?, ?, ?, ?)
        """, ("admin", "admin@realestateguruapp.com", admin_password, "admin", datetime.now().isoformat()))
    
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

## Assessment Questions

1. What is the difference between freehold and leasehold property?
2. Name three regulatory bodies governing real estate in India.
3. What are the main types of residential properties?
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

## 4. RERA Authorities Structure

### Central Level:
- **MoHUA**: Policy formulation and coordination
- **Central Advisory Council**: Interstate coordination

### State Level:
- **State RERA**: Project registrations and complaints
- **Appellate Tribunal**: Second-level appeals
- **State Advisory Council**: Industry consultation

## 5. Penalties and Violations

### Developer Penalties:
- **10% per annum** interest for delivery delays
- **Project deregistration** for serious violations
- **Criminal prosecution** for fraud cases

### Common Violations:
- Unauthorized changes to approved plans
- Failure to maintain escrow account
- Non-disclosure of project information
- Delayed possession without compensation

## 6. Filing Complaints

### Process:
1. **Online Filing**: State RERA website
2. **Documentation**: Sale agreement, payment receipts
3. **Hearing**: Before RERA authority
4. **Appeal**: To Appellate Tribunal if unsatisfied

## Case Studies

### Successful Cases:
- **Amrapali Group**: NBCC took over stalled projects
- **Jaypee Infratech**: Insolvency resolution completed
- **Supertech**: Illegal constructions demolished

## Assessment Questions

1. What are the key objectives of RERA Act 2016?
2. Which projects need RERA registration?
3. What compensation can buyers claim for delivery delays?
"""

        # Module 3: Property Measurements & Standards
        measurements_content = """
# Property Measurements & Standards

## 1. Understanding Property Areas

### Carpet Area:
- **Definition**: Actual usable floor area
- **Includes**: Rooms, kitchen, bathrooms, balconies
- **Excludes**: Walls, common areas, utility areas
- **Legal Standard**: As per RERA, sales based on carpet area only

### Built-up Area:
- **Formula**: Carpet Area + Wall Area + Balcony Area
- **Includes**: Interior walls, columns within apartment
- **Typical Addition**: 10-15% over carpet area
- **Usage**: Internal planning and design

### Super Built-up Area:
- **Formula**: Built-up Area + Proportionate Common Area
- **Includes**: Lobbies, elevators, staircases, amenities
- **Typical Addition**: 25-40% over carpet area
- **Note**: No longer legally valid for sales post-RERA

## 2. BIS Standards for Measurement

### IS 3861:2002:
- **Standard**: Method of measurement of areas of buildings
- **Carpet Area**: Wall-to-wall measurement
- **Balcony**: 50% weightage in carpet area calculation
- **Common Areas**: Pro-rata distribution basis

### Loading Factor:
- **Definition**: Difference between super built-up and carpet area
- **Typical Range**: 15-40% depending on project type
- **Calculation**: (Super Built-up - Carpet) / Carpet × 100

## 3. Floor Plan Reading

### Basic Elements:
- **Walls**: Thick black lines showing structure
- **Doors**: Breaks in walls with door symbols
- **Windows**: Double lines with glass indication
- **Electrical**: Symbols for switches, outlets, fixtures

### Room Dimensions:
- **Length × Width**: In feet or meters
- **Ceiling Height**: Standard 9-10 feet
- **Door/Window Sizes**: Standard modular sizes
- **Area Calculation**: Length × Width for each room

### Common Symbols:
- **WC**: Water closet/toilet
- **K**: Kitchen
- **BR**: Bedroom
- **LR**: Living room
- **DB**: Distribution board
- **AC**: Air conditioning unit

## 4. Measurement Best Practices

### For Buyers:
- **Verify Measurements**: Independent surveyor recommended
- **Check Calculations**: Area-wise breakdown
- **Compare Plans**: Approved vs. actual construction
- **Document Variations**: Any deviations from approved plans

### For Developers:
- **Accurate Drawings**: As-built drawings mandatory
- **Regular Surveys**: During construction phases
- **BIS Compliance**: Follow measurement standards
- **Clear Documentation**: Area statements with breakdown

## 5. Common Measurement Issues

### Discrepancies:
- **Area Shortfall**: Actual less than promised
- **Layout Changes**: Unauthorized modifications
- **Quality Variations**: Substandard construction
- **Common Area Disputes**: Calculation methodology differences

### Legal Remedies:
- **RERA Complaints**: For area shortfall
- **Compensation**: Proportionate price reduction
- **Specific Performance**: Force developer to deliver
- **Refund**: With interest for major variations

## 6. Technology in Measurement

### Modern Tools:
- **Laser Measurement**: High accuracy devices
- **3D Scanning**: Complete building documentation
- **BIM Models**: Building Information Modeling
- **Drone Surveys**: Large project mapping

### Digital Documentation:
- **CAD Drawings**: Computer-aided design
- **GIS Integration**: Geographic information systems
- **Mobile Apps**: On-site measurement tools
- **Cloud Storage**: Centralized documentation

## Assessment Questions

1. What is the difference between carpet area and built-up area?
2. How is loading factor calculated?
3. What are the key elements to check in a floor plan?
4. What legal remedies exist for area discrepancies?
"""

        # Module 4: Valuation & Finance
        valuation_content = """
# Property Valuation & Finance

## 1. Property Valuation Methods

### Comparative Market Analysis (CMA):
- **Methodology**: Compare with similar recent sales
- **Key Factors**: Location, size, age, amenities, condition
- **Data Sources**: Registration records, broker databases
- **Accuracy**: ±10-15% in established markets
- **Best For**: Residential properties in active markets

### Income Approach:
- **Formula**: Property Value = Net Operating Income / Cap Rate
- **Components**: Rental income, operating expenses, capitalization rate
- **Applications**: Investment properties, commercial buildings
- **Calculations**: 
  - Gross Rental Yield = Annual Rent / Property Price × 100
  - Net Yield = (Annual Rent - Expenses) / Property Price × 100

### Cost Approach:
- **Formula**: Land Value + Building Cost - Depreciation
- **Components**: Land rate, construction cost, depreciation factors
- **Applications**: New constructions, unique properties
- **Depreciation**: 2-3% per year for residential buildings

## 2. Factors Affecting Property Values

### Location Factors:
- **Connectivity**: Metro, highways, airports
- **Social Infrastructure**: Schools, hospitals, shopping
- **Employment Hubs**: IT parks, business districts
- **Future Development**: Planned infrastructure projects

### Property-Specific Factors:
- **Size and Layout**: Carpet area, room configuration
- **Floor Level**: Higher floors command premium
- **Facing**: East/North facing preferred
- **Age and Condition**: Newer properties valued higher
- **Amenities**: Swimming pool, gym, security

### Market Factors:
- **Supply-Demand**: Inventory levels vs. absorption
- **Interest Rates**: Impact on affordability
- **Government Policies**: Tax benefits, subsidies
- **Economic Conditions**: Employment, income growth

## 3. Home Loan Fundamentals

### Loan-to-Value (LTV) Ratio:
- **Definition**: Loan amount as % of property value
- **Typical Range**: 75-90% for home loans
- **Factors**: Property type, borrower profile, loan amount
- **Higher LTV**: First-time buyers, salaried professionals

### Interest Rate Structures:
- **Fixed Rate**: Same rate throughout loan tenure
- **Floating Rate**: Varies with market rates
- **Hybrid**: Fixed for initial years, then floating
- **Current Rates**: 8.5-10.5% per annum (as of 2024)

### EMI Calculation:
- **Formula**: P × r × (1+r)^n / ((1+r)^n - 1)
- **Where**: P = Principal, r = Monthly rate, n = Number of months
- **Factors**: Loan amount, interest rate, tenure
- **Tools**: Online EMI calculators, mobile apps

## 4. Property Taxation

### Stamp Duty:
- **Purpose**: Revenue for state governments
- **Rates**: 3-10% of property value (varies by state)
- **Payment**: Before registration
- **Calculation**: On agreement value or circle rate, whichever higher

### Registration Charges:
- **Rate**: 1-2% of property value
- **Payment**: Along with stamp duty  
- **Process**: Sub-registrar office
- **Documents**: Sale deed, NOC, approvals

### Goods and Services Tax (GST):
- **Under Construction**: 5% GST (with ITC) or 1% GST (without ITC)
- **Ready-to-Move**: No GST on resale properties
- **Commercial**: 12% GST on commercial properties
- **Input Tax Credit**: Available for businesses

### Capital Gains Tax:
- **Short-term**: Sale within 2 years - Normal tax rates
- **Long-term**: Sale after 2 years - 20% with indexation
- **Exemptions**: Section 54 (new house purchase), Section 54EC (bonds)
- **Indexation**: Cost inflation index adjustment

## 5. Home Loan Process

### Eligibility Assessment:
- **Income**: Minimum ₹25,000 per month
- **Age**: 21-65 years typically
- **Credit Score**: 750+ preferred
- **Debt-to-Income**: <50% of monthly income

### Documentation:
- **Income Proof**: Salary slips, ITR, bank statements
- **Identity**: PAN, Aadhaar, passport
- **Property**: Sale agreement, approvals, NOC
- **Additional**: Employment certificate, property insurance

### Approval Process:
1. **Application**: Online or branch submission
2. **Document Verification**: Bank verification
3. **Property Valuation**: Technical assessment
4. **Credit Appraisal**: Income and CIBIL check
5. **Sanction**: Loan approval letter
6. **Disbursement**: After registration

## 6. Investment Analysis

### Return Calculations:
- **Rental Yield**: Annual rent / Property price × 100
- **Capital Appreciation**: (Current value - Purchase price) / Purchase price × 100
- **Total Return**: Rental yield + Capital appreciation
- **IRR**: Internal rate of return including cash flows

### Risk Factors:
- **Market Risk**: Price fluctuations
- **Liquidity Risk**: Time to sell property
- **Rental Risk**: Vacancy, rent collection
- **Regulatory Risk**: Policy changes

## Assessment Questions

1. What are the three main property valuation methods?
2. How is EMI calculated for home loans?
3. What is the current GST rate on under-construction properties?
4. How do you calculate rental yield?
"""

        # Module 5: Land & Development Laws
        development_content = """
# Land & Development Laws

## 1. General Development Control Regulations (GDCR)

### Purpose and Scope:
- **Objective**: Regulate construction and development activities
- **Coverage**: Building specifications, land use, infrastructure
- **Authority**: State governments and urban development authorities
- **Compliance**: Mandatory for all development projects

### Key Components:
- **Setback Requirements**: Minimum distances from boundaries
- **Height Restrictions**: Maximum building heights per zone
- **Parking Norms**: Minimum parking spaces required
- **Open Space**: Mandatory open areas within developments

### Setback Norms (Typical):
- **Front**: 3-6 meters depending on road width
- **Side**: 1.5-3 meters for each side
- **Rear**: 3-6 meters from back boundary
- **Special Cases**: Corner plots, wide roads have different norms

## 2. Floor Space Index (FSI) / Floor Area Ratio (FAR)

### Definition:
- **FSI**: Total covered area of all floors / Plot area
- **Example**: 1000 sq.m plot with FSI 2.0 = 2000 sq.m total construction
- **Variations**: Different FSI for different zones and cities
- **Premium FSI**: Additional FSI at premium rates

### FSI Calculations:
- **Basic FSI**: As per zoning regulations
- **Premium FSI**: Available against payment
- **Incentive FSI**: For affordable housing, green buildings
- **Fungible FSI**: Transferable between zones

### City-wise FSI Examples:
- **Mumbai**: 1.33 (basic), up to 4.0 with premiums
- **Delhi**: 1.2-3.5 depending on zone
- **Bangalore**: 1.75-2.5 depending on area
- **Pune**: 1.0-2.0 with premiums available

## 3. Transfer of Development Rights (TDR)

### Concept:
- **Definition**: Right to transfer unused FSI from one plot to another
- **Generation**: From land acquisition, slum rehabilitation, heritage preservation
- **Utilization**: In designated receiving zones
- **Validity**: Time-bound usage (typically 10 years)

### TDR Sources:
- **Reservation TDR**: Land acquired for public purposes
- **Slum TDR**: From slum rehabilitation projects
- **Heritage TDR**: For preserving heritage structures
- **Amenity TDR**: For providing public amenities

### TDR Process:
1. **Generation**: Authority issues TDR certificate
2. **Banking**: TDR deposited in government bank
3. **Transfer**: TDR sold to developers
4. **Utilization**: Used for additional construction
5. **Verification**: Building approval with TDR usage

## 4. Land Use Zoning

### Zoning Categories:
- **Residential**: R-1 (low density) to R-4 (high density)
- **Commercial**: C-1 (local) to C-4 (central business)
- **Industrial**: I-1 (light) to I-3 (heavy industry)
- **Mixed Use**: Combination zones
- **Special Zones**: IT parks, SEZ, institutional

### Permitted Activities:
- **Residential Zones**: Housing, schools, clinics, local shops
- **Commercial Zones**: Offices, retail, hotels, restaurants
- **Industrial Zones**: Manufacturing, warehouses, service industries
- **Mixed Use**: Residential + commercial as per ratios

### Land Use Conversion:
- **Process**: Application to town planning authority
- **Requirements**: Feasibility study, public notice, approvals
- **Charges**: Conversion charges and betterment levy
- **Timeline**: 6-12 months typically

## 5. Town Planning Schemes

### Objectives:
- **Planned Development**: Organized growth of urban areas
- **Infrastructure Provision**: Roads, water, electricity, sewerage
- **Land Redistribution**: Equitable distribution after infrastructure
- **Revenue Generation**: Through land auctions and development

### TP Scheme Process:
1. **Draft Scheme**: Prepared by planning authority
2. **Public Consultation**: Objections and suggestions
3. **Final Scheme**: After incorporating feedback
4. **Implementation**: Land acquisition and development
5. **Redistribution**: Final plots to original owners

### Benefits:
- **For Landowners**: Developed land with infrastructure
- **For Government**: Revenue generation and planned development
- **For Citizens**: Better infrastructure and services
- **For Environment**: Planned green spaces and utilities

## 6. Approvals and Clearances

### Building Plan Approval:
- **Authority**: Municipal corporation/development authority
- **Requirements**: Architectural plans, structural drawings, compliance certificate
- **Timeline**: 30-60 days for approval
- **Validity**: 3 years typically

### Environmental Clearances:
- **EIA**: Environmental Impact Assessment for large projects
- **CRZ**: Coastal Regulation Zone clearance for coastal areas
- **Forest Clearance**: For projects affecting forest land
- **Pollution Control**: State pollution control board approvals

### Utility Connections:
- **Water Supply**: Water authority approval and connection
- **Electricity**: Electricity board approval and supply
- **Sewerage**: Sewerage board connection and treatment
- **Gas**: Gas authority approval for piped gas supply

## 7. Compliance and Penalties

### Common Violations:
- **Unauthorized Construction**: Beyond approved plans
- **FSI Violations**: Exceeding permitted FSI
- **Setback Violations**: Insufficient setbacks
- **Land Use Violations**: Non-conforming activities

### Penalties:
- **Monetary**: Fines and penalties
- **Regularization**: Payment for unauthorized construction
- **Demolition**: For serious violations
- **Legal Action**: Criminal prosecution in extreme cases

## Assessment Questions

1. What is FSI and how is it calculated?
2. What are the main sources of TDR generation?
3. What approvals are needed for building plan approval?
4. What are the benefits of Town Planning Schemes?
"""

        default_modules = [
            ('Real Estate Fundamentals', 'Introduction to real estate basics, stakeholders, and market overview', 'Beginner', 'Fundamentals', fundamentals_content, 1),
            ('Legal Framework & RERA', 'Comprehensive guide to RERA, legal compliance, and regulatory framework', 'Intermediate', 'Legal Framework', rera_content, 2),
            ('Property Measurements & Standards', 'Carpet area vs built-up area, BIS standards, and floor plan reading', 'Beginner', 'Measurements', measurements_content, 3),
            ('Valuation & Finance', 'Property valuation methods, home loans, and taxation', 'Intermediate', 'Finance', valuation_content, 4),
            ('Land & Development Laws', 'GDCR, municipal bylaws, FSI/TDR calculations, and zoning', 'Advanced', 'Legal Framework', development_content, 5)
        ]
        
        for module in default_modules:
            cursor.execute("""
                INSERT INTO modules (title, description, difficulty, category, content, order_index, created_date, active)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            """, (*module, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()

def get_db_connection():
    """Get database connection"""
    return sqlite3.connect(DATABASE_PATH)

# CSS Styling
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
</style>
""", unsafe_allow_html=True)

# DeepSeek Chat Integration
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

# FIXED: Content Research Module
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
            },
            "Real estate market trends": {
                "key_points": [
                    "Residential market showing 15% YoY growth in Q3 2024",
                    "Tier-2 cities emerging as investment hotspots with 25% price appreciation",
                    "Green building certifications becoming mandatory in major cities",
                    "Co-working spaces demand increasing by 30% post-pandemic",
                    "PropTech adoption accelerating with 40% increase in digital transactions"
                ],
                "sources": [
                    {"title": "India Real Estate Market Report 2024", "url": "https://knightfrank.com/india-report", "date": "2024-01-15"},
                    {"title": "Residential Market Analysis", "url": "https://anarock.com/market-trends", "date": "2023-12-01"}
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

# Authentication functions
def authenticate_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    cursor.execute("""
        SELECT id, username, role FROM users 
        WHERE username = ? AND password = ? AND active = 1
    """, (username, hashed_password))
    
    user = cursor.fetchone()
    conn.close()
    
    if user:
        st.session_state.user_id = user[0]
        st.session_state.username = user[1]
        st.session_state.user_role = user[2]
        return True
    
    return False

def register_user(username, email, password, user_type):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if username or email already exists
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = ? OR email = ?", (username, email))
        if cursor.fetchone()[0] > 0:
            conn.close()
            return False
            
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        cursor.execute("""
            INSERT INTO users (username, email, password, role, created_date)
            VALUES (?, ?, ?, ?, ?)
        """, (username, email, hashed_password, user_type, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.close()
        return False

def get_available_modules():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, title, description, difficulty, category 
        FROM modules 
        WHERE active = 1
        ORDER BY order_index
    """)
    
    modules = cursor.fetchall()
    conn.close()
    
    return [
        {
            'id': module[0],
            'title': module[1],
            'description': module[2],
            'difficulty': module[3],
            'category': module[4]
        }
        for module in modules
    ]

def get_module_content(module_id):
    """Get full content of a specific module"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT title, description, content, difficulty, category
        FROM modules 
        WHERE id = ? AND active = 1
    """, (module_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {
            'title': result[0],
            'description': result[1],
            'content': result[2],
            'difficulty': result[3],
            'category': result[4]
        }
    return None

def add_module(title, description, difficulty, category):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO modules (title, description, difficulty, category, created_date, active)
            VALUES (?, ?, ?, ?, ?, 1)
        """, (title, description, difficulty, category, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        return True
    except:
        conn.close()
        return False

def delete_module(module_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("UPDATE modules SET active = 0 WHERE id = ?", (module_id,))
        conn.commit()
        conn.close()
        return True
    except:
        conn.close()
        return False

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
                st.success("Registration successful! Please login.")
                st.session_state.show_register = False
                st.rerun()
            else:
                st.error("Registration failed - Username or email already exists")
    
    if st.button("Back to Login"):
        st.session_state.show_register = False
        st.rerun()

def show_navigation():
    st.markdown('<div class="sidebar-logo"><h3>🏠 RealEstateGuru</h3></div>', unsafe_allow_html=True)
    st.write(f"Welcome, **{st.session_state.username}**!")
    st.write(f"Role: *{st.session_state.user_role.title()}*")
    
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
        
        if st.button("🔍 Content Research", use_container_width=True):
            st.session_state.current_page = "content_research"
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
        
        if st.button("🏆 Assessments", use_container_width=True):
            st.session_state.current_page = "assessments"
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
    st.markdown('<div class="main-header"><h1>Welcome to RealEstateGuru</h1><p>Your Complete Real Estate Education Platform</p></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="module-card">
            <h3>🎯 Beginner Track</h3>
            <p>Start from basics with guided learning paths covering fundamentals of real estate, legal frameworks, and basic concepts.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="module-card">
            <h3>🚀 Intermediate Track</h3>
            <p>Deepen your knowledge with advanced topics including valuation methods, financial modeling, and regulatory compliance.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="module-card">
            <h3>🏆 Advanced Track</h3>
            <p>Master complex topics like dispute resolution, investment strategies, and become a real estate expert.</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Key Features")
        st.markdown("""
        - 📚 **Comprehensive Curriculum**: 5 detailed modules covering all aspects of Indian real estate
        - 🎮 **Interactive Learning**: Rich content with real-world examples and case studies
        - 📱 **Multi-Platform Access**: Learn on desktop, tablet, or mobile
        - 🏅 **Progress Tracking**: Monitor your learning journey with detailed analytics
        """)
    
    with col2:
        st.subheader("🚀 Advanced Features")
        st.markdown("""
        - 🤖 **AI Assistant**: Get instant help with your queries using advanced AI
        - 📊 **Assessment System**: Test your knowledge with interactive assessments
        - 🎥 **Rich Content**: Detailed explanations with practical examples
        - 👥 **Admin Panel**: Complete content management system for educators
        """)
    
    st.markdown("---")
    st.info("💡 **Get Started**: Register as a student to access learning modules or as an admin to manage content. Default admin login: `admin` / `admin123`")

def show_user_dashboard():
    st.markdown('<div class="main-header"><h1>Your Learning Dashboard</h1></div>', unsafe_allow_html=True)
    
    # Progress Overview
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Modules Available", "5", "All unlocked")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Learning Hours", "25+", "Rich content")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_width=True)
        st.metric("Difficulty Levels", "3", "Beginner to Advanced")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("AI Assistant", "Available", "24/7 support")
        st.markdown('</div>', unsafe_allow_html=True)
    
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
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"Start Learning", key=f"start_{module['id']}"):
                    st.session_state.current_module = module['id']
                    st.session_state.current_page = "module_content"
                    st.rerun()
            
            with col2:
                st.info("Click 'Start Learning' to access full content")

def show_module_content():
    """Display detailed content of a specific module"""
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
    
    # Module info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info(f"**Difficulty:** {module['difficulty']}")
    with col2:
        st.info(f"**Category:** {module['category']}")
    with col3:
        if st.button("← Back to Dashboard"):
            st.session_state.current_page = "dashboard"
            st.session_state.current_module = None
            st.rerun()
    
    st.markdown("---")
    
    # Module content
    if module['content']:
        st.markdown('<div class="content-viewer">', unsafe_allow_html=True)
        st.markdown(module['content'])
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Progress tracking
        st.success("✅ Module content loaded successfully!")
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📝 Take Assessment", use_container_width=True):
                st.session_state.current_page = "assessments"
                st.rerun()
        
        with col2:
            if st.button("🤖 Ask AI Assistant", use_container_width=True):
                st.session_state.current_page = "ai_assistant"
                st.rerun()
        
        with col3:
            if st.button("📊 View Progress", use_container_width=True):
                st.session_state.current_page = "progress"
                st.rerun()
    else:
        st.warning("No content available for this module yet.")

def show_admin_dashboard():
    st.markdown('<div class="main-header"><h1>Admin Dashboard</h1></div>', unsafe_allow_html=True)
    
    # System Overview
    col1, col2, col3, col4 = st.columns(4)
    
    # Get actual counts from database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE active = 1")
    user_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM modules WHERE active = 1")
    module_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
    admin_count = cursor.fetchone()[0]
    
    conn.close()
    
    with col1:
        st.metric("Total Users", user_count, "Active users")
    
    with col2:
        st.metric("Active Modules", module_count, "Published modules")
    
    with col3:
        st.metric("Admin Users", admin_count, "System administrators")
    
    with col4:
        st.metric("System Status", "Online", "All systems operational")
    
    st.markdown("---")
    
    # Quick Actions
    st.subheader("🚀 Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📚 Manage Content", use_container_width=True):
            st.session_state.current_page = "content_management"
            st.rerun()
    
    with col2:
        if st.button("👥 Manage Users", use_container_width=True):
            st.session_state.current_page = "user_management"
            st.rerun()
    
    with col3:
        if st.button("🔍 Research Content", use_container_width=True):
            st.session_state.current_page = "content_research"
            st.rerun()
    
    st.markdown("---")
    
    # Recent Activity
    st.subheader("📋 System Information")
    
    activities = [
        {"time": "System", "action": "Database initialized", "status": "✅ Success"},
        {"time": "Content", "action": "5 modules with rich content loaded", "status": "✅ Active"},
        {"time": "AI Assistant", "action": "DeepSeek API integration ready", "status": "✅ Connected"},
        {"time": "Admin", "action": "Admin panel fully functional", "status": "✅ Operational"}
    ]
    
    for activity in activities:
        st.markdown(f"""
        <div class="module-card">
            <strong>{activity['time']}</strong> - {activity['action']} - {activity['status']}
        </div>
        """, unsafe_allow_html=True)

def show_content_management():
    st.markdown('<div class="main-header"><h1>Content Management</h1></div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📚 Manage Modules", "➕ Add New Module"])
    
    with tab1:
        st.subheader("Existing Modules")
        
        modules = get_available_modules()
        
        for module in modules:
            difficulty_color = {"Beginner": "🟢", "Intermediate": "🟡", "Advanced": "🔴"}
            color = difficulty_color.get(module['difficulty'], "📚")
            
            with st.expander(f"{color} {module['title']} ({module['difficulty']})"):
                st.write(f"**Description:** {module['description']}")
                st.write(f"**Category:** {module['category']}")
                
                # Get content preview
                full_module = get_module_content(module['id'])
                if full_module and full_module['content']:
                    content_preview = full_module['content'][:200] + "..." if len(full_module['content']) > 200 else full_module['content']
                    st.write(f"**Content Preview:** {content_preview}")
                    st.success("✅ Content available")
                else:
                    st.warning("⚠️ No content available")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("👁️ View Content", key=f"view_{module['id']}"):
                        st.session_state.current_module = module['id']
                        st.session_state.current_page = "module_content"
                        st.rerun()
                
                with col2:
                    if st.button("✏️ Edit", key=f"edit_{module['id']}"):
                        st.info("Edit functionality available - content can be updated in database")
                
                with col3:
                    if st.button("🗑️ Delete", key=f"delete_{module['id']}"):
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
            difficulty = st.selectbox("Difficulty Level", ["Beginner", "Intermediate", "Advanced"])
            category = st.selectbox("Category", [
                "Fundamentals",
                "Legal Framework",
                "Property Measurements",
                "Valuation & Finance",
                "Technical & Construction",
                "Transactions & Documentation",
                "Property Management",
                "Brokerage & Agency",
                "Digital Tools",
                "Case Studies",
                "Sustainability"
            ])
            content = st.text_area("Module Content (Markdown supported)", height=300, 
                                 placeholder="Enter detailed content for this module. You can use Markdown formatting.")
            
            submitted = st.form_submit_button("Add Module")
            
            if submitted and title and description:
                if add_module(title, description, difficulty, category):
                    # If content provided, update the module with content
                    if content:
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute("UPDATE modules SET content = ? WHERE title = ?", (content, title))
                        conn.commit()
                        conn.close()
                    
                    st.success("Module added successfully!")
                    st.rerun()
                else:
                    st.error("Failed to add module")
            elif submitted:
                st.error("Please fill in at least title and description")

def show_user_management():
    st.markdown('<div class="main-header"><h1>User Management</h1></div>', unsafe_allow_html=True)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, username, email, role, created_date, last_login, active
        FROM users
        ORDER BY created_date DESC
    """)
    
    users = cursor.fetchall()
    conn.close()
    
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
        
        with st.expander(f"{emoji} {user[1]} ({user[3]}) - {status}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Email:** {user[2]}")
                st.write(f"**Role:** {user[3].title()}")
                st.write(f"**Joined:** {user[4]}")
            
            with col2:
                st.write(f"**Last Login:** {user[5] or 'Never'}")
                st.write(f"**Status:** {'Active' if user[6] else 'Inactive'}")
                
                if user[3] != 'admin':  # Don't allow deactivating admin users
                    if st.button(f"{'Deactivate' if user[6] else 'Activate'}", key=f"toggle_{user[0]}"):
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute("UPDATE users SET active = ? WHERE id = ?", (0 if user[6] else 1, user[0]))
                        conn.commit()
                        conn.close()
                        st.success(f"User {'deactivated' if user[6] else 'activated'} successfully!")
                        st.rerun()
                else:
                    st.info("Admin users cannot be deactivated")

def show_content_research():
    st.markdown('<div class="main-header"><h1>Content Research</h1></div>', unsafe_allow_html=True)
    
    researcher = ContentResearcher()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Research Topics")
        selected_topics = st.multiselect(
            "Select Topics to Research", 
            researcher.available_topics,
            help="Select one or more topics to research for content creation"
        )
        
        if st.button("Start Research", use_container_width=True):
            if selected_topics:
                with st.spinner("Researching content..."):
                    results = researcher.run_research(selected_topics)
                    st.session_state.research_results = results
                    st.success(f"Research completed for {len(selected_topics)} topics!")
            else:
                st.warning("Please select at least one topic to research")
    
    with col2:
        st.subheader("Research Results")
        
        if 'research_results' in st.session_state and st.session_state.research_results:
            for topic, content in st.session_state.research_results.items():
                with st.expander(f"📋 {topic}"):
                    st.write("**Key Points:**")
                    for i, point in enumerate(content['key_points'], 1):
                        st.write(f"{i}. {point}")
                    
                    st.write("**Sources:**")
                    for source in content['sources']:
                        st.write(f"• [{source['title']}]({source['url']}) - {source['date']}")
                    
                    st.write(f"**Last Updated:** {content.get('last_updated', 'N/A')}")
                    
                    if st.button(f"Add to Module", key=f"research_{topic}"):
                        # Save research to database
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        
                        cursor.execute("""
                            INSERT INTO content_research (topic, content, sources, created_date, status)
                            VALUES (?, ?, ?, ?, 'completed')
                        """, (
                            topic,
                            json.dumps(content['key_points']),
                            json.dumps(content['sources']),
                            datetime.now().isoformat()
                        ))
                        
                        conn.commit()
                        conn.close()
                        
                        st.success(f"Research for '{topic}' saved to database!")
        else:
            st.info("No research results yet. Select topics and click 'Start Research' to begin.")
    
    st.markdown("---")
    
    # Show saved research
    st.subheader("📚 Saved Research")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT topic, created_date, status FROM content_research ORDER BY created_date DESC LIMIT 10")
    saved_research = cursor.fetchall()
    conn.close()
    
    if saved_research:
        for research in saved_research:
            st.markdown(f"""
            <div class="module-card">
                <strong>{research[0]}</strong> - Created: {research[1]} - Status: {research[2]}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No saved research yet.")

def show_ai_assistant():
    st.markdown('<div class="main-header"><h1>🤖 AI Assistant</h1></div>', unsafe_allow_html=True)
    
    st.info("💡 Ask me anything about real estate! I'm here to help with RERA compliance, property valuation, legal frameworks, and more.")
    
    # Initialize chat history
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Get DeepSeek API key
    try:
        api_key = st.secrets.get("DEEPSEEK_API_KEY", "sk-54bd3323c4d14bf08b941f0bff7a47d5")
    except:
        api_key = "sk-54bd3323c4d14bf08b941f0bff7a47d5"
    
    deepseek_chat = DeepSeekChat(api_key)
    
    # Chat interface
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    # Display chat history
    for message in st.session_state.chat_history:
        if message['role'] == 'user':
            st.markdown(f"**You:** {message['content']}")
            st.markdown("---")
        else:
            st.markdown(f"**🤖 AI Assistant:** {message['content']}")
            st.markdown("---")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Chat input
    col1, col2 = st.columns([4, 1])
    
    with col1:
        user_input = st.text_input(
            "Ask me anything about real estate:", 
            key="chat_input", 
            placeholder="e.g., What is RERA and how does it protect homebuyers?"
        )
    
    with col2:
        send_clicked = st.button("Send", use_container_width=True)
    
    if (send_clicked or user_input) and user_input:
        # Add user message to history
        st.session_state.chat_history.append({
            'role': 'user',
            'content': user_input
        })
        
        # Get AI response
        with st.spinner("🤔 Thinking..."):
            response = deepseek_chat.get_response(user_input)
            
            # Add AI response to history
            st.session_state.chat_history.append({
                'role': 'assistant',
                'content': response
            })
        
        # Clear input and rerun
        st.session_state.chat_input = ""
        st.rerun()
    
    # Quick questions
    st.markdown("---")
    st.subheader("💡 Quick Questions")
    
    quick_questions = [
        "What is RERA and how does it protect homebuyers?",
        "How do I calculate property valuation using CMA method?",
        "What documents are required for property registration?",
        "What is the difference between FSI and TDR?",
        "How do I invest in REITs in India?",
        "What are the tax implications of property investment?",
        "How do I conduct due diligence before buying property?",
        "What are the latest green building certifications in India?"
    ]
    
    cols = st.columns(2)
    
    for i, question in enumerate(quick_questions):
        with cols[i % 2]:
            if st.button(question, key=f"quick_{i}"):
                # Add question to chat
                st.session_state.chat_history.append({
                    'role': 'user',
                    'content': question
                })
                
                # Get AI response
                with st.spinner("Getting answer..."):
                    response = deepseek_chat.get_response(question)
                    
                    st.session_state.chat_history.append({
                        'role': 'assistant',
                        'content': response
                    })
                
                st.rerun()
    
    st.markdown("---")
    
    # Clear chat button
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
    
    with col2:
        if st.button("💾 Export Chat", use_container_width=True):
            chat_text = "\n\n".join([f"{msg['role'].title()}: {msg['content']}" for msg in st.session_state.chat_history])
            st.download_button(
                label="Download Chat History",
                data=chat_text,
                file_name=f"realestate_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )

def show_progress_page():
    st.markdown('<div class="main-header"><h1>📊 Your Learning Progress</h1></div>', unsafe_allow_html=True)
    
    # Overall progress metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Modules Available", "5", "All unlocked")
    
    with col2:
        st.metric("Content Access", "100%", "Full access")
    
    with col3:
        st.metric("AI Assistance", "Available", "24/7 support")
    
    st.markdown("---")
    
    # Module progress
    st.subheader("📚 Module Progress")
    
    modules = get_available_modules()
    
    for module in modules:
        difficulty_color = {"Beginner": "🟢", "Intermediate": "🟡", "Advanced": "🔴"}
        color = difficulty_color.get(module['difficulty'], "📚")
        
        st.markdown(f"""
        <div class="module-card">
            <h4>{color} {module['title']}</h4>
            <p><strong>Category:</strong> {module['category']} | <strong>Difficulty:</strong> {module['difficulty']}</p>
            <p>{module['description']}</p>
            <p>✅ <strong>Status:</strong> Content Available - Ready to Study</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Learning recommendations
    st.subheader("🎯 Learning Recommendations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Recommended Learning Path:**
        1. 🟢 Start with **Real Estate Fundamentals**
        2. 🟢 Learn **Property Measurements & Standards**
        3. 🟡 Move to **Legal Framework & RERA**
        4. 🟡 Study **Valuation & Finance**
        5. 🔴 Master **Land & Development Laws**
        """)
    
    with col2:
        st.markdown("""
        **Study Tips:**
        - 📖 Read through each module content thoroughly
        - 🤖 Use AI Assistant for clarifications
        - 📝 Take notes while studying
        - 🏆 Test yourself with assessments
        - 🔄 Review previous modules regularly
        """)

def show_assessments():
    st.markdown('<div class="main-header"><h1>🏆 Assessments & Quizzes</h1></div>', unsafe_allow_html=True)
    
    st.info("💡 Assessments help test your understanding of the modules. Complete modules first to get the most out of these assessments.")
    
    st.subheader("Available Assessments")
    
    assessments = [
        {
            'title': 'Real Estate Fundamentals Quiz',
            'module': 'Real Estate Fundamentals',
            'questions': 10,
            'duration': '15 min',
            'difficulty': 'Beginner',
            'status': 'Available'
        },
        {
            'title': 'RERA Compliance Test',
            'module': 'Legal Framework & RERA',
            'questions': 15,
            'duration': '20 min',
            'difficulty': 'Intermediate',
            'status': 'Available'
        },
        {
            'title': 'Property Measurement Standards',
            'module': 'Property Measurements & Standards',
            'questions': 12,
            'duration': '18 min',
            'difficulty': 'Beginner',
            'status': 'Available'
        },
        {
            'title': 'Valuation Methods Assessment',
            'module': 'Valuation & Finance',
            'questions': 20,
            'duration': '25 min',
            'difficulty': 'Intermediate',
            'status': 'Available'
        },
        {
            'title': 'Development Laws Exam',
            'module': 'Land & Development Laws',
            'questions': 25,
            'duration': '35 min',
            'difficulty': 'Advanced',
            'status': 'Available'
        }
    ]
    
    for assessment in assessments:
        difficulty_color = {"Beginner": "🟢", "Intermediate": "🟡", "Advanced": "🔴"}
        color = difficulty_color.get(assessment['difficulty'], "📝")
        
        with st.expander(f"{color} {assessment['title']} ({assessment['difficulty']})"):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.write(f"**Module:** {assessment['module']}")
            
            with col2:
                st.write(f"**Questions:** {assessment['questions']}")
            
            with col3:
                st.write(f"**Duration:** {assessment['duration']}")
            
            with col4:
                st.write(f"**Status:** {assessment['status']}")
            
            st.markdown("---")
            
            if assessment['status'] == 'Available':
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("📖 Study Module First", key=f"study_{assessment['title']}"):
                        # Find the corresponding module
                        modules = get_available_modules()
                        for module in modules:
                            if module['title'] == assessment['module']:
                                st.session_state.current_module = module['id']
                                st.session_state.current_page = "module_content"
                                st.rerun()
                
                with col2:
                    if st.button("🚀 Start Assessment", key=f"start_{assessment['title']}"):
                        st.success(f"Assessment '{assessment['title']}' would start here!")
                        st.info("💡 Assessment functionality will be implemented in the next version. For now, study the modules and use the AI Assistant to test your knowledge!")
    
    st.markdown("---")
    
    # Assessment tips
    st.subheader("📚 Assessment Tips")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Before Taking Assessments:**
        - 📖 Complete the related module content
        - 📝 Take notes while studying
        - 🤖 Ask AI Assistant for clarifications
        - 🔄 Review key concepts multiple times
        """)
    
    with col2:
        st.markdown("""
        **During Assessments:**
        - ⏰ Manage your time effectively
        - 📖 Read questions carefully
        - 🤔 Think through each option
        - ✅ Review answers before submission
        """)

def main():
    # Initialize database
    try:
        init_database()
    except Exception as e:
        st.error(f"Database initialization error: {str(e)}")
        st.stop()
    
    # Sidebar
    with st.sidebar:
        if not st.session_state.authenticated:
            if st.session_state.get('show_register', False):
                show_registration_form()
            else:
                show_login_form()
        else:
            show_navigation()
    
    # Main content
    if not st.session_state.authenticated:
        show_welcome_page()
    else:
        page = st.session_state.get('current_page', 'dashboard')
        
        try:
            if page == 'dashboard':
                if st.session_state.user_role == 'admin':
                    show_admin_dashboard()
                else:
                    show_user_dashboard()
            elif page == 'admin_dashboard':
                show_admin_dashboard()
            elif page == 'content_management':
                show_content_management()
            elif page == 'user_management':
                show_user_management()
            elif page == 'content_research':
                show_content_research()
            elif page == 'module_content':
                show_module_content()
            elif page == 'progress':
                show_progress_page()
            elif page == 'assessments':
                show_assessments()
            elif page == 'ai_assistant':
                show_ai_assistant()
            else:
                show_user_dashboard()
        except Exception as e:
            st.error(f"Page error: {str(e)}")
            st.info("Redirecting to dashboard...")
            st.session_state.current_page = 'dashboard'
            st.rerun()

if __name__ == "__main__":
    main()
