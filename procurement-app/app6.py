import streamlit as st
import json
import os
import requests
from datetime import datetime
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import socket
from collections import defaultdict, Counter
from ollama import Client
import matplotlib.pyplot as plt

# -----------------------------
# Configuration
# -----------------------------
DATA_DIR = "procurement_data"
os.makedirs(DATA_DIR, exist_ok=True)

# -----------------------------
# Load Data
# -----------------------------
# Source-To-Pay Process Theme Data
with open("Recommendations.json") as f:
    RECOMMENDATIONS = json.load(f)

FOCUSED_AREAS = {
    "Strategic Sourcing": [
        {
            "number": 1,
            "question": "To what extent are preferred vendors documented and used in sourcing decisions?",
            "responses": [
                {"score": 5, "text": "Preferred vendors are maintained centrally, regularly updated, and integrated into sourcing strategy"},
                {"score": 4, "text": "Preferred vendors are defined for key categories and referenced in sourcing events"},
                {"score": 3, "text": "Some category-level vendor preferences exist, but usage is inconsistent"},
                {"score": 2, "text": "Limited category planning, with ad-hoc supplier preference"},
                {"score": 1, "text": "No defined preferred vendors used"}
            ]
        },
        {
            "number": 2,
            "question": "How well-defined and consistently followed is your strategic sourcing process?",
            "responses": [
                {"score": 5, "text": "End-to-end strategic sourcing process is documented, digitized, and consistently followed"},
                {"score": 4, "text": "Most sourcing events follow a structured and repeatable process"},
                {"score": 3, "text": "Sourcing process is documented but applied selectively"},
                {"score": 2, "text": "Ad-hoc sourcing with minimal process adherence"},
                {"score": 1, "text": "No defined sourcing process or documentation"}
            ]
        },
        {
            "number": 3,
            "question": "How comprehensive is your approach in evaluating suppliers during sourcing?",
            "responses": [
                {"score": 5, "text": "Supplier selection includes total cost of ownership, risk, sustainability, and performance history"},
                {"score": 4, "text": "Evaluations include cost and quality, with limited use of additional criteria"},
                {"score": 3, "text": "Evaluation focuses mainly on cost and delivery"},
                {"score": 2, "text": "Evaluation is informal and varies by event"},
                {"score": 1, "text": "No structured supplier evaluation"}
            ]
        },
        {
            "number": 4,
            "question": "What tools or approaches are used to identify and engage new suppliers?",
            "responses": [
                {"score": 5, "text": "Dedicated tools or platforms (e.g., supplier discovery portals, AI scouting tools) used globally"},
                {"score": 4, "text": "Category managers actively scout using databases or networks"},
                {"score": 3, "text": "New supplier identification is done manually on a case-by-case basis"},
                {"score": 2, "text": "Limited to existing supplier base with rare exploration"},
                {"score": 1, "text": "No effort or process to identify new suppliers"}
            ]
        },
        {
            "number": 5,
            "question": "How structured and efficient is your RFx (RFI/RFP/RFQ) process?",
            "responses": [
                {"score": 5, "text": "Fully automated and standardized RFx process with clear scoring and audit trail"},
                {"score": 4, "text": "RFx templates and evaluation criteria are used consistently"},
                {"score": 3, "text": "RFx processes are in place but vary by category or manager"},
                {"score": 2, "text": "RFx events are run manually with limited structure"},
                {"score": 1, "text": "No formal RFx process in place"}
            ]
        },
        {
            "number": 6,
            "question": "How structured is your approach to preparing for and conducting negotiations with suppliers?",
            "responses": [
                {"score": 5, "text": "Highly Structured & Institutionalized"},
                {"score": 4, "text": "Structured"},
                {"score": 3, "text": "Moderately Structured"},
                {"score": 2, "text": "Somewhat Unstructured"},
                {"score": 1, "text": "Very Unstructured"}
            ]
        }
    ],
    "Procurement Process": [
        {
            "number": 1,
            "question": "How standardized and compliant is your requisition process across the organization?",
            "responses": [
                {"score": 5, "text": "Fully standardized and automated requisition process across all units; high compliance monitored and enforced via tools"},
                {"score": 4, "text": "Well-documented, consistently followed process with automated compliance validation in most areas"},
                {"score": 3, "text": "Standardized requisition process exists in most departments; basic compliance checks are in place"},
                {"score": 2, "text": "Some standard templates exist, but processes are loosely followed; compliance is ad hoc and not enforced"},
                {"score": 1, "text": "Requisition processes are manual, inconsistent, and vary across departments; no compliance checks in place"}
            ]
        },
        {
            "number": 2,
            "question": "How mature is your PO management in terms of accuracy, control, and compliance?",
            "responses": [
                {"score": 5, "text": "Advanced PO automation with full audit trails, real-time validation, and strong control mechanisms"},
                {"score": 4, "text": "PO system is integrated with procurement tools, ensuring high accuracy and compliance tracking"},
                {"score": 3, "text": "PO process is largely digitized with some accuracy and approval controls in place"},
                {"score": 2, "text": "Basic PO system in place, but accuracy is inconsistent and control measures are minimal"},
                {"score": 1, "text": "PO creation is mostly manual with frequent errors and lack of oversight or control"}
            ]
        },
        {
            "number": 3,
            "question": "How effectively do you leverage technology in your procurement process?",
            "responses": [
                {"score": 5, "text": "Fully digitized and automated procurement using advanced tools (e-sourcing, AI, analytics)"},
                {"score": 4, "text": "Good use of integrated tools (e.g., ERP, e-procurement platforms); moderate automation"},
                {"score": 3, "text": "Use of basic procurement systems for POs or requisitions; partial process automation"},
                {"score": 2, "text": "Limited use of technology (e.g., Excel, email); no integrated procurement platform"},
                {"score": 1, "text": "Procurement is primarily manual with minimal use of digital tools or technology"}
            ]
        },
        {
            "number": 4,
            "question": "How well-defined are your procurement governance and risk mitigation frameworks?",
            "responses": [
                {"score": 5, "text": "Robust governance structure with real-time risk monitoring and mitigation strategies embedded in processes"},
                {"score": 4, "text": "Governance frameworks and risk registers are well-defined and regularly reviewed"},
                {"score": 3, "text": "Some policies exist; basic risk assessments are conducted periodically"},
                {"score": 2, "text": "Ad hoc risk handling; limited policies or governance documentation"},
                {"score": 1, "text": "No formal governance or risk mitigation practices in procurement"}
            ]
        },
        {
            "number": 5,
            "question": "How do you track and measure procurement performance?",
            "responses": [
                {"score": 5, "text": "Advanced analytics and dashboards provide real-time performance visibility; continuous improvement is data-driven"},
                {"score": 4, "text": "Comprehensive KPIs regularly tracked and reported with insights for decision-making"},
                {"score": 3, "text": "Basic KPIs (e.g., savings, supplier count) tracked; reports generated periodically"},
                {"score": 2, "text": "Some metrics (e.g., spend) tracked manually; limited insight into performance"},
                {"score": 1, "text": "No performance metrics tracked; lack of visibility into procurement outcome"}
            ]
        },
        {
            "number": 6,
            "question": "How embedded are sustainability and ethical practices in your procurement process?",
            "responses": [
                {"score": 5, "text": "Sustainability and ethical sourcing are core procurement principles with enforced compliance and transparent tracking"},
                {"score": 4, "text": "Formal sustainability policies in place; supplier assessments are conducted"},
                {"score": 3, "text": "Basic sustainability/ethics criteria applied in some sourcing decisions"},
                {"score": 2, "text": "Some awareness, but no formal practices or criteria in place"},
                {"score": 1, "text": "No consideration of sustainability or ethics in procurement decisions"}
            ]
        }
    ],
    "Category Management": [
        {
            "number": 1,
            "question": "How frequently do you perform spend analysis?",
            "responses": [
                {"score": 5, "text": "Real-time or monthly"},
                {"score": 4, "text": "Quarterly"},
                {"score": 3, "text": "Annually"},
                {"score": 2, "text": "Ad-hoc or only when requested"},
                {"score": 1, "text": "Rarely or not at all"}
            ]
        },
        {
            "number": 2,
            "question": "How systematic is your spend analysis process?",
            "responses": [
                {"score": 5, "text": "Fully automated with dashboards and coverage across all categories"},
                {"score": 4, "text": "Partially automated with good visibility and structured templates"},
                {"score": 3, "text": "Mostly manual with basic categorization"},
                {"score": 2, "text": "Inconsistent methods; depends on team/initiative"},
                {"score": 1, "text": "No standardized process; lacks repeatability"}
            ]
        },
        {
            "number": 3,
            "question": "To what extent are category strategies documented and action-oriented?",
            "responses": [
                {"score": 5, "text": "Documented for all categories with KPIs, reviews, and alignment to business strategy"},
                {"score": 4, "text": "Documented for key categories with basic objectives"},
                {"score": 3, "text": "Some informal strategies without measurable goals"},
                {"score": 2, "text": "Very limited strategy documents; mostly reactive"},
                {"score": 1, "text": "No documented category strategies"}
            ]
        },
        {
            "number": 4,
            "question": "How are sourcing savings tracked and validated?",
            "responses": [
                {"score": 5, "text": "Centralized system with real-time tracking, finance-aligned validation, and reporting"},
                {"score": 4, "text": "System-based tracking, with periodic finance review"},
                {"score": 3, "text": "Spreadsheet-based tracking with irregular validation"},
                {"score": 2, "text": "Only tracked during sourcing events"},
                {"score": 1, "text": "No standard methodology or tracking"}
            ]
        },
        {
            "number": 5,
            "question": "How do you monitor and manage supplier performance?",
            "responses": [
                {"score": 5, "text": "Formal process with KPIs, scorecards, reviews, and improvement plans"},
                {"score": 4, "text": "KPIs tracked for key suppliers, but no formal reviews"},
                {"score": 3, "text": "Informal evaluations without clear KPIs"},
                {"score": 2, "text": "Evaluations based on issues/escalations only"},
                {"score": 1, "text": "No structured supplier performance evaluation"}
            ]
        },
        {
            "number": 6,
            "question": "How do you manage supplier and market risks?",
            "responses": [
                {"score": 5, "text": "Formal framework with real-time risk dashboards and proactive mitigation"},
                {"score": 4, "text": "Risk register and monitoring in place, with periodic assessments"},
                {"score": 3, "text": "Basic risk identification, reactive handling only"},
                {"score": 2, "text": "Limited visibility into supplier risks"},
                {"score": 1, "text": "No structured risk management"}
            ]
        }
    ],
    "Payment Process": [
        {
            "number": 1,
            "question": "How efficient and automated is your invoice receipt and processing workflow?",
            "responses": [
                {"score": 5, "text": "Fully automated invoice capture, 3-way match, touchless processing"},
                {"score": 4, "text": "Mostly system-based with minimal manual effort and 2/3-way match"},
                {"score": 3, "text": "Mix of manual and digital steps; partial automation"},
                {"score": 2, "text": "Mostly manual; email and spreadsheet-based tracking"},
                {"score": 1, "text": "Entirely manual, paper-based invoice handling"}
            ]
        },
        {
            "number": 2,
            "question": "What level of visibility do suppliers have into their invoice and payment status?",
            "responses": [
                {"score": 5, "text": "Supplier portal with real-time invoice/payment tracking and support tools"},
                {"score": 4, "text": "Automated email updates and self-service options"},
                {"score": 3, "text": "Basic visibility through AP responses or manual reports"},
                {"score": 2, "text": "Suppliers must frequently follow up for updates"},
                {"score": 1, "text": "No structured visibility or support mechanisms for suppliers"}
            ]
        },
        {
            "number": 3,
            "question": "How are payments reviewed, approved, and controlled?",
            "responses": [
                {"score": 5, "text": "Fully digital, role-based approval workflows with audit trails"},
                {"score": 4, "text": "Mostly digital approvals with some manual oversight"},
                {"score": 3, "text": "Manual approvals supported by standard templates"},
                {"score": 2, "text": "Ad-hoc approval methods; inconsistent documentation"},
                {"score": 1, "text": "No formal approval process; payments made without structured review"}
            ]
        },
        {
            "number": 4,
            "question": "How well does your organization ensure payments are made on time and accurately?",
            "responses": [
                {"score": 5, "text": "Payments are made on time >95% of the time, with automated scheduling"},
                {"score": 4, "text": "Mostly on-time with minimal delays and errors"},
                {"score": 3, "text": "Occasional delays or duplicate/incorrect payments"},
                {"score": 2, "text": "Frequent issues in timing or mismatched amounts"},
                {"score": 1, "text": "Regular payment delays, errors, and supplier escalations"}
            ]
        },
        {
            "number": 5,
            "question": "How optimized and digitized are your payment methods?",
            "responses": [
                {"score": 5, "text": "Majority of payments via secure digital methods (ACH, virtual cards, etc.)"},
                {"score": 4, "text": "High usage of ACH/digital methods; checks rarely used"},
                {"score": 3, "text": "Balanced mix of digital and manual payment methods"},
                {"score": 2, "text": "Predominantly check/wire based, with limited digital adoption"},
                {"score": 1, "text": "Manual, paper-based payment handling only"}
            ]
        },
        {
            "number": 6,
            "question": "What controls are in place to ensure compliance and prevent fraud in payments?",
            "responses": [
                {"score": 5, "text": "Proactive risk controls, segregation of duties, automated fraud detection"},
                {"score": 4, "text": "Strong approval controls and periodic audits"},
                {"score": 3, "text": "Basic compliance checks during processing"},
                {"score": 2, "text": "Minimal compliance processes; relies on trust"},
                {"score": 1, "text": "No formal compliance or anti-fraud mechanisms"}
            ]
        }
    ]
}

