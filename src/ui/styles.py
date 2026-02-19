import streamlit as st

def apply_custom_styles():
    """
    Applies custom CSS for a professional, corporate look.
    Avoids setting background colors on .stMetric to prevent Streamlit Cloud rendering issues.
    """
    st.markdown("""
    <style>
        /* Main background */
        .main {
            background-color: #f5f7f9;
        }

        /* Typography */
        h1, h2, h3 {
            color: #0e1117;
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            font-weight: 600;
        }

        h1 {
            padding-bottom: 1rem;
            border-bottom: 1px solid #e0e0e0;
        }

        /* Card-like containers (optional, if we use containers) */
        div[data-testid="stVerticalBlock"] > div {
            /* padding: 1rem; */
        }

        /* Sidebar styling */
        section[data-testid="stSidebar"] {
            background-color: #262730;
            border-right: 1px solid #e0e0e0;
        }

        /* Ensure text in sidebar is white for contrast */
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] .stRadio label,
        section[data-testid="stSidebar"] .stMarkdown p,
        section[data-testid="stSidebar"] .stMarkdown li,
        section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] p {
            color: #ffffff !important;
        }

        /* Metric Styling - Clean & Minimal */
        div[data-testid="stMetricValue"] {
            font-weight: bold;
            color: #1f77b4;
        }

        /* Table headers */
        thead tr th:first-child {display:none}
        tbody th {display:none}
    </style>
    """, unsafe_allow_html=True)