# Procurement Performance Theme Data
with open("slas_kpis_questions_final.json") as f:
    performance_questions = json.load(f)["questions"]

with open("deepseek_json_20250720_551af9.json") as f:
    deepseek_data = json.load(f)["questions"]

# Industry Benchmarks
INDUSTRY_STANDARDS = {
    "Source-To-Pay Process": {
        "Strategic Sourcing": 3.7,
        "Procurement Process": 3.5,
        "Category Management": 3.6,
        "Payment Process": 3.8
    },
    "Procurement Performance": {
        "Performance Review": 3,
        "Savings Tracking": 4,
        "Procurement KPIs": 3,
        "Compliance KPIs": 4,
        "Reporting": 5
    }
}

# Theme benchmarks (for combined view)
THEME_BENCHMARKS = {
    "Source-To-Pay Process": 3.6,
    "Procurement Performance": 3.8,
    "Strategy and Vision": 3.5,
    "People and Organization": 3.4,
    "Technology and Enablers": 3.7
}

# Source for Industry Standards
INDUSTRY_STANDARD_SOURCES = [
    "Deloitte Global Chief Procurement Officer Survey 2024",
    "Kearney Procurement Study 2023",
    "Gartner Magic Quadrant for Strategic Sourcing Suites 2023",
    "IBM Institute for Business Value: The CPO Study 2023"
]

# Theme definitions
THEMES = {
    "Strategy and Vision": {
        "status": "under_development",
        "description": "Strategic planning, governance, and procurement alignment with business objectives"
    },
    "Technology and Enablers": {
        "status": "under_development",
        "description": "Digital tools, automation, and technology infrastructure supporting procurement"
    },
    "People and Organization": {
        "status": "under_development",
        "description": "Organizational structure, skills development, and talent management"
    },
    "Source-To-Pay Process": {
        "status": "active",
        "description": "End-to-end procurement process from sourcing to payment",
        "focused_areas": FOCUSED_AREAS
    },
    "Procurement Performance": {
        "status": "active",
        "description": "Performance measurement, analytics, and continuous improvement",
        "questions": performance_questions
    }
}

# -----------------------------
# Ollama Connection
# -----------------------------
ollama_available = False
# -----------------------------
# Utility Functions
# -----------------------------

# Add this function in the Utility Functions section
def calculate_org_maturity(org_data, theme):
    """Calculate maturity for an organization for a specific theme"""
    if not org_data or "users" not in org_data:
        return None
    
    # Collect all responses for this theme
    all_responses = []
    for user in org_data["users"]:
        if user.get("theme") == theme:
            all_responses.extend(user["responses"])
    
    if not all_responses:
        return None
    
    # For Source-To-Pay Process
    if theme == "Source-To-Pay Process":
        # Group by focused area
        area_scores = defaultdict(list)
        for resp in all_responses:
            area_scores[resp["focused_area"]].append(resp["score"])
        
        # Calculate average per area
        by_area = {}
        for area, scores in area_scores.items():
            by_area[area] = round(sum(scores) / len(scores), 1)
        
        # Overall is average of all responses
        overall = round(sum(resp["score"] for resp in all_responses) / len(all_responses), 1)
        
        return {
            "overall": overall,
            "by_area": by_area
        }
    
    # For Procurement Performance
    elif theme == "Procurement Performance":
        # Group by focus area
        area_scores = defaultdict(list)
        for resp in all_responses:
            area_scores[resp["focus_area"]].append(resp["score"])
        
        by_area = {}
        for area, scores in area_scores.items():
            by_area[area] = round(sum(scores) / len(scores), 1)
        
        overall = round(sum(resp["score"] for resp in all_responses) / len(all_responses), 1)
        
        return {
            "overall": overall,
            "by_area": by_area
        }
    
    return None

def save_response(user_data):
    """Save user response to organization-specific JSON file"""
    org_name = user_data["organization"].replace(" ", "_").replace("/", "-")
    org_file = os.path.join(DATA_DIR, f"{org_name}.json")

    if os.path.exists(org_file):
        with open(org_file, "r") as f:
            data = json.load(f)
    else:
        data = {"organization": user_data["organization"], "users": []}

    # Create a complete user record
    user_record = {
        "name": user_data["name"],
        "email": user_data["email"],
        "designation": user_data.get("designation", ""),
        "theme": user_data.get("theme", "Combined Assessment"),
        "responses": user_data["responses"],
        "timestamp": user_data["timestamp"]
    }
    
    # Add user_info if available
    if "user_info" in user_data:
        user_record["user_info"] = user_data["user_info"]
    
    # Remove existing response from same user if exists
    data["users"] = [user for user in data["users"] if user["email"] != user_data["email"]]
    data["users"].append(user_record)  # Append the complete user record

    with open(org_file, "w") as f:
        json.dump(data, f, indent=2)

def get_org_data(org_name):
    """Retrieve all user responses for an organization"""
    org_name_clean = org_name.replace(" ", "_").replace("/", "-")
    org_file = os.path.join(DATA_DIR, f"{org_name_clean}.json")
    
    if os.path.exists(org_file):
        with open(org_file, "r") as f:
            return json.load(f)
    return None

def calculate_theme_score(responses, theme):
    """Calculate average score for a specific theme"""
    theme_responses = [r for r in responses if r["theme"] == theme]
    if not theme_responses:
        return 0.0
    total_score = sum(response["score"] for response in theme_responses)
    return round(total_score / len(theme_responses), 1)

def get_industry_benchmarks(theme):
    """Get industry benchmarks for a specific theme"""
    if theme in THEME_BENCHMARKS:
        return THEME_BENCHMARKS[theme]
    return 0.0

def get_recommendations(theme, score):
    """Get theme-level recommendations"""
    if theme == "Source-To-Pay Process":
        return "Implement end-to-end process automation and supplier collaboration tools"
    elif theme == "Procurement Performance":
        return "Establish comprehensive performance metrics and real-time dashboards"
    else:
        return "Focus on strategic alignment and digital transformation initiatives"

def get_maturity_label(level):
    """Get text label for maturity level for the gauge chart."""
    if 0 <= level < 1: return "Latent"
    elif 1 <= level < 2: return "Discovery"
    elif 2 <= level < 3: return "Reactive"
    elif 3 <= level < 4: return "Proactive"
    elif 4 <= level <= 5: return "Strategic Value"
    else: return "Unknown"

def get_participants_count(org_data):
    """Get number of participants in an organization"""
    if not org_data or not org_data.get("users"):
        return 0
    return len(org_data["users"])

def show_theme_tiles():
    """Display theme selection tiles"""
    st.header(":notebook: Select Procurement Themes to Assess")
    st.caption("Choose one or more themes to evaluate your organization's procurement maturity")
    
    cols = st.columns(5)
    theme_keys = list(THEMES.keys())
    
    for i, theme in enumerate(theme_keys):
        with cols[i]:
            # Display theme icon (using emoji as placeholder)
            icon = "📊" if "Performance" in theme else "👥" if "People" in theme else "🔄" if "Process" in theme else "💡" if "Vision" in theme else "💻"
            st.markdown(f"<div style='text-align: center; margin-bottom: 10px; font-size: 48px;'>{icon}</div>", unsafe_allow_html=True)
            
            # Theme name and description
            st.subheader(theme)
            st.caption(THEMES[theme]["description"])
            
            # Selection checkbox
            if THEMES[theme]["status"] == "active":
                selected = st.checkbox(f"Select {theme}", key=f"select_{theme}")
                st.session_state.selected_themes[theme] = selected
            else:
                st.warning("Coming Soon")
                st.session_state.selected_themes[theme] = False

# --- AI Functions ---
def generate_ai_recommendations(prompt, context=""):
    """Generate AI recommendations using Ollama"""
    try:
        # Create the full prompt with context
        full_prompt = f"{context}\n\n{prompt}"
        
        # Generate response using the correct model name
        response = client.generate(
            model="llama3.2:latest",
            prompt=full_prompt,
            options={"temperature": 0.6}
        )
        return response['response'].strip()
    except Exception as e:
        st.error(f"AI recommendation generation failed: {str(e)}")
        return f"AI recommendations are currently unavailable. Please check your Ollama installation and server status."

def generate_holistic_recommendations(overall_score, maturity_gap):
    """Generate holistic organization-level recommendations"""
    prompt = f"""
    As a procurement consultant, provide holistic recommendations for an organization 
    with overall procurement maturity at {overall_score}/5.0. 
    
    The organization is {abs(maturity_gap):.1f} points below industry standard.
    Focus on strategic priorities that would have the most significant impact on 
    improving overall procurement maturity. Include both short-term quick wins and 
    long-term transformation initiatives.
    """
    return generate_ai_recommendations(prompt)

def generate_role_specific_actions(designations, maturity_gap):
    """Generate role-specific action items"""
    prompt = f"""
    Generate specific action items for different roles in procurement to improve 
    procurement maturity. Current maturity gap: {maturity_gap:.1f} below industry standard.
    
    Roles: {', '.join(designations)}
    
    For each role, provide 2-3 concrete, executable action items that align with 
    their responsibilities and will contribute to improving overall procurement maturity.
    """
    return generate_ai_recommendations(prompt)

def generate_theme_recommendation(theme, score, benchmark):
    """Generate theme-level recommendations"""
    prompt = f"""
    As a procurement consultant, provide recommendations for improving the {theme} capability.
    The organization's current maturity level is {score}/5.0 (industry benchmark: {benchmark}/5.0).
    Focus on strategic priorities that would have the most significant impact.
    Provide 2-3 actionable recommendations.
    """
    return generate_ai_recommendations(prompt)

# --- Plotly Chart Functions ---
def create_gauge_chart(value, title, max_value=5.0):
    """Creates a Plotly Gauge Chart for overall maturity."""
    # Define ranges and colors
    ranges = {
        "Latent": [0, 1],
        "Discovery": [1, 2],
        "Reactive": [2, 3],
        "Proactive": [3, 4],
        "Strategic Value": [4, 5]
    }
    colors = {
        "Latent": "#FF4B4B",       # Red
        "Discovery": "#FFA500",    # Orange
        "Reactive": "#FFD700",     # Gold
        "Proactive": "#90EE90",    # Light Green
        "Strategic Value": "#20B2AA" # Light Sea Green
    }
    
    # Determine current stage and color
    current_stage = get_maturity_label(value)
    current_color = colors.get(current_stage, "#CCCCCC") # Default to grey if not found

    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = value,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': f"<span style='font-size:1.2em'>{title}</span><br><span style='font-size:0.9em;color:gray'>{current_stage}</span>"},
        delta = {'reference': max_value / 2, 'decreasing': {'color': 'red'}, 'increasing': {'color': 'green'}},
        gauge = {
            'axis': {'range': [None, max_value], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': current_color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': ranges["Latent"], 'color': colors["Latent"], 'name': 'Latent'},
                {'range': ranges["Discovery"], 'color': colors["Discovery"], 'name': 'Discovery'},
                {'range': ranges["Reactive"], 'color': colors["Reactive"], 'name': 'Reactive'},
                {'range': ranges["Proactive"], 'color': colors["Proactive"], 'name': 'Proactive'},
                {'range': ranges["Strategic Value"], 'color': colors["Strategic Value"], 'name': 'Strategic Value'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': value
            }}
    ))

    fig.update_layout(height=250, margin=dict(l=10, r=10, t=50, b=10))
    return fig

def create_radar_chart(theme_scores, theme_benchmarks):
    """Creates a Plotly Radar Chart for theme-wise comparison."""
    themes = list(theme_scores.keys())
    
    # Add the first point again to close the loop in the radar chart
    r_org = [theme_scores[theme] for theme in themes] + [theme_scores[themes[0]]]
    r_industry = [theme_benchmarks.get(theme, 0) for theme in themes] + [theme_benchmarks.get(themes[0], 0)]
    theta_labels = themes + [themes[0]] # Labels for theta axis

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
          r=r_org,
          theta=theta_labels,
          fill='toself',
          name='Your Organization',
          line_color='blue',
          opacity=0.7,
          hoverinfo='text+name+r',
          mode='lines+markers'
    ))
    fig.add_trace(go.Scatterpolar(
          r=r_industry,
          theta=theta_labels,
          fill='toself',
          name='Industry Standard',
          line_color='orange',
          opacity=0.4,
          hoverinfo='text+name+r',
          mode='lines+markers'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 5],
                tickvals=[0, 1, 2, 3, 4, 5],
                ticktext=['0', '1', '2', '3', '4', '5']  # Simplified labels
            )),
        showlegend=True,
        title="Maturity Comparison by Theme",
        height=550,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        )
    )
    
    # Add maturity level explanation below the chart
    st.caption("""
    **Maturity Levels:**  
    • 1-2: Latent (Initial/Ad-hoc)  
    • 2-3: Discovery (Developing)  
    • 3-4: Reactive (Defined)  
    • 4-5: Proactive (Managed/Optimized)
    """)
    
    return fig

# Main app
def main():
    st.set_page_config(page_title="Procurement Maturity Assessment", page_icon="📊", layout="wide")
    st.title(":briefcase: Procurement Maturity Assessment Tool")
    st.caption("Evaluate and elevate your organization's procurement capabilities")
    
    # Initialize session state
    if "stage" not in st.session_state:
        st.session_state.stage = "user_info"
        st.session_state.selected_themes = {}
        st.session_state.user_responses = {}
        st.session_state.user_data = None
        st.session_state.org_data = None
        st.session_state.org_maturity = None
        st.session_state.selected_focused_areas = []
        st.session_state.performance_responses = {}
        st.session_state.performance_current_question = 0
        st.session_state.combined_mode = False
        st.session_state.theme_scores = {}

    # User information stage
    if st.session_state.stage == "user_info":
        with st.form("user_info_form"):
            st.header(":bust_in_silhouette: User Information")
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Full Name", placeholder="John Smith")
                email = st.text_input("Work Email", placeholder="john@company.com")
            with col2:
                designation = st.text_input("Designation/Role", placeholder="Procurement Manager")
                organization = st.text_input("Organization Name", placeholder="Acme Corporation")
            
            if st.form_submit_button("Continue to Theme Selection"):
                if name and email and organization:
                    st.session_state.user_info = {
                        "name": name,
                        "email": email,
                        "designation": designation,
                        "organization": organization
                    }
                    st.session_state.stage = "theme_selection"
                    st.rerun()
                else:
                    st.warning("Please fill all required fields (Name, Email, Organization)")

    # Theme selection stage
    elif st.session_state.stage == "theme_selection":
        st.header(":clipboard: Assessment Themes")
        show_theme_tiles()
        
        if st.button("Start Assessment", type="primary"):
            selected_count = sum(st.session_state.selected_themes.values())
            if selected_count == 0:
                st.warning("Please select at least one theme to assess")
            else:
                # Check if we're in combined mode
                st.session_state.combined_mode = selected_count > 1
                
                # Get selected themes
                selected_themes = [theme for theme, selected in st.session_state.selected_themes.items() if selected]
                
                # For Source-To-Pay Process, we need focused area selection
                if "Source-To-Pay Process" in selected_themes and not st.session_state.combined_mode:
                    st.session_state.stage = "focused_area_selection"
                    st.rerun()
                else:
                    # Start assessment
                    st.session_state.stage = "assessment"
                    st.rerun()

    # Focused area selection stage (only for Source-To-Pay Process in single mode)
    elif st.session_state.stage == "focused_area_selection":
        theme = "Source-To-Pay Process"
        theme_data = THEMES[theme]
        
        st.header(f":mag: {theme} - Select Focused Areas")
        st.caption("Select the specific areas you want to assess under Source-To-Pay Process")
        
        # Get focused areas for the theme
        focused_areas = list(theme_data["focused_areas"].keys())
        
        # Reset selected focused areas
        st.session_state.selected_focused_areas = []
        
        with st.form("focused_area_form"):
            for area in focused_areas:
                selected = st.checkbox(area, key=f"select_{area}")
                if selected:
                    st.session_state.selected_focused_areas.append(area)
            
            if st.form_submit_button("Continue to Assessment"):
                if len(st.session_state.selected_focused_areas) > 0:
                    st.session_state.stage = "assessment"
                    st.rerun()
                else:
                    st.warning("Please select at least one focused area to assess")

    # Assessment stage
    elif st.session_state.stage == "assessment":
        selected_themes = [theme for theme, selected in st.session_state.selected_themes.items() if selected]
        
        # Combined mode assessment
        if st.session_state.combined_mode:
            st.header(":clipboard: Combined Assessment")
            st.info("You are assessing multiple themes. Please answer questions for all selected themes.")
            
            # Get all questions for all themes
            all_questions = []
            
            # Add Source-To-Pay Process questions
            if "Source-To-Pay Process" in selected_themes:
                theme_data = THEMES["Source-To-Pay Process"]
                for focused_area in theme_data["focused_areas"]:
                    for question in theme_data["focused_areas"][focused_area]:
                        all_questions.append({
                            "theme": "Source-To-Pay Process",
                            "focused_area": focused_area,
                            "question": question,
                            "type": "stp"
                        })
            
            # Add Procurement Performance questions
            if "Procurement Performance" in selected_themes:
                theme_data = THEMES["Procurement Performance"]
                for qid, q in theme_data["questions"].items():
                    all_questions.append({
                        "theme": "Procurement Performance",
                        "focused_area": q["focus_area"],
                        "question": q,
                        "type": "perf",
                        "qid": qid
                    })
            
            # Initialize question index
            if "current_question_index" not in st.session_state:
                st.session_state.current_question_index = 0
                st.session_state.combined_responses = []
            
            # Show current question
            if st.session_state.current_question_index < len(all_questions):
                q_data = all_questions[st.session_state.current_question_index]
                q = q_data["question"]
                
                st.subheader(f"{q_data['theme']} - {q_data['focused_area']}")
                st.markdown(f"**{q['question'] if 'question' in q else q['question']}**")
                
                if q_data["type"] == "stp":
                    options = [resp["text"] for resp in q["responses"]]
                    scores = [resp["score"] for resp in q["responses"]]
                    option_score_map = {text: score for text, score in zip(options, scores)}
                    
                    selected = st.radio(
                        label="Select your response:",
                        options=options,
                        index=None,
                        key=f"combined_q{st.session_state.current_question_index}",
                        label_visibility="collapsed"
                    )
                    
                    if selected:
                        score = option_score_map[selected]
                        st.session_state.combined_responses.append({
                            "theme": q_data["theme"],
                            "focused_area": q_data["focused_area"],
                            "question": q["question"],
                            "selected_text": selected,
                            "score": score
                        })
                        st.session_state.current_question_index += 1
                        st.rerun()
                
                else:  # perf
                    options = q["options"]
                    selected = st.radio(
                        label="Select your response:",
                        options=options,
                        index=None,
                        key=f"combined_q{st.session_state.current_question_index}",
                        label_visibility="collapsed"
                    )
                    
                    if selected:
                        score = options.index(selected) + 1
                        st.session_state.combined_responses.append({
                            "theme": q_data["theme"],
                            "focused_area": q_data["focused_area"],
                            "question": q["question"],
                            "selected_text": selected,
                            "score": score
                        })
                        st.session_state.current_question_index += 1
                        st.rerun()
            
            else:  # All questions answered
                # Save responses
                user_data = {
                    "user_info": st.session_state.user_info,
                    "name": st.session_state.user_info["name"],
                    "email": st.session_state.user_info["email"],
                    "designation": st.session_state.user_info["designation"],
                    "organization": st.session_state.user_info["organization"],
                    "theme": "Combined Assessment",
                    "responses": st.session_state.combined_responses,
                    "timestamp": datetime.now().isoformat()
                }
                save_response(user_data)
                
                # Store individual user's results and load organization data
                st.session_state.user_data = user_data
                org_data_all_users = get_org_data(user_data["organization"])
                st.session_state.org_data = org_data_all_users
                
                # Calculate theme scores
                theme_scores = {}
                for theme in selected_themes:
                    theme_responses = [r for r in st.session_state.combined_responses if r["theme"] == theme]
                    if theme_responses:
                        theme_score = sum(r["score"] for r in theme_responses) / len(theme_responses)
                        theme_scores[theme] = round(theme_score, 1)
                
                st.session_state.theme_scores = theme_scores
                st.session_state.stage = "confirmation"
                st.rerun()
        
        # Single theme assessment
        else:
            theme = selected_themes[0]
            theme_data = THEMES[theme]
            
            if theme_data["status"] != "active":
                st.warning(f"The **{theme}** theme is under development and cannot be assessed yet.")
                if st.button("Back to Theme Selection"):
                    st.session_state.stage = "theme_selection"
                    st.rerun()
                return
            
            st.header(f":mag: {theme} Assessment")
            
            # Source-To-Pay Process theme
            if theme == "Source-To-Pay Process":
                st.caption(f"Assessing: {', '.join(st.session_state.selected_focused_areas)}")
                responses = []
                with st.form("assessment_form"):
                    # Show questions for each selected focused area
                    for focused_area in st.session_state.selected_focused_areas:
                        st.subheader(f":arrow_right: {focused_area}")
                        for question in theme_data["focused_areas"][focused_area]:
                            st.markdown(f"**{question['number']}. {question['question']}**")
                            
                            options = [resp["text"] for resp in question["responses"]]
                            scores = [resp["score"] for resp in question["responses"]]
                            
                            # Create a mapping between option text and score
                            option_score_map = {text: score for text, score in zip(options, scores)}
                            
                            selected = st.radio(
                                label="Select your response:",
                                options=options,
                                index=None,
                                key=f"{focused_area}_q{question['number']}",
                                label_visibility="collapsed"
                            )
                            
                            if selected:
                                score = option_score_map[selected]
                                responses.append({
                                    "question": question["question"],
                                    "focused_area": focused_area,
                                    "selected_text": selected,
                                    "score": score
                                })
                    
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        if st.form_submit_button("Submit Assessment", type="primary"):
                            if len(responses) > 0:
                                # Save responses
                                user_data = {
                                    **st.session_state.user_info,
                                    "theme": theme,
                                    "responses": responses,
                                    "timestamp": datetime.now().isoformat()
                                }
                                
                                save_response(user_data)
                                
                                # Store individual user's results
                                st.session_state.user_data = user_data
                                
                                # Get ALL organization data (from all users) to calculate overall maturity
                                org_data_all_users = get_org_data(user_data["organization"])
                                st.session_state.org_data = org_data_all_users

                                # Calculate organizational maturity for this theme
                                org_maturity = calculate_org_maturity(org_data_all_users, theme)
                                st.session_state.org_maturity = org_maturity
                                
                                st.session_state.stage = "confirmation"
                                st.rerun()
                            else:
                                st.warning("Please answer all questions before submitting.")
                    with col2:
                        if st.form_submit_button("Back to Themes"):
                            st.session_state.stage = "theme_selection"
                            st.rerun()
            
            # Procurement Performance theme
            elif theme == "Procurement Performance":
                q_keys = list(theme_data["questions"].keys())
                if "performance_current_question" not in st.session_state:
                    st.session_state.performance_current_question = 0
                    st.session_state.performance_responses = {}
                
                if st.session_state.performance_current_question < len(q_keys):
                    qid = q_keys[st.session_state.performance_current_question]
                    q = theme_data["questions"][qid]

                    st.subheader(q["question"])
                    choice = st.radio("Select one:", q["options"], index=None, key=f"perf_q_{qid}")
                    if choice:
                        score = q["options"].index(choice) + 1
                        st.session_state.performance_responses[qid] = {
                            "question": q["question"],
                            "response": choice,
                            "score": score,
                            "focus_area": q["focus_area"]
                        }
                        st.session_state.performance_current_question += 1
                        st.rerun()
                else:
                    # Save responses
                    user_data = {
                        **st.session_state.user_info,
                        "theme": theme,
                        "responses": list(st.session_state.performance_responses.values()),
                        "timestamp": datetime.now().isoformat()
                    }
                    save_response(user_data)
                    
                    # Store individual user's results
                    st.session_state.user_data = user_data
                    
                    # Get ALL organization data (from all users) to calculate overall maturity
                    org_data_all_users = get_org_data(user_data["organization"])
                    st.session_state.org_data = org_data_all_users

                    # Calculate organizational maturity for this theme
                    org_maturity = calculate_org_maturity(org_data_all_users, theme)
                    st.session_state.org_maturity = org_maturity
                    
                    st.session_state.stage = "confirmation"
                    st.rerun()
            else:
                st.warning("This theme is not fully implemented yet")

    # Confirmation stage
    elif st.session_state.stage == "confirmation":
        user_data = st.session_state.user_data
        org_data = st.session_state.org_data
        
        st.header(":tada: Assessment Submitted Successfully!")
        st.balloons()
        
        st.subheader(f"Thank you for completing the assessment!")
        st.markdown(f"**Organization:** {user_data['organization']}")
        
        if "participant_count" not in st.session_state:
            if org_data:
                st.session_state.participant_count = len(org_data["users"])
            else:
                st.session_state.participant_count = 1
        
        st.markdown(f"**Participants from your organization:** {st.session_state.participant_count} user(s)")
        
        st.info("""
        **Next Steps:**
        - Your responses have been securely stored.
        - You can view the maturity assessment results at any time.
        - The more colleagues participate, the more accurate our assessment will be!
        """)
        
        # Navigation buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button(":leftwards_arrow_with_hook: Back to Themes", use_container_width=True):
                st.session_state.stage = "theme_selection"
                st.rerun()
        with col2:
            if st.button(":house: Back to Home", use_container_width=True):
                st.session_state.stage = "user_info"
                st.rerun()
        with col3:
            if st.button(":bar_chart: View Results", use_container_width=True, type="primary"):
                st.session_state.stage = "results"
                st.rerun()

    # Results stage
    elif st.session_state.stage == "results":
        user_data = st.session_state.user_data
        org_data = st.session_state.org_data
        
        st.header(f":trophy: Assessment Results")
                
        # Combined mode results
        if st.session_state.combined_mode:
            # Get theme scores from session state
            theme_scores = st.session_state.theme_scores
            
            # Calculate overall maturity
            overall_maturity = round(np.mean(list(theme_scores.values())), 1) if theme_scores else 0.0
            
            # Calculate industry benchmarks
            industry_benchmarks = {theme: THEME_BENCHMARKS.get(theme, 0) for theme in theme_scores}
            overall_industry_avg = round(np.mean(list(industry_benchmarks.values())), 1)
            
            # Display overall gauge chart
            st.plotly_chart(create_gauge_chart(overall_maturity, "Organization's Overall Maturity"), use_container_width=True)
            
            st.divider()
            st.subheader(":office: Organization Benchmarking")
            
            # Overall comparison
            st.markdown(f"**Organization's Overall Maturity:** {overall_maturity:.1f}/5.0")
            st.markdown(f"**Industry Standard Average:** {overall_industry_avg:.1f}/5.0")
            
            # Theme-wise comparison using Radar Chart
            st.subheader(":bar_chart: Theme Comparison with Industry Standards")
            st.markdown("**Source of Industry Standards:**")
            for source in INDUSTRY_STANDARD_SOURCES:
                st.markdown(f"- {source}")
            
            # Display the radar chart
            st.plotly_chart(create_radar_chart(theme_scores, industry_benchmarks), use_container_width=True)
            
            # NEW: Holistic recommendations section
            st.divider()
            st.subheader(":bulb: Strategic Recommendations & Action Plan")
            
            # Calculate maturity gap
            maturity_gap = overall_maturity - overall_industry_avg
            
            # Generate holistic recommendations
            with st.spinner("Generating strategic recommendations..."):
                holistic_rec = generate_holistic_recommendations(
                    overall_maturity,
                    maturity_gap
                )
                st.markdown(holistic_rec)
            
            # NEW: Role-specific action items
            st.subheader(":busts_in_silhouette: Role-Specific Action Items")
            
            # Get unique designations from ALL organization users
            designations = set()
            if st.session_state.org_data and "users" in st.session_state.org_data:
                for user in st.session_state.org_data["users"]:
                     # Check multiple possible locations for designation
                     designation = ""
                     
                     # Check direct field
                     if user.get("designation"):
                         designation = user["designation"]

                     # Check user_info dictionary   
                     elif user.get("user_info") and user["user_info"].get("designation"):
                         designation = user["user_info"]["designation"]

                     # Check top-level fields
                     elif "designation" in user:
                        designation = user["designation"]

                     # Clean and add if valid
                     if designation and designation.strip():
                        designations.add(designation.strip().title())           
            if designations:
                with st.spinner("Generating role-specific actions..."):
                    # Calculate gap magnitude
                    gap_magnitude = abs(maturity_gap) if maturity_gap < 0 else 0.5
                    
                    # Generate role-specific actions
                    role_actions = generate_role_specific_actions(
                        list(designations),
                        gap_magnitude
                    )
                    st.markdown(role_actions)
                    # Add expandable section with raw designation data
                    with st.expander("View participant roles"):
                         st.write(f"**{len(designations)} unique roles identified:**")
                         st.write(", ".join(sorted(designations)))
            else:
                st.info("No role information available for action item generation. Designations weren't collected from participants.")
            
            # Theme recommendations
            st.divider()
            st.subheader(":mag: Theme-Level Recommendations")
            
            for theme, score in theme_scores.items():
                industry_benchmark = industry_benchmarks.get(theme, 3.0)
                static_recommendation = get_recommendations(theme, score)
                
                with st.expander(f"{theme} (Your Org: {score:.1f} vs Industry: {industry_benchmark:.1f})"):
                    # Display static recommendation
                    st.markdown(f"**Recommendation:** {static_recommendation}")
                    
                    # Generate AI-complemented recommendations
                    if ollama_available:
                        with st.spinner(f"Generating complementary recommendations for {theme}..."):
                            ai_recommendation = generate_theme_recommendation(
                                theme, score, industry_benchmark
                            )
                            if ai_recommendation:
                                st.markdown("**AI-Enhanced Suggestions:**")
                                st.markdown(ai_recommendation)
                    else:
                        st.info("Connect Ollama for AI-powered recommendations.")
        
        # Single theme results
        else:
            theme = user_data["theme"]
            org_maturity = st.session_state.get("org_maturity")
            industry_benchmarks = {}
            
            if theme == "Source-To-Pay Process":
                industry_benchmarks = INDUSTRY_STANDARDS.get(theme, {})
            elif theme == "Procurement Performance":
                industry_benchmarks = INDUSTRY_STANDARDS.get(theme, {})
            
            # --- Only show organization-level results ---
            if org_maturity:
                st.markdown(f"**Organization:** {user_data['organization']}")
                
                # Display the gauge chart for the ORGANIZATION'S overall maturity
                overall_maturity = org_maturity['overall']
                st.plotly_chart(create_gauge_chart(overall_maturity, "Organization's Overall Maturity"), use_container_width=True)
                
                st.divider()
                st.subheader(":office: Organization Benchmarking")
                
                # Overall comparison
                overall_industry_avg = np.mean(list(industry_benchmarks.values())) if industry_benchmarks else 0
                st.markdown(f"**Organization's Overall Maturity for {theme}:** {overall_maturity:.1f}/5.0")
                st.markdown(f"**Industry Standard Average for {theme}:** {overall_industry_avg:.1f}/5.0")
                
                # Area-wise comparison using Radar Chart
                st.subheader(":bar_chart: Focused Area Comparison with Industry Standards")
                st.markdown("**Source of Industry Standards:**")
                for source in INDUSTRY_STANDARD_SOURCES:
                    st.markdown(f"- {source}")
                
                # Prepare data for visualization
                focused_areas = list(org_maturity["by_area"].keys())
                org_area_scores = {area: org_maturity["by_area"][area] for area in focused_areas}
                industry_area_scores = industry_benchmarks
                
                # Display the radar chart
                st.plotly_chart(create_radar_chart(org_area_scores, industry_area_scores), use_container_width=True)
                
                # --- NEW: Add organization-level recommendations and role-specific actions ---
                st.divider()
                st.subheader(":bulb: Strategic Recommendations & Action Plan")

                # Calculate maturity gap
                maturity_gap = overall_maturity - overall_industry_avg

                # Generate holistic recommendations
                with st.spinner("Generating strategic recommendations..."):
                    holistic_rec = generate_holistic_recommendations(
                        overall_maturity,
                        maturity_gap
                    )
                    st.markdown(holistic_rec)
                st.subheader(":busts_in_silhouette: Role-Specific Action Items")

                # Get unique designations from ALL organization users
                designations = set()
                if st.session_state.org_data and "users" in st.session_state.org_data:
                    for user in st.session_state.org_data["users"]:
                         # Check multiple possible locations for designation
                         designation = ""
                         if user.get("designation"):
                              designation = user["designation"]
                         elif user.get("user_info") and user["user_info"].get("designation"):
                              designation = user["user_info"]["designation"]
                         elif "designation" in user:
                              designation = user["designation"]
                         if designation and designation.strip():
                              designations.add(designation.strip().title())
                
                if designations:
                    with st.spinner("Generating role-specific actions..."):
                         # Calculate gap magnitude
                         gap_magnitude = abs(maturity_gap) if maturity_gap < 0 else 0.5
                    
                         # Generate role-specific actions
                         role_actions = generate_role_specific_actions(
                              list(designations),
                              gap_magnitude
                         )
                         st.markdown(role_actions)
                         # Add expandable section with raw designation data
                         with st.expander("View participant roles"):
                              st.write(f"**{len(designations)} unique roles identified:**")
                              st.write(", ".join(sorted(designations)))
                else:
                    st.info("No role information available for action item generation. Designations weren't collected from participants.")

                # Focused area recommendations
                st.divider()
                st.subheader(":mag: Focused Area Recommendations")
                
                for area in focused_areas:
                    org_score = org_maturity["by_area"][area]
                    industry_score = industry_benchmarks.get(area, 3.0)
                    
                    if theme == "Source-To-Pay Process":
                        # Convert score to integer for recommendation levels
                        score_level = str(min(5, max(1, int(round(org_score)))))
                        static_recommendation = RECOMMENDATIONS.get(area, {}).get(score_level, "No recommendation available")
                    else:  # Procurement Performance
                        # Find matching question for this focus area
                        matched_question_id = None
                        for qid, q in performance_questions.items():
                            if q["focus_area"] == area:
                                matched_question_id = qid
                                break
                        
                        static_recommendation = "No recommendation available"
                        if matched_question_id:
                            # Find recommendations in deepseek data
                            for key, val in deepseek_data.items():
                                if val["question"].strip().lower() == performance_questions[matched_question_id]["question"].strip().lower():
                                    rounded_score = str(int(round(org_score)))
                                    static_recommendation = val["recommendations"].get(rounded_score, "No recommendation available")
                                    break
                    
                    with st.expander(f"{area} (Your Org: {org_score:.1f} vs Industry: {industry_score:.1f})"):
                        # Display static recommendation
                        st.markdown(f"**Recommendation:** {static_recommendation}")
                        
                        # Generate AI-complemented recommendations
                        if ollama_available:
                            with st.spinner(f"Generating complementary recommendations for {area}..."):
                                ai_recommendation = generate_theme_recommendation(
                                    area, org_score, industry_score
                                )
                                if ai_recommendation:
                                    st.markdown("**AI-Enhanced Suggestions:**")
                                    st.markdown(ai_recommendation)
                        else:
                            st.info("Connect Ollama for AI-powered recommendations.")
            else:
                st.info("No organizational data available for comparison. Encourage more colleagues to participate to see your organization's overall maturity!")
            
        # Show detailed responses
        st.divider()
        st.subheader(":page_facing_up: Your Detailed Responses")
        
        if st.session_state.combined_mode:
            response_data = []
            for response in st.session_state.combined_responses:
                response_data.append({
                    "Theme": response["theme"],
                    "Focus Area": response["focused_area"],
                    "Question": response["question"],
                    "Your Response": response["selected_text"],
                    "Score": response["score"]
                })
            st.dataframe(pd.DataFrame(response_data), hide_index=True, use_container_width=True)
        else:
            if theme == "Source-To-Pay Process":
                response_data = []
                for response in user_data["responses"]:
                    response_data.append({
                        "Focused Area": response["focused_area"],
                        "Question": response["question"],
                        "Your Response": response["selected_text"],
                        "Score": response["score"]
                    })
                st.dataframe(pd.DataFrame(response_data), hide_index=True, use_container_width=True)
            elif theme == "Procurement Performance":
                response_data = []
                for response in user_data["responses"]:
                    response_data.append({
                        "Focus Area": response["focus_area"],
                        "Question": response["question"],
                        "Your Response": response["response"],
                        "Score": response["score"]
                    })
                st.dataframe(pd.DataFrame(response_data), hide_index=True, use_container_width=True)
        
        # Navigation buttons
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            if st.button(":leftwards_arrow_with_hook: Back to Themes", use_container_width=True):
                st.session_state.stage = "theme_selection"
                st.rerun()
        with col2:
            if st.button(":house: Back to Home", use_container_width=True):
                st.session_state.stage = "user_info"
                st.rerun()

if __name__ == "__main__":
    main()
