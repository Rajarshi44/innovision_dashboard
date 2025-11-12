import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from sklearn.preprocessing import MinMaxScaler, StandardScaler, RobustScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from scipy.stats import pearsonr, spearmanr
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Enhanced page configuration
st.set_page_config(
    page_title="Event Analytics Dashboard", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        padding: 1.5rem !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1) !important;
        text-align: center !important;
        margin-bottom: 1rem !important;
        border: none !important;
        min-height: 120px !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
    }
    .metric-card h3 {
        margin: 0 !important;
        font-size: 0.9rem !important;
        font-weight: 500 !important;
        opacity: 0.9 !important;
        margin-bottom: 0.5rem !important;
        color: white !important;
    }
    .metric-card h2 {
        margin: 0 !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
        color: white !important;
    }
    .chart-container {
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
    
    /* Fix selectbox styling */
    .stSelectbox > div > div {
        background-color: #ffffff !important;
        color: #262730 !important;
        border: 1px solid #ddd !important;
        border-radius: 5px !important;
    }
    
    .stSelectbox > div > div > div {
        color: #262730 !important;
        background-color: #ffffff !important;
    }
    
    .stSelectbox label {
        color: #262730 !important;
        font-weight: 600 !important;
        font-size: 14px !important;
    }
    
    /* Fix multiselect styling */
    .stMultiSelect > div > div {
        background-color: #ffffff !important;
        color: #262730 !important;
        border: 1px solid #ddd !important;
        border-radius: 5px !important;
    }
    
    .stMultiSelect > div > div > div {
        color: #262730 !important;
        background-color: #ffffff !important;
    }
    
    .stMultiSelect label {
        color: #262730 !important;
        font-weight: 600 !important;
        font-size: 14px !important;
    }
    
    /* Fix text input styling */
    .stTextInput > div > div > input {
        background-color: #ffffff !important;
        color: #262730 !important;
        border: 1px solid #ddd !important;
        border-radius: 5px !important;
    }
    
    .stTextInput label {
        color: #262730 !important;
        font-weight: 600 !important;
        font-size: 14px !important;
    }
    
    /* Fix slider styling */
    .stSlider > div > div > div {
        color: #262730 !important;
    }
    
    .stSlider label {
        color: #262730 !important;
        font-weight: 600 !important;
        font-size: 14px !important;
    }
    
    /* Fix button styling */
    .stButton > button {
        background-color: #667eea !important;
        color: white !important;
        border: none !important;
        border-radius: 5px !important;
        font-weight: 600 !important;
        padding: 0.5rem 1rem !important;
    }
    
    .stButton > button:hover {
        background-color: #764ba2 !important;
        color: white !important;
    }
    
    /* Override any Streamlit default styles */
    div[data-testid="metric-container"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 1.5rem !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1) !important;
    }
    div[data-testid="metric-container"] > div {
        color: white !important;
    }
    div[data-testid="metric-container"] label {
        color: white !important;
    }
    
    /* Fix dropdown options visibility */
    div[data-baseweb="select"] {
        background-color: #ffffff !important;
    }
    
    div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #262730 !important;
    }
    
    /* Fix dropdown menu items */
    ul[role="listbox"] {
        background-color: #ffffff !important;
        border: 1px solid #ddd !important;
        border-radius: 5px !important;
    }
    
    li[role="option"] {
        background-color: #ffffff !important;
        color: #262730 !important;
        padding: 8px 12px !important;
    }
    
    li[role="option"]:hover {
        background-color: #f0f2f6 !important;
        color: #262730 !important;
    }
    
    /* Fix selected option styling */
    div[data-baseweb="select"] span {
        color: #262730 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- Load files with enhanced error handling and data validation ---
@st.cache_data
def load_files(file_paths):
    all_data = {}
    loading_summary = {
        'files_loaded': 0,
        'sheets_loaded': 0,
        'total_records': 0,
        'errors': [],
        'warnings': []
    }
    
    for f in file_paths:
        try:
            if Path(f).suffix in ['.xlsx', '.xls']:
                file_data = pd.read_excel(f, sheet_name=None)
                all_data[Path(f).name] = file_data
                loading_summary['files_loaded'] += 1
                loading_summary['sheets_loaded'] += len(file_data)
                
                # Validate each sheet
                for sheet_name, sheet_df in file_data.items():
                    if sheet_df.empty:
                        loading_summary['warnings'].append(f"Sheet '{sheet_name}' in '{f}' is empty")
                    else:
                        loading_summary['total_records'] += len(sheet_df)
                        
                        # Check for potential data issues
                        if sheet_df.columns.duplicated().any():
                            loading_summary['warnings'].append(f"Duplicate columns found in '{sheet_name}' of '{f}'")
                        
                        # Check for completely empty columns
                        empty_cols = sheet_df.columns[sheet_df.isnull().all()].tolist()
                        if empty_cols:
                            loading_summary['warnings'].append(f"Empty columns in '{sheet_name}': {empty_cols}")
                            
        except Exception as e:
            loading_summary['errors'].append(f"Error loading {f}: {str(e)}")
            st.error(f"Error loading {f}: {str(e)}")
    
    merged = []
    for fname, sheets in all_data.items():
        for sname, df in sheets.items():
            if not df.empty:
                temp = df.copy()
                
                # Add metadata columns
                temp['source'] = f"{fname}::{sname}"
                temp['file_name'] = fname
                temp['sheet_name'] = sname
                temp['record_id'] = range(len(temp))  # Add unique record ID
                temp['load_timestamp'] = pd.Timestamp.now()  # Add load timestamp
                
                merged.append(temp)
    
    if merged:
        result = pd.concat(merged, ignore_index=True, sort=False)
        
        # Display loading summary
        st.sidebar.markdown("### 📊 Data Loading Summary")
        st.sidebar.markdown(f"**Files Loaded:** {loading_summary['files_loaded']}")
        st.sidebar.markdown(f"**Sheets Loaded:** {loading_summary['sheets_loaded']}")
        st.sidebar.markdown(f"**Total Records:** {loading_summary['total_records']:,}")
        
        if loading_summary['warnings']:
            st.sidebar.warning(f"⚠️ {len(loading_summary['warnings'])} warnings")
            with st.sidebar.expander("View Warnings"):
                for warning in loading_summary['warnings']:
                    st.write(f"• {warning}")
        
        if loading_summary['errors']:
            st.sidebar.error(f"❌ {len(loading_summary['errors'])} errors")
            with st.sidebar.expander("View Errors"):
                for error in loading_summary['errors']:
                    st.write(f"• {error}")
        
        return result
    return pd.DataFrame()

# --- Advanced data preprocessing with accuracy validation ---
@st.cache_data
def preprocess_data(df):
    if df.empty:
        return df, [], [], []
    
    # Identify column types
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    date_cols = []
    
    # Advanced date detection with validation
    for col in df.columns:
        if any(keyword in col.lower() for keyword in ['date', 'time', 'timestamp', 'created', 'updated']):
            try:
                original_values = df[col].dropna().iloc[:5].tolist()  # Sample original values
                df[col] = pd.to_datetime(df[col], errors='coerce')
                converted_values = df[col].dropna().iloc[:5].tolist()  # Sample converted values
                
                if not df[col].isna().all():
                    date_cols.append(col)
                    
                    # Validate date conversion accuracy
                    conversion_success_rate = (len(df[col].dropna()) / len(df[col][df[col].notna()])) * 100 if len(df[col][df[col].notna()]) > 0 else 0
                    if conversion_success_rate < 90:
                        st.warning(f"⚠️ Date conversion for '{col}' may be inaccurate. Success rate: {conversion_success_rate:.1f}%")
            except:
                pass
    
    # Remove system columns from analysis
    system_cols = ['source', 'file_name', 'sheet_name', 'record_id', 'load_timestamp']
    numeric_cols = [col for col in numeric_cols if col not in system_cols]
    categorical_cols = [col for col in categorical_cols if col not in system_cols]
    
    return df, numeric_cols, categorical_cols, date_cols

# --- Data accuracy validation function ---
@st.cache_data
def validate_data_accuracy(df):
    """Comprehensive data accuracy validation"""
    accuracy_report = {
        'total_records': len(df),
        'total_columns': len(df.columns),
        'data_quality_score': 0,
        'issues': [],
        'recommendations': []
    }
    
    # 1. Check for duplicate records
    duplicates = df.duplicated().sum()
    if duplicates > 0:
        duplicate_percentage = (duplicates / len(df)) * 100
        accuracy_report['issues'].append(f"🔴 {duplicates} duplicate records found ({duplicate_percentage:.1f}%)")
        accuracy_report['recommendations'].append("Consider removing duplicate records")
    
    # 2. Check for missing data patterns
    missing_data = df.isnull().sum()
    high_missing_cols = missing_data[missing_data > len(df) * 0.5].index.tolist()
    if high_missing_cols:
        accuracy_report['issues'].append(f"🔴 Columns with >50% missing data: {high_missing_cols}")
        accuracy_report['recommendations'].append("Review columns with high missing data rates")
    
    # 3. Check numeric data consistency
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if col not in ['record_id']:  # Skip system columns
            # Check for outliers using IQR method
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)][col].count()
            
            if outliers > len(df) * 0.1:  # More than 10% outliers
                outlier_percentage = (outliers / len(df)) * 100
                accuracy_report['issues'].append(f"🟡 '{col}' has {outliers} potential outliers ({outlier_percentage:.1f}%)")
    
    # 4. Check categorical data consistency
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns
    for col in categorical_cols:
        if col not in ['source', 'file_name', 'sheet_name']:  # Skip system columns
            unique_count = df[col].nunique()
            total_count = len(df[col].dropna())
            
            # Check for too many unique values (potential data entry errors)
            if unique_count > total_count * 0.8 and total_count > 10:
                accuracy_report['issues'].append(f"🟡 '{col}' has unusually high uniqueness ({unique_count}/{total_count})")
                accuracy_report['recommendations'].append(f"Review '{col}' for potential data entry inconsistencies")
    
    # 5. Check date data consistency
    date_cols = df.select_dtypes(include=['datetime64[ns]']).columns
    for col in date_cols:
        if col != 'load_timestamp':  # Skip system columns
            # Check for future dates (if not expected)
            future_dates = df[df[col] > pd.Timestamp.now()][col].count()
            if future_dates > 0:
                accuracy_report['issues'].append(f"🟡 '{col}' contains {future_dates} future dates")
            
            # Check for very old dates (potential data errors)
            very_old_dates = df[df[col] < pd.Timestamp('1900-01-01')][col].count()
            if very_old_dates > 0:
                accuracy_report['issues'].append(f"🔴 '{col}' contains {very_old_dates} dates before 1900")
    
    # 6. Calculate overall data quality score
    total_possible_issues = 10  # Base scoring system
    issues_found = len(accuracy_report['issues'])
    accuracy_report['data_quality_score'] = max(0, (total_possible_issues - issues_found) / total_possible_issues * 100)
    
    # 7. Cross-validation between sources (if multiple sources exist)
    if 'source' in df.columns and df['source'].nunique() > 1:
        sources = df['source'].unique()
        for col in numeric_cols:
            if col not in ['record_id']:
                source_means = df.groupby('source')[col].mean()
                cv = source_means.std() / source_means.mean() * 100 if source_means.mean() != 0 else 0
                
                if cv > 50:  # High variation between sources
                    accuracy_report['issues'].append(f"🟡 High variation in '{col}' between sources (CV: {cv:.1f}%)")
                    accuracy_report['recommendations'].append(f"Verify data consistency for '{col}' across different sources")
    
    return accuracy_report

# --- Statistical analysis functions ---
def calculate_statistics(df, numeric_cols):
    stats = {}
    for col in numeric_cols:
        stats[col] = {
            'mean': df[col].mean(),
            'median': df[col].median(),
            'std': df[col].std(),
            'min': df[col].min(),
            'max': df[col].max(),
            'skewness': df[col].skew(),
            'kurtosis': df[col].kurtosis(),
            'null_count': df[col].isnull().sum(),
            'unique_count': df[col].nunique()
        }
    return stats

# --- Correlation analysis ---
def correlation_analysis(df, numeric_cols):
    if len(numeric_cols) < 2:
        return None, None
    
    correlation_matrix = df[numeric_cols].corr()
    
    # Find strong correlations
    strong_correlations = []
    for i in range(len(correlation_matrix.columns)):
        for j in range(i+1, len(correlation_matrix.columns)):
            corr_val = correlation_matrix.iloc[i, j]
            if abs(corr_val) > 0.7:  # Strong correlation threshold
                strong_correlations.append({
                    'var1': correlation_matrix.columns[i],
                    'var2': correlation_matrix.columns[j],
                    'correlation': corr_val
                })
    
    return correlation_matrix, strong_correlations

# --- Load and process data ---
files = ["Supabase Snippet Event Analytic.xlsx"]  # Using only the Event Analytic file
df = load_files(files)
df, numeric_cols, categorical_cols, date_cols = preprocess_data(df)

# --- Sidebar for navigation ---
st.sidebar.title("🎛️ Event Analytics Navigation")
analysis_type = st.sidebar.selectbox(
    "Choose Analysis Type",
    ["📊 Overview", "📈 Visualizations"]
)

# --- Main Title ---
st.title("🚀 Event Analytics Dashboard")
st.markdown("**Comprehensive analysis of Event Analytics data**")
st.markdown("---")

if df.empty:
    st.error("❌ No data could be loaded. Please check your Excel files.")
    st.stop()

# --- OVERVIEW SECTION ---
if analysis_type == "📊 Overview":
    st.header("📊 Data Overview")
    
    # Data accuracy validation
    accuracy_report = validate_data_accuracy(df)
    
    # Data Quality Score prominently displayed
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); text-align: center; margin-bottom: 1rem;">
            <h3 style="margin: 0; font-size: 0.9rem; font-weight: 500; opacity: 0.9; margin-bottom: 0.5rem; color: white;">📋 Total Records</h3>
            <h2 style="margin: 0; font-size: 2rem; font-weight: 700; color: white;">{len(df):,}</h2>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); text-align: center; margin-bottom: 1rem;">
            <h3 style="margin: 0; font-size: 0.9rem; font-weight: 500; opacity: 0.9; margin-bottom: 0.5rem; color: white;">📊 Numeric Columns</h3>
            <h2 style="margin: 0; font-size: 2rem; font-weight: 700; color: white;">{len(numeric_cols)}</h2>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); text-align: center; margin-bottom: 1rem;">
            <h3 style="margin: 0; font-size: 0.9rem; font-weight: 500; opacity: 0.9; margin-bottom: 0.5rem; color: white;">📝 Categorical Columns</h3>
            <h2 style="margin: 0; font-size: 2rem; font-weight: 700; color: white;">{len(categorical_cols)}</h2>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        # Color code the quality score
        if accuracy_report['data_quality_score'] >= 80:
            quality_color = "linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%)"  # Green
        elif accuracy_report['data_quality_score'] >= 60:
            quality_color = "linear-gradient(135deg, #f7b801 0%, #f18701 100%)"  # Orange
        else:
            quality_color = "linear-gradient(135deg, #e53e3e 0%, #fc8181 100%)"  # Red
            
        st.markdown(f"""
        <div style="background: {quality_color}; color: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); text-align: center; margin-bottom: 1rem;">
            <h3 style="margin: 0; font-size: 0.9rem; font-weight: 500; opacity: 0.9; margin-bottom: 0.5rem; color: white;">🎯 Data Quality</h3>
            <h2 style="margin: 0; font-size: 2rem; font-weight: 700; color: white;">{accuracy_report['data_quality_score']:.0f}%</h2>
        </div>
        """, unsafe_allow_html=True)
    
    # Data Quality Issues and Recommendations
    if accuracy_report['issues'] or accuracy_report['recommendations']:
        st.subheader("🔍 Data Accuracy Assessment")
        
        col1, col2 = st.columns(2)
        with col1:
            if accuracy_report['issues']:
                st.markdown("**⚠️ Data Quality Issues:**")
                for issue in accuracy_report['issues']:
                    st.markdown(f"- {issue}")
            else:
                st.success("✅ No significant data quality issues detected!")
        
        with col2:
            if accuracy_report['recommendations']:
                st.markdown("**💡 Recommendations:**")
                for rec in accuracy_report['recommendations']:
                    st.markdown(f"- {rec}")
            else:
                st.info("👍 Data appears to be in good condition!")
    
    # Key metrics (keeping the existing ones)
    # col1, col2, col3, col4 = st.columns(4) - Removed duplicate
    
    # Event data breakdown
    st.subheader("� Event Data Overview")
    source_counts = df['source'].value_counts()
    
    col1, col2 = st.columns([1, 1])
    with col1:
        fig_pie = px.pie(values=source_counts.values, names=source_counts.index, 
                        title="Event Records Distribution")
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        st.dataframe(source_counts.to_frame("Event Record Count"))
    
    # Enhanced Student Count Analysis by Department-Section
    st.subheader("👥 Student Participation Analysis by Department & Section")
    
    # Check if required columns exist
    if 'department' in df.columns and 'section' in df.columns and 'student_count' in df.columns:
        
        # Clean and standardize the data
        df_clean = df.copy()
        df_clean['department'] = df_clean['department'].astype(str).str.strip().str.upper()
        df_clean['section'] = df_clean['section'].astype(str).str.strip().str.upper()
        
        # Extract year from date columns if available
        year_col = None
        for col in df_clean.columns:
            if 'year' in col.lower():
                year_col = col
                break
        
        # If no year column found, try to extract from date columns
        if year_col is None:
            for col in date_cols:
                if col in df_clean.columns:
                    df_clean['year'] = pd.to_datetime(df_clean[col], errors='coerce').dt.year
                    year_col = 'year'
                    break
        
        # Create department-section-year combination
        if year_col and year_col in df_clean.columns:
            df_clean['dept_section_year'] = df_clean['department'] + ' - ' + df_clean['section'] + ' - ' + df_clean[year_col].astype(str)
            group_by_col = 'dept_section_year'
            title_suffix = " by Department-Section-Year"
        else:
            df_clean['dept_section'] = df_clean['department'] + ' - ' + df_clean['section']
            group_by_col = 'dept_section'
            title_suffix = " by Department-Section"
        
        # Department-wise section analysis
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"#### 📊 Average Student Participation{title_suffix}")
            dept_section_avg = df_clean.groupby(group_by_col)['student_count'].mean().sort_values(ascending=False)
            
            # Create bar chart for average participation
            fig_avg = px.bar(
                x=dept_section_avg.index, 
                y=dept_section_avg.values,
                title=f"Average Student Participation per Event{title_suffix}",
                labels={'x': group_by_col.replace('_', ' ').title(), 'y': 'Avg Students per Event'},
                color=dept_section_avg.values,
                color_continuous_scale='blues'
            )
            fig_avg.update_xaxes(tickangle=45)
            st.plotly_chart(fig_avg, use_container_width=True)
            
            # Show top 10 table
            st.dataframe(dept_section_avg.head(10).round(2).to_frame("Avg Students per Event").reset_index())
        
        with col2:
            st.markdown(f"#### 📈 Event Participation Count{title_suffix}")
            dept_section_events = df_clean.groupby(group_by_col).size().sort_values(ascending=False)
            
            # Create bar chart for event counts
            fig_events = px.bar(
                x=dept_section_events.index, 
                y=dept_section_events.values,
                title=f"Number of Events Participated{title_suffix}",
                labels={'x': group_by_col.replace('_', ' ').title(), 'y': 'Number of Events'},
                color=dept_section_events.values,
                color_continuous_scale='oranges'
            )
            fig_events.update_xaxes(tickangle=45)
            st.plotly_chart(fig_events, use_container_width=True)
            
            # Show top 10 table
            st.dataframe(dept_section_events.head(10).to_frame("Events Participated").reset_index())
        
        # Department-wise summary
        st.markdown("#### 🏢 Department-wise Summary")
        dept_summary = df_clean.groupby('department').agg({
            'student_count': ['mean', 'max', 'min'],
            group_by_col: 'count',
            'section': 'nunique'
        }).round(2)
        dept_summary.columns = ['Avg Students per Event', 'Max Students in Event', 'Min Students in Event', 'Total Event Participations', 'Unique Sections']
        dept_summary = dept_summary.sort_values('Total Event Participations', ascending=False)
        
        # Display with enhanced metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1rem; border-radius: 8px; text-align: center;">
                <h4 style="margin: 0; color: white;">🏢 Total Departments</h4>
                <h2 style="margin: 0; color: white;">{df_clean['department'].nunique()}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 1rem; border-radius: 8px; text-align: center;">
                <h4 style="margin: 0; color: white;">📚 Total Sections</h4>
                <h2 style="margin: 0; color: white;">{df_clean['section'].nunique()}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white; padding: 1rem; border-radius: 8px; text-align: center;">
                <h4 style="margin: 0; color: white;">🎯 Total Event Records</h4>
                <h2 style="margin: 0; color: white;">{len(df_clean):,}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        st.dataframe(dept_summary)
        
        # Analysis interpretation
        st.markdown("#### � How to Interpret This Data")
        st.info("""
        **Important Note:** Each row in the data represents a department-section's participation in a specific event.
        
        - **Average Student Participation:** Average number of students from each dept-section per event
        - **Event Participation Count:** How many events each dept-section participated in
        - **Not Total Students:** We're measuring event participation, not unique student counts
        
        For example: If CSE-A shows 15 events and 5 avg students, it means CSE-A section participated in 15 different events with an average of 5 students per event.
        """)
        
        # Section distribution within departments
        st.markdown("#### 🗂️ Section Participation by Department")
        for dept in sorted(df_clean['department'].unique()):
            dept_data = df_clean[df_clean['department'] == dept]
            
            # Create section_year if year data exists
            if year_col and year_col in dept_data.columns:
                dept_data['section_year'] = dept_data['section'] + ' - ' + dept_data[year_col].astype(str)
                section_group_col = 'section_year'
                section_label = 'Section-Year'
            else:
                section_group_col = 'section'
                section_label = 'Section'
            
            section_stats = dept_data.groupby(section_group_col).agg({
                'student_count': ['mean', 'count', 'sum'],
                'event_name': 'nunique'
            }).round(2)
            section_stats.columns = ['Avg Students per Event', 'Event Participations', 'Total Student-Event Count', 'Unique Events']
            
            section_count = dept_data[section_group_col].nunique()
            with st.expander(f"📂 {dept} Department {section_label}s ({section_count} {section_label.lower()}s)"):
                col1, col2 = st.columns(2)
                with col1:
                    # Create pie chart for this department's event participation
                    fig_dept = px.pie(
                        values=section_stats['Event Participations'], 
                        names=section_stats.index,
                        title=f"Event Participation Distribution in {dept}"
                    )
                    st.plotly_chart(fig_dept, use_container_width=True)
                
                with col2:
                    st.dataframe(section_stats.sort_values('Event Participations', ascending=False))
        
        # Update the main dataframe for other sections
        if 'dept_section' in df_clean.columns:
            df['dept_section'] = df_clean['dept_section']
        if 'dept_section_year' in df_clean.columns:
            df['dept_section_year'] = df_clean['dept_section_year']
    
    else:
        st.warning("⚠️ Department, section, or student_count columns not found for detailed analysis.")

# --- DATA ACCURACY SECTION ---
elif analysis_type == "🎯 Data Accuracy":
    st.header("🎯 Comprehensive Data Accuracy Analysis")
    
    # Run comprehensive validation
    accuracy_report = validate_data_accuracy(df)
    
    # Overall accuracy score
    st.subheader("📊 Overall Data Quality Score")
    
    # Visual quality score indicator
    if accuracy_report['data_quality_score'] >= 90:
        score_color = "#22c55e"  # Green
        score_status = "Excellent"
        score_emoji = "🟢"
    elif accuracy_report['data_quality_score'] >= 75:
        score_color = "#3b82f6"  # Blue
        score_status = "Good"
        score_emoji = "🔵"
    elif accuracy_report['data_quality_score'] >= 60:
        score_color = "#f59e0b"  # Orange
        score_status = "Fair"
        score_emoji = "🟡"
    else:
        score_color = "#ef4444"  # Red
        score_status = "Poor"
        score_emoji = "🔴"
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {score_color}, {score_color}aa); color: white; padding: 2rem; border-radius: 15px; text-align: center; margin: 1rem 0;">
        <h1 style="margin: 0; font-size: 3rem; margin-bottom: 0.5rem;">{score_emoji} {accuracy_report['data_quality_score']:.0f}%</h1>
        <h3 style="margin: 0; opacity: 0.9;">Data Quality: {score_status}</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Detailed accuracy breakdown
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("⚠️ Data Quality Issues")
        if accuracy_report['issues']:
            for i, issue in enumerate(accuracy_report['issues'], 1):
                st.markdown(f"**{i}.** {issue}")
        else:
            st.success("✅ No significant data quality issues detected!")
    
    with col2:
        st.subheader("💡 Recommendations")
        if accuracy_report['recommendations']:
            for i, rec in enumerate(accuracy_report['recommendations'], 1):
                st.markdown(f"**{i}.** {rec}")
        else:
            st.info("👍 Data quality is good - no specific recommendations!")
    
    # Detailed validation results
    st.subheader("📋 Detailed Validation Results")
    
    # Record-level analysis
    st.markdown("#### 📊 Record-Level Analysis")
    col1, col2, col3, col4 = st.columns(4)
    
    duplicates = df.duplicated().sum()
    with col1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1rem; border-radius: 8px; text-align: center;">
            <h4 style="margin: 0; color: white;">Duplicate Records</h4>
            <h2 style="margin: 0; color: white;">{duplicates:,}</h2>
            <p style="margin: 0; opacity: 0.8;">{(duplicates/len(df)*100):.1f}% of total</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        missing_records = df.isnull().any(axis=1).sum()
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 1rem; border-radius: 8px; text-align: center;">
            <h4 style="margin: 0; color: white;">Records with Missing Data</h4>
            <h2 style="margin: 0; color: white;">{missing_records:,}</h2>
            <p style="margin: 0; opacity: 0.8;">{(missing_records/len(df)*100):.1f}% of total</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        complete_records = len(df) - missing_records
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white; padding: 1rem; border-radius: 8px; text-align: center;">
            <h4 style="margin: 0; color: white;">Complete Records</h4>
            <h2 style="margin: 0; color: white;">{complete_records:,}</h2>
            <p style="margin: 0; opacity: 0.8;">{(complete_records/len(df)*100):.1f}% of total</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        unique_records = len(df) - duplicates
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); color: white; padding: 1rem; border-radius: 8px; text-align: center;">
            <h4 style="margin: 0; color: white;">Unique Records</h4>
            <h2 style="margin: 0; color: white;">{unique_records:,}</h2>
            <p style="margin: 0; opacity: 0.8;">{(unique_records/len(df)*100):.1f}% of total</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Column-level analysis
    st.markdown("#### 🗂️ Column-Level Analysis")
    
    # Missing data heatmap
    if len(df) > 0:
        missing_data = df.isnull().sum()
        missing_percentage = (missing_data / len(df)) * 100
        
        # Create missing data visualization
        missing_df = pd.DataFrame({
            'Column': missing_data.index,
            'Missing Count': missing_data.values,
            'Missing Percentage': missing_percentage.values
        }).sort_values('Missing Percentage', ascending=False)
        
        # Filter out columns with no missing data for cleaner visualization
        missing_df_filtered = missing_df[missing_df['Missing Count'] > 0]
        
        if not missing_df_filtered.empty:
            st.markdown("**Missing Data by Column:**")
            fig = px.bar(missing_df_filtered.head(10), x='Column', y='Missing Percentage',
                        title="Top 10 Columns with Missing Data",
                        labels={'Missing Percentage': 'Missing Data (%)'},
                        color='Missing Percentage',
                        color_continuous_scale='Reds')
            fig.update_layout(xaxis_tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.success("✅ No missing data found in any columns!")
    
    # Data consistency across sources
    if 'source' in df.columns and df['source'].nunique() > 1:
        st.markdown("#### 🔄 Cross-Source Data Consistency")
        
        # Compare record counts across sources
        source_counts = df['source'].value_counts()
        fig = px.pie(values=source_counts.values, names=source_counts.index,
                    title="Record Distribution Across Sources")
        st.plotly_chart(fig, use_container_width=True)
        
        # Consistency metrics for numeric columns
        if numeric_cols:
            consistency_metrics = []
            for col in numeric_cols[:5]:  # Top 5 numeric columns
                source_stats = df.groupby('source')[col].agg(['mean', 'std']).round(3)
                cv = (source_stats['std'] / source_stats['mean'] * 100).mean()
                consistency_metrics.append({
                    'Column': col,
                    'Coefficient of Variation (%)': cv,
                    'Consistency': 'High' if cv < 20 else 'Medium' if cv < 50 else 'Low'
                })
            
            consistency_df = pd.DataFrame(consistency_metrics)
            st.markdown("**Numeric Data Consistency Across Sources:**")
            st.dataframe(consistency_df)
    
    # Export accuracy report
    st.subheader("📥 Export Accuracy Report")
    if st.button("📊 Generate Detailed Accuracy Report"):
        # Create comprehensive report
        report_data = {
            'Data Quality Score': [accuracy_report['data_quality_score']],
            'Total Records': [accuracy_report['total_records']],
            'Total Columns': [accuracy_report['total_columns']],
            'Duplicate Records': [duplicates],
            'Records with Missing Data': [missing_records],
            'Complete Records': [complete_records],
            'Issues Found': [len(accuracy_report['issues'])],
            'Recommendations': [len(accuracy_report['recommendations'])]
        }
        
        report_df = pd.DataFrame(report_data)
        csv_report = report_df.to_csv(index=False)
        
        st.download_button(
            label="📥 Download Accuracy Report (CSV)",
            data=csv_report,
            file_name=f"data_accuracy_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
        
        st.success("✅ Accuracy report generated successfully!")

# --- VISUALIZATIONS SECTION ---
elif analysis_type == "📈 Visualizations":
    st.header("📈 Advanced Visualizations")
    
    if not numeric_cols:
        st.warning("⚠️ No numeric columns found for visualization.")
        st.stop()
    
    # Chart type selection
    chart_type = st.selectbox("🎨 Select Chart Type", [
        "📊 Interactive Bar Charts", "🎯 Scatter Plots", "📦 Box Plots", 
        "🌡️ Heatmaps", "📊 Histograms", "🎯 Violin Plots", "📈 3D Scatter Plots"
    ])
    
    # Enhanced variable selection with department-section combinations
    if 'department' in df.columns and 'section' in df.columns:
        # Clean and standardize department and section data
        df['department_clean'] = df['department'].astype(str).str.strip().str.upper()
        df['section_clean'] = df['section'].astype(str).str.strip().str.upper()
        df['dept_section'] = df['department_clean'] + ' - ' + df['section_clean']
        
        # Extract year if available
        year_col = None
        for col in df.columns:
            if 'year' in col.lower():
                year_col = col
                break
        
        # If no year column found, try to extract from date columns
        if year_col is None:
            for col in date_cols:
                if col in df.columns:
                    df['year'] = pd.to_datetime(df[col], errors='coerce').dt.year
                    year_col = 'year'
                    break
        
        # Create department-section-year combination
        if year_col and year_col in df.columns:
            df['dept_section_year'] = df['department_clean'] + ' - ' + df['section_clean'] + ' - ' + df[year_col].astype(str)
            categorical_cols = [col for col in categorical_cols if col not in ['department', 'section']] + ['department_clean', 'section_clean', 'dept_section', 'dept_section_year']
        else:
            categorical_cols = [col for col in categorical_cols if col not in ['department', 'section']] + ['department_clean', 'section_clean', 'dept_section']
    
    col1, col2 = st.columns(2)
    with col1:
        x_var = st.selectbox("🔸 X Variable", ['source'] + numeric_cols + categorical_cols)
    with col2:
        y_var = st.selectbox("🔹 Y Variable", numeric_cols)
    
    # Enhanced color coding with department-section-year options
    color_options = [None, 'source'] + categorical_cols + numeric_cols
    if 'dept_section_year' in df.columns:
        color_options = [None, 'source', 'department_clean', 'section_clean', 'dept_section', 'dept_section_year'] + [col for col in categorical_cols + numeric_cols if col not in ['department_clean', 'section_clean', 'dept_section', 'dept_section_year']]
    elif 'dept_section' in df.columns:
        color_options = [None, 'source', 'department_clean', 'section_clean', 'dept_section'] + [col for col in categorical_cols + numeric_cols if col not in ['department_clean', 'section_clean', 'dept_section']]
    
    color_var = st.selectbox("🎨 Color By", color_options)
    
    # Aggregation method selection
    if chart_type == "📊 Interactive Bar Charts":
        agg_method = st.selectbox("🔧 Aggregation Method", 
                                 ["sum", "mean", "count", "min", "max"],
                                 format_func=lambda x: {
                                     "sum": "📊 Total (Sum)",
                                     "mean": "📈 Average (Mean)", 
                                     "count": "🔢 Count",
                                     "min": "⬇️ Minimum",
                                     "max": "⬆️ Maximum"
                                 }[x])
    
    # Generate charts based on selection
    if chart_type == "📊 Interactive Bar Charts":
        if x_var in categorical_cols or x_var == 'source':
            # Apply selected aggregation method
            if agg_method == "sum":
                agg_data = df.groupby(x_var)[y_var].sum().reset_index()
                chart_title = f"Total {y_var} by {x_var}"
            elif agg_method == "mean":
                agg_data = df.groupby(x_var)[y_var].mean().reset_index()
                chart_title = f"Average {y_var} by {x_var}"
            elif agg_method == "count":
                agg_data = df.groupby(x_var)[y_var].count().reset_index()
                chart_title = f"Count of {y_var} by {x_var}"
            elif agg_method == "min":
                agg_data = df.groupby(x_var)[y_var].min().reset_index()
                chart_title = f"Minimum {y_var} by {x_var}"
            else:  # max
                agg_data = df.groupby(x_var)[y_var].max().reset_index()
                chart_title = f"Maximum {y_var} by {x_var}"
            
            # Only use color if it exists in the aggregated data
            if color_var and color_var in agg_data.columns:
                fig = px.bar(agg_data, x=x_var, y=y_var, 
                            title=chart_title,
                            color=color_var)
            else:
                fig = px.bar(agg_data, x=x_var, y=y_var, 
                            title=chart_title)
        else:
            fig = px.histogram(df, x=x_var, y=y_var, color=color_var if color_var and color_var in df.columns else None,
                             title=f"{y_var} Distribution by {x_var}")
        st.plotly_chart(fig, use_container_width=True)
        
        # Show detailed analysis summary after the chart
        if x_var in categorical_cols or x_var == 'source':
            st.markdown("#### 📊 Detailed Analysis Summary")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                total_sum = df.groupby(x_var)[y_var].sum().sum()
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1rem; border-radius: 8px; text-align: center;">
                    <h4 style="margin: 0; color: white;">📊 Total Sum</h4>
                    <h2 style="margin: 0; color: white;">{total_sum:,.0f}</h2>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                avg_value = df.groupby(x_var)[y_var].mean().mean()
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 1rem; border-radius: 8px; text-align: center;">
                    <h4 style="margin: 0; color: white;">📈 Overall Average</h4>
                    <h2 style="margin: 0; color: white;">{avg_value:.1f}</h2>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                unique_categories = df[x_var].nunique()
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white; padding: 1rem; border-radius: 8px; text-align: center;">
                    <h4 style="margin: 0; color: white;">🗂️ Categories</h4>
                    <h2 style="margin: 0; color: white;">{unique_categories}</h2>
                </div>
                """, unsafe_allow_html=True)
            
            # Show detailed breakdown table
            st.markdown("#### 📋 Complete Statistical Breakdown")
            detailed_stats = df.groupby(x_var)[y_var].agg(['sum', 'mean', 'count', 'min', 'max']).round(2)
            detailed_stats.columns = ['Total', 'Average', 'Count', 'Minimum', 'Maximum']
            detailed_stats = detailed_stats.sort_values('Total', ascending=False)
            
            # Add percentage of total
            detailed_stats['% of Total'] = (detailed_stats['Total'] / detailed_stats['Total'].sum() * 100).round(1)
            
            st.dataframe(detailed_stats)
            
            # Highlight top performers
            if len(detailed_stats) > 1:
                top_total = detailed_stats.index[0]
                top_avg = detailed_stats.sort_values('Average', ascending=False).index[0]
                
                col1, col2 = st.columns(2)
                with col1:
                    st.success(f"🏆 **Highest Total:** {top_total} ({detailed_stats.loc[top_total, 'Total']:,.0f} - {detailed_stats.loc[top_total, '% of Total']:.1f}%)")
                with col2:
                    st.info(f"⭐ **Highest Average:** {top_avg} ({detailed_stats.loc[top_avg, 'Average']:.1f})")
                
                # Additional insights
                st.markdown("#### 💡 Key Insights")
                insights = []
                
                # Most popular event (highest total)
                insights.append(f"📊 **{top_total}** has the highest total {y_var.lower()} with {detailed_stats.loc[top_total, 'Total']:,.0f}")
                
                # Most efficient event (highest average)
                if top_avg != top_total:
                    insights.append(f"⭐ **{top_avg}** has the highest average {y_var.lower()} per record with {detailed_stats.loc[top_avg, 'Average']:.1f}")
                
                # Distribution insight
                total_variance = detailed_stats['Total'].std()
                if total_variance > detailed_stats['Total'].mean() * 0.5:
                    insights.append(f"📈 High variation in {y_var.lower()} across {x_var.lower()} (suggests different event sizes/types)")
                else:
                    insights.append(f"📊 Relatively consistent {y_var.lower()} across {x_var.lower()}")
                
                for insight in insights:
                    st.markdown(f"- {insight}")
            
            # Download detailed breakdown
            if st.button("📥 Download Detailed Analysis", key="download_analysis"):
                csv_data = detailed_stats.to_csv()
                st.download_button(
                    label="📊 Download Complete Analysis (CSV)",
                    data=csv_data,
                    file_name=f"{y_var}_by_{x_var}_analysis_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    key="download_csv"
                )
    
    elif chart_type == "📈 Line Charts":
        if date_cols and len(date_cols) > 0:
            date_col = st.selectbox("📅 Date Column", date_cols)
            time_agg = st.selectbox("⏰ Time Aggregation", ["D", "W", "M", "Q", "Y"],
                                   format_func=lambda x: {"D": "Daily", "W": "Weekly", "M": "Monthly", "Q": "Quarterly", "Y": "Yearly"}[x])
            
            try:
                df_clean = df.dropna(subset=[date_col, y_var]).copy()
                df_clean[date_col] = pd.to_datetime(df_clean[date_col], errors='coerce')
                df_clean = df_clean.dropna(subset=[date_col])
                
                if len(df_clean) > 0:
                    df_clean = df_clean.set_index(date_col)
                    
                    if color_var and color_var in df_clean.columns:
                        fig = go.Figure()
                        for group_val in df_clean[color_var].unique():
                            group_data = df_clean[df_clean[color_var] == group_val]
                            if len(group_data) > 0:
                                resampled = group_data[y_var].resample(time_agg).mean()
                                fig.add_trace(go.Scatter(x=resampled.index, y=resampled.values,
                                                       mode='lines+markers', name=str(group_val)))
                        fig.update_layout(title=f"{y_var} Trend Over Time ({time_agg})",
                                        xaxis_title="Date", yaxis_title=y_var)
                    else:
                        resampled = df_clean[y_var].resample(time_agg).mean()
                        fig = px.line(x=resampled.index, y=resampled.values,
                                     title=f"{y_var} Trend Over Time ({time_agg})")
                        fig.update_layout(xaxis_title="Date", yaxis_title=y_var)
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("⚠️ No valid date data available after cleaning.")
            except Exception as e:
                st.error(f"❌ Error creating line chart: {str(e)}")
                st.info("💡 Try selecting a different date column or check your date format.")
        else:
            st.warning("⚠️ No date columns available for time series. Line charts require date/time data.")
    
    elif chart_type == "📉 Area Charts":
        if date_cols and len(date_cols) > 0:
            date_col = st.selectbox("📅 Date Column", date_cols)
            time_agg = st.selectbox("⏰ Time Aggregation", ["D", "W", "M"],
                                   format_func=lambda x: {"D": "Daily", "W": "Weekly", "M": "Monthly"}[x])
            
            try:
                df_clean = df.dropna(subset=[date_col, y_var]).copy()
                df_clean[date_col] = pd.to_datetime(df_clean[date_col], errors='coerce')
                df_clean = df_clean.dropna(subset=[date_col])
                
                if len(df_clean) > 0 and 'source' in df_clean.columns:
                    df_clean = df_clean.set_index(date_col)
                    resampled = df_clean.groupby('source')[y_var].resample(time_agg).sum().unstack(0).fillna(0)
                    
                    fig = go.Figure()
                    for col in resampled.columns:
                        fig.add_trace(go.Scatter(x=resampled.index, y=resampled[col],
                                               mode='lines', stackgroup='one', name=col))
                    fig.update_layout(title=f"Stacked Area Chart: {y_var} Over Time ({time_agg})",
                                    xaxis_title="Date", yaxis_title=y_var)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("⚠️ No valid date data available after cleaning.")
            except Exception as e:
                st.error(f"❌ Error creating area chart: {str(e)}")
                st.info("💡 Try selecting a different date column or check your date format.")
        else:
            st.warning("⚠️ No date columns available for time series. Area charts require date/time data.")
    
    elif chart_type == "🎯 Scatter Plots":
        if len(numeric_cols) >= 2:
            x_scatter = st.selectbox("🔸 X Axis", numeric_cols, key="scatter_x")
            y_scatter = st.selectbox("🔹 Y Axis", [col for col in numeric_cols if col != x_scatter], key="scatter_y")
            
            # Only use color if it exists in the dataframe
            color_to_use = color_var if color_var and color_var in df.columns else None
            fig = px.scatter(df, x=x_scatter, y=y_scatter, color=color_to_use,
                           title=f"Scatter Plot: {y_scatter} vs {x_scatter}",
                           hover_data=['source'])
            st.plotly_chart(fig, use_container_width=True)
    
    elif chart_type == "📦 Box Plots":
        color_to_use = color_var if color_var and color_var in df.columns else None
        fig = px.box(df, x=x_var if x_var in categorical_cols else 'source', 
                    y=y_var, color=color_to_use,
                    title=f"Box Plot: {y_var} Distribution")
        st.plotly_chart(fig, use_container_width=True)
    
    elif chart_type == "🌡️ Heatmaps":
        if len(numeric_cols) >= 2:
            corr_matrix = df[numeric_cols].corr()
            fig = px.imshow(corr_matrix, text_auto=True, aspect="auto",
                           title="Correlation Heatmap")
            st.plotly_chart(fig, use_container_width=True)
    
    elif chart_type == "📊 Histograms":
        color_to_use = color_var if color_var and color_var in df.columns else None
        fig = px.histogram(df, x=y_var, color=color_to_use, marginal="box",
                          title=f"Distribution of {y_var}")
        st.plotly_chart(fig, use_container_width=True)
    
    elif chart_type == "🎯 Violin Plots":
        color_to_use = color_var if color_var and color_var in df.columns else None
        fig = px.violin(df, x=x_var if x_var in categorical_cols else 'source', 
                       y=y_var, color=color_to_use, box=True,
                       title=f"Violin Plot: {y_var} Distribution")
        st.plotly_chart(fig, use_container_width=True)
    
    elif chart_type == "📈 3D Scatter Plots":
        if len(numeric_cols) >= 3:
            x_3d = st.selectbox("🔸 X Axis", numeric_cols, key="3d_x")
            y_3d = st.selectbox("🔹 Y Axis", [col for col in numeric_cols if col != x_3d], key="3d_y")
            z_3d = st.selectbox("🔺 Z Axis", [col for col in numeric_cols if col not in [x_3d, y_3d]], key="3d_z")
            
            color_to_use = color_var if color_var and color_var in df.columns else None
            fig = px.scatter_3d(df, x=x_3d, y=y_3d, z=z_3d, color=color_to_use,
                              title=f"3D Scatter: {x_3d} vs {y_3d} vs {z_3d}")
            st.plotly_chart(fig, use_container_width=True)

# --- DATA COMPARISON SECTION ---
elif analysis_type == "🔍 Data Comparison":
    st.header("🔍 Advanced Data Comparison")
    
    comparison_type = st.selectbox("🔄 Comparison Type", [
        "📊 Side-by-Side Comparison", "📈 Trend Comparison", "📋 Statistical Comparison",
        "🎯 Performance Metrics", "📉 Growth Analysis"
    ])
    
    # Source selection for comparison
    available_sources = df['source'].unique()
    selected_sources = st.multiselect("🎯 Select Sources to Compare", 
                                    available_sources, 
                                    default=available_sources[:2] if len(available_sources) >= 2 else available_sources)
    
    if len(selected_sources) < 2:
        st.warning("⚠️ Please select at least 2 sources for comparison.")
    else:
        comparison_df = df[df['source'].isin(selected_sources)]
        
        if comparison_type == "📊 Side-by-Side Comparison":
            if numeric_cols:
                selected_metrics = st.multiselect("📊 Select Metrics", numeric_cols, default=numeric_cols[:3])
                
                # Create comparison charts
                for metric in selected_metrics:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Bar comparison
                        agg_data = comparison_df.groupby('source')[metric].agg(['mean', 'sum', 'count']).reset_index()
                        fig_bar = px.bar(agg_data, x='source', y='mean', 
                                        title=f"Average {metric} Comparison")
                        st.plotly_chart(fig_bar, use_container_width=True)
                    
                    with col2:
                        # Box comparison
                        fig_box = px.box(comparison_df, x='source', y=metric,
                                        title=f"{metric} Distribution Comparison")
                        st.plotly_chart(fig_box, use_container_width=True)
        
        elif comparison_type == "📈 Trend Comparison" and date_cols:
            date_col = st.selectbox("📅 Select Date Column", date_cols)
            metric_col = st.selectbox("📊 Select Metric", numeric_cols)
            
            df_clean = comparison_df.dropna(subset=[date_col, metric_col])
            df_clean[date_col] = pd.to_datetime(df_clean[date_col])
            df_clean = df_clean.set_index(date_col)
            
            fig = go.Figure()
            for source in selected_sources:
                source_data = df_clean[df_clean['source'] == source]
                if not source_data.empty:
                    trend_data = source_data[metric_col].resample('D').mean()
                    fig.add_trace(go.Scatter(x=trend_data.index, y=trend_data.values,
                                           mode='lines+markers', name=source))
            
            fig.update_layout(title=f"{metric_col} Trend Comparison", xaxis_title="Date", yaxis_title=metric_col)
            st.plotly_chart(fig, use_container_width=True)
        
        elif comparison_type == "📋 Statistical Comparison":
            if numeric_cols:
                comparison_stats = []
                for source in selected_sources:
                    source_data = comparison_df[comparison_df['source'] == source]
                    for col in numeric_cols:
                        comparison_stats.append({
                            'Source': source,
                            'Metric': col,
                            'Mean': source_data[col].mean(),
                            'Median': source_data[col].median(),
                            'Std Dev': source_data[col].std(),
                            'Min': source_data[col].min(),
                            'Max': source_data[col].max(),
                            'Count': source_data[col].count()
                        })
                
                stats_df = pd.DataFrame(comparison_stats)
                st.dataframe(stats_df)
                
                # Statistical significance testing
                if len(selected_sources) == 2 and len(numeric_cols) > 0:
                    st.subheader("🧪 Statistical Significance Tests")
                    test_col = st.selectbox("Select column for t-test", numeric_cols)
                    
                    group1 = comparison_df[comparison_df['source'] == selected_sources[0]][test_col].dropna()
                    group2 = comparison_df[comparison_df['source'] == selected_sources[1]][test_col].dropna()
                    
                    if len(group1) > 1 and len(group2) > 1:
                        from scipy.stats import ttest_ind
                        t_stat, p_value = ttest_ind(group1, group2)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"""
                            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); text-align: center; margin-bottom: 1rem;">
                                <h3 style="margin: 0; font-size: 0.9rem; font-weight: 500; opacity: 0.9; margin-bottom: 0.5rem; color: white;">📊 T-Statistic</h3>
                                <h2 style="margin: 0; font-size: 2rem; font-weight: 700; color: white;">{t_stat:.4f}</h2>
                            </div>
                            """, unsafe_allow_html=True)
                        with col2:
                            st.markdown(f"""
                            <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); text-align: center; margin-bottom: 1rem;">
                                <h3 style="margin: 0; font-size: 0.9rem; font-weight: 500; opacity: 0.9; margin-bottom: 0.5rem; color: white;">📈 P-Value</h3>
                                <h2 style="margin: 0; font-size: 2rem; font-weight: 700; color: white;">{p_value:.4f}</h2>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        if p_value < 0.05:
                            st.success("✅ Statistically significant difference detected (p < 0.05)")
                        else:
                            st.info("ℹ️ No statistically significant difference (p ≥ 0.05)")

# --- STATISTICAL ANALYSIS SECTION ---
elif analysis_type == "📋 Statistical Analysis":
    st.header("📋 Comprehensive Statistical Analysis")
    
    if not numeric_cols:
        st.warning("⚠️ No numeric columns available for statistical analysis.")
    else:
        # Calculate comprehensive statistics
        stats = calculate_statistics(df, numeric_cols)
        
        # Display statistics table
        stats_df = pd.DataFrame(stats).T
        st.subheader("📊 Descriptive Statistics")
        st.dataframe(stats_df.round(4))
        
        # Statistical insights
        st.subheader("🔍 Statistical Insights")
        insights = []
        
        for col, stat in stats.items():
            # Skewness interpretation
            if abs(stat['skewness']) > 1:
                skew_type = "highly skewed" if abs(stat['skewness']) > 2 else "moderately skewed"
                direction = "right" if stat['skewness'] > 0 else "left"
                insights.append(f"📊 **{col}** is {skew_type} to the {direction} (skewness: {stat['skewness']:.2f})")
            
            # Outlier detection using IQR method
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)][col].count()
            
            if outliers > 0:
                outlier_pct = (outliers / len(df)) * 100
                insights.append(f"⚠️ **{col}** has {outliers} potential outliers ({outlier_pct:.1f}% of data)")
        
        for insight in insights:
            st.markdown(f"- {insight}")
        
        # Distribution analysis
        st.subheader("📈 Distribution Analysis")
        selected_col = st.selectbox("Select column for distribution analysis", numeric_cols)
        
        col1, col2 = st.columns(2)
        with col1:
            # Histogram with normal curve overlay
            fig, ax = plt.subplots(figsize=(10, 6))
            df[selected_col].hist(bins=30, alpha=0.7, ax=ax, density=True)
            
            # Add normal curve
            mu, sigma = df[selected_col].mean(), df[selected_col].std()
            x = np.linspace(df[selected_col].min(), df[selected_col].max(), 100)
            y = ((np.pi*sigma) * np.sqrt(2 * np.pi)) ** -1 * np.exp(-0.5 * (x - mu) ** 2 / sigma ** 2)
            ax.plot(x, y, 'r-', linewidth=2, label='Normal Distribution')
            ax.set_title(f'Distribution of {selected_col}')
            ax.legend()
            st.pyplot(fig)
        
        with col2:
            # Q-Q plot for normality assessment
            from scipy import stats
            fig, ax = plt.subplots(figsize=(10, 6))
            stats.probplot(df[selected_col].dropna(), dist="norm", plot=ax)
            ax.set_title(f'Q-Q Plot: {selected_col}')
            st.pyplot(fig)

# --- CLUSTERING ANALYSIS SECTION ---
elif analysis_type == "🎯 Clustering Analysis":
    st.header("🎯 Advanced Clustering Analysis")
    
    if len(numeric_cols) < 2:
        st.warning("⚠️ Need at least 2 numeric columns for clustering analysis.")
    else:
        # Feature selection for clustering
        selected_features = st.multiselect("🎯 Select Features for Clustering", 
                                         numeric_cols, 
                                         default=numeric_cols[:min(4, len(numeric_cols))])
        
        if len(selected_features) >= 2:
            # Prepare data for clustering
            cluster_data = df[selected_features].dropna()
            
            # Scaling options
            scaler_type = st.selectbox("🔧 Select Scaling Method", 
                                     ["StandardScaler", "MinMaxScaler", "RobustScaler", "None"])
            
            if scaler_type != "None":
                if scaler_type == "StandardScaler":
                    scaler = StandardScaler()
                elif scaler_type == "MinMaxScaler":
                    scaler = MinMaxScaler()
                else:
                    scaler = RobustScaler()
                
                scaled_data = scaler.fit_transform(cluster_data)
                scaled_df = pd.DataFrame(scaled_data, columns=selected_features)
            else:
                scaled_df = cluster_data
            
            # Optimal number of clusters using elbow method
            st.subheader("📊 Optimal Number of Clusters")
            max_clusters = min(10, len(scaled_df) // 5)
            
            if max_clusters >= 2:
                inertias = []
                silhouette_scores = []
                k_range = range(2, max_clusters + 1)
                
                for k in k_range:
                    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
                    kmeans.fit(scaled_df)
                    inertias.append(kmeans.inertia_)
                    silhouette_scores.append(silhouette_score(scaled_df, kmeans.labels_))
                
                col1, col2 = st.columns(2)
                with col1:
                    # Elbow curve
                    fig, ax = plt.subplots(figsize=(10, 6))
                    ax.plot(k_range, inertias, 'bo-')
                    ax.set_xlabel('Number of Clusters')
                    ax.set_ylabel('Inertia')
                    ax.set_title('Elbow Method for Optimal k')
                    st.pyplot(fig)
                
                with col2:
                    # Silhouette scores
                    fig, ax = plt.subplots(figsize=(10, 6))
                    ax.plot(k_range, silhouette_scores, 'ro-')
                    ax.set_xlabel('Number of Clusters')
                    ax.set_ylabel('Silhouette Score')
                    ax.set_title('Silhouette Score by Number of Clusters')
                    st.pyplot(fig)
                
                # Optimal k selection
                optimal_k = k_range[np.argmax(silhouette_scores)]
                st.info(f"💡 Recommended number of clusters: {optimal_k} (highest silhouette score: {max(silhouette_scores):.3f})")
                
                # User selection of k
                selected_k = st.slider("🎛️ Select Number of Clusters", 2, max_clusters, optimal_k)
                
                # Perform clustering
                kmeans = KMeans(n_clusters=selected_k, random_state=42, n_init=10)
                cluster_labels = kmeans.fit_predict(scaled_df)
                
                # Add cluster labels to original data
                clustered_df = cluster_data.copy()
                clustered_df['Cluster'] = cluster_labels
                clustered_df['Source'] = df.loc[cluster_data.index, 'source']
                
                # Cluster visualization
                st.subheader("🎨 Cluster Visualization")
                
                if len(selected_features) >= 2:
                    x_axis = st.selectbox("🔸 X Axis", selected_features, key="cluster_x")
                    y_axis = st.selectbox("🔹 Y Axis", [col for col in selected_features if col != x_axis], key="cluster_y")
                    
                    fig = px.scatter(clustered_df, x=x_axis, y=y_axis, 
                                   color='Cluster', symbol='Source',
                                   title=f"Clusters: {x_axis} vs {y_axis}")
                    st.plotly_chart(fig, use_container_width=True)
                
                # Cluster characteristics
                st.subheader("📋 Cluster Characteristics")
                cluster_summary = clustered_df.groupby('Cluster')[selected_features].agg(['mean', 'std', 'count'])
                st.dataframe(cluster_summary.round(3))
                
                # Cluster composition by source
                st.subheader("🎯 Cluster Composition by Source")
                cluster_composition = pd.crosstab(clustered_df['Cluster'], clustered_df['Source'], normalize='index') * 100
                fig = px.imshow(cluster_composition, text_auto='.1f', aspect="auto",
                               title="Cluster Composition by Source (%)")
                st.plotly_chart(fig, use_container_width=True)

# --- CORRELATION ANALYSIS SECTION ---
elif analysis_type == "📊 Correlation Analysis":
    st.header("📊 Advanced Correlation Analysis")
    
    if len(numeric_cols) < 2:
        st.warning("⚠️ Need at least 2 numeric columns for correlation analysis.")
    else:
        correlation_matrix, strong_correlations = correlation_analysis(df, numeric_cols)
        
        # Correlation heatmap
        st.subheader("🌡️ Correlation Matrix")
        fig = px.imshow(correlation_matrix, text_auto=True, aspect="auto",
                       title="Pearson Correlation Matrix",
                       color_continuous_scale="RdBu_r")
        st.plotly_chart(fig, use_container_width=True)
        
        # Strong correlations
        if strong_correlations:
            st.subheader("🔗 Strong Correlations (|r| > 0.7)")
            for corr in strong_correlations:
                correlation_strength = "Very Strong" if abs(corr['correlation']) > 0.9 else "Strong"
                correlation_direction = "Positive" if corr['correlation'] > 0 else "Negative"
                st.markdown(f"- **{corr['var1']}** ↔ **{corr['var2']}**: {correlation_strength} {correlation_direction} correlation (r = {corr['correlation']:.3f})")
        else:
            st.info("ℹ️ No strong correlations found.")
        
        # Detailed correlation analysis
        st.subheader("🔍 Detailed Correlation Analysis")
        col1, col2 = st.columns(2)
        
        with col1:
            var1 = st.selectbox("🔸 Variable 1", numeric_cols, key="corr_var1")
        with col2:
            var2 = st.selectbox("🔹 Variable 2", [col for col in numeric_cols if col != var1], key="corr_var2")
        
            # Calculate correlations
            clean_data = df[[var1, var2]].dropna()
            if len(clean_data) > 3:
                pearson_corr, pearson_p = pearsonr(clean_data[var1], clean_data[var2])
                spearman_corr, spearman_p = spearmanr(clean_data[var1], clean_data[var2])
                
                # Display correlation metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); text-align: center; margin-bottom: 1rem;">
                        <h3 style="margin: 0; font-size: 0.9rem; font-weight: 500; opacity: 0.9; margin-bottom: 0.5rem; color: white;">📊 Pearson r</h3>
                        <h2 style="margin: 0; font-size: 2rem; font-weight: 700; color: white;">{pearson_corr:.4f}</h2>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); text-align: center; margin-bottom: 1rem;">
                        <h3 style="margin: 0; font-size: 0.9rem; font-weight: 500; opacity: 0.9; margin-bottom: 0.5rem; color: white;">📈 P-value</h3>
                        <h2 style="margin: 0; font-size: 2rem; font-weight: 700; color: white;">{pearson_p:.4f}</h2>
                    </div>
                    """, unsafe_allow_html=True)
                with col3:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); text-align: center; margin-bottom: 1rem;">
                        <h3 style="margin: 0; font-size: 0.9rem; font-weight: 500; opacity: 0.9; margin-bottom: 0.5rem; color: white;">📊 Spearman ρ</h3>
                        <h2 style="margin: 0; font-size: 2rem; font-weight: 700; color: white;">{spearman_corr:.4f}</h2>
                    </div>
                    """, unsafe_allow_html=True)
                with col4:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); color: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); text-align: center; margin-bottom: 1rem;">
                        <h3 style="margin: 0; font-size: 0.9rem; font-weight: 500; opacity: 0.9; margin-bottom: 0.5rem; color: white;">📈 P-value</h3>
                        <h2 style="margin: 0; font-size: 2rem; font-weight: 700; color: white;">{spearman_p:.4f}</h2>
                    </div>
                    """, unsafe_allow_html=True)            # Scatter plot with regression line
            fig = px.scatter(clean_data, x=var1, y=var2, 
                           title=f"Correlation: {var1} vs {var2}",
                           trendline="ols")
            st.plotly_chart(fig, use_container_width=True)
            
            # Interpretation
            if abs(pearson_corr) > 0.7:
                strength = "strong"
            elif abs(pearson_corr) > 0.3:
                strength = "moderate"
            else:
                strength = "weak"
            
            direction = "positive" if pearson_corr > 0 else "negative"
            significance = "statistically significant" if pearson_p < 0.05 else "not statistically significant"
            
            st.info(f"📊 **Interpretation**: There is a {strength} {direction} correlation between {var1} and {var2}. This correlation is {significance} (p = {pearson_p:.4f}).")

# --- TIME SERIES ANALYSIS SECTION ---
elif analysis_type == "📉 Time Series Analysis":
    st.header("📉 Advanced Time Series Analysis")
    
    if not date_cols:
        st.warning("⚠️ No date columns found for time series analysis.")
    else:
        # Date and metric selection
        col1, col2 = st.columns(2)
        with col1:
            date_col = st.selectbox("📅 Select Date Column", date_cols)
        with col2:
            metric_col = st.selectbox("📊 Select Metric", numeric_cols)
        
        # Data preparation
        ts_data = df[[date_col, metric_col, 'source']].dropna()
        ts_data[date_col] = pd.to_datetime(ts_data[date_col])
        ts_data = ts_data.sort_values(date_col)
        
        # Time aggregation
        time_agg = st.selectbox("⏰ Time Aggregation", ["D", "W", "M", "Q", "Y"], 
                              format_func=lambda x: {"D": "Daily", "W": "Weekly", "M": "Monthly", "Q": "Quarterly", "Y": "Yearly"}[x])
        
        # Aggregation method
        agg_method = st.selectbox("🔧 Aggregation Method", ["sum", "mean", "count", "min", "max"])
        
        # Create time series
        st.subheader("📈 Time Series Visualization")
        fig = go.Figure()
        
        for source in ts_data['source'].unique():
            source_data = ts_data[ts_data['source'] == source].set_index(date_col)
            if agg_method == "sum":
                resampled = source_data[metric_col].resample(time_agg).sum()
            elif agg_method == "mean":
                resampled = source_data[metric_col].resample(time_agg).mean()
            elif agg_method == "count":
                resampled = source_data[metric_col].resample(time_agg).count()
            elif agg_method == "min":
                resampled = source_data[metric_col].resample(time_agg).min()
            else:  # max
                resampled = source_data[metric_col].resample(time_agg).max()
            
            fig.add_trace(go.Scatter(x=resampled.index, y=resampled.values,
                                   mode='lines+markers', name=source))
        
        fig.update_layout(
            title=f"{metric_col} Time Series ({agg_method.capitalize()}, {time_agg})",
            xaxis_title="Date",
            yaxis_title=metric_col
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Time series decomposition (if enough data points)
        if len(ts_data) > 24:  # Need sufficient data for decomposition
            st.subheader("🔍 Time Series Decomposition")
            
            # Prepare data for decomposition
            decomp_source = st.selectbox("📊 Select Source for Decomposition", ts_data['source'].unique())
            source_ts = ts_data[ts_data['source'] == decomp_source].set_index(date_col)[metric_col]
            
            if agg_method == "sum":
                decomp_data = source_ts.resample(time_agg).sum()
            else:
                decomp_data = source_ts.resample(time_agg).mean()
            
            if len(decomp_data) > 24:
                try:
                    from statsmodels.tsa.seasonal import seasonal_decompose
                    
                    # Handle missing values
                    decomp_data = decomp_data.fillna(method='ffill').fillna(method='bfill')
                    
                    # Perform decomposition
                    decomposition = seasonal_decompose(decomp_data, model='additive', period=min(12, len(decomp_data)//2))
                    
                    # Plot components
                    fig = make_subplots(rows=4, cols=1, 
                                      subplot_titles=['Original', 'Trend', 'Seasonal', 'Residual'])
                    
                    fig.add_trace(go.Scatter(x=decomposition.observed.index, y=decomposition.observed.values,
                                           name='Original'), row=1, col=1)
                    fig.add_trace(go.Scatter(x=decomposition.trend.index, y=decomposition.trend.values,
                                           name='Trend'), row=2, col=1)
                    fig.add_trace(go.Scatter(x=decomposition.seasonal.index, y=decomposition.seasonal.values,
                                           name='Seasonal'), row=3, col=1)
                    fig.add_trace(go.Scatter(x=decomposition.resid.index, y=decomposition.resid.values,
                                           name='Residual'), row=4, col=1)
                    
                    fig.update_layout(height=800, title_text=f"Time Series Decomposition: {metric_col}")
                    st.plotly_chart(fig, use_container_width=True)
                    
                except ImportError:
                    st.warning("📦 Install statsmodels for time series decomposition: pip install statsmodels")
                except Exception as e:
                    st.error(f"❌ Decomposition failed: {str(e)}")
        
        # Time series statistics
        st.subheader("📊 Time Series Statistics")
        ts_stats = []
        for source in ts_data['source'].unique():
            source_data = ts_data[ts_data['source'] == source]
            ts_stats.append({
                'Source': source,
                'Data Points': len(source_data),
                'Date Range': f"{source_data[date_col].min().date()} to {source_data[date_col].max().date()}",
                'Mean': source_data[metric_col].mean(),
                'Trend': 'Increasing' if source_data[metric_col].iloc[-1] > source_data[metric_col].iloc[0] else 'Decreasing',
                'Volatility (Std)': source_data[metric_col].std()
            })
        
        stats_df = pd.DataFrame(ts_stats)
        st.dataframe(stats_df)

# --- DATA TOOLS SECTION ---
elif analysis_type == "🔧 Data Tools":
    st.header("🔧 Data Processing Tools")
    
    tool_type = st.selectbox("🛠️ Select Tool", [
        "🔍 Data Quality Assessment", "🧹 Data Cleaning", "📊 Data Export", "🔄 Data Transformation"
    ])
    
    if tool_type == "🔍 Data Quality Assessment":
        st.subheader("🔍 Data Quality Report")
        
        # Overall data quality metrics
        total_cells = df.shape[0] * df.shape[1]
        missing_cells = df.isnull().sum().sum()
        completeness = ((total_cells - missing_cells) / total_cells) * 100
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); text-align: center; margin-bottom: 1rem;">
                <h3 style="margin: 0; font-size: 0.9rem; font-weight: 500; opacity: 0.9; margin-bottom: 0.5rem; color: white;">📊 Data Completeness</h3>
                <h2 style="margin: 0; font-size: 2rem; font-weight: 700; color: white;">{completeness:.1f}%</h2>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); text-align: center; margin-bottom: 1rem;">
                <h3 style="margin: 0; font-size: 0.9rem; font-weight: 500; opacity: 0.9; margin-bottom: 0.5rem; color: white;">🔢 Total Records</h3>
                <h2 style="margin: 0; font-size: 2rem; font-weight: 700; color: white;">{len(df):,}</h2>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); text-align: center; margin-bottom: 1rem;">
                <h3 style="margin: 0; font-size: 0.9rem; font-weight: 500; opacity: 0.9; margin-bottom: 0.5rem; color: white;">📋 Total Columns</h3>
                <h2 style="margin: 0; font-size: 2rem; font-weight: 700; color: white;">{len(df.columns)}</h2>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); color: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); text-align: center; margin-bottom: 1rem;">
                <h3 style="margin: 0; font-size: 0.9rem; font-weight: 500; opacity: 0.9; margin-bottom: 0.5rem; color: white;">❌ Missing Values</h3>
                <h2 style="margin: 0; font-size: 2rem; font-weight: 700; color: white;">{missing_cells:,}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        # Column-wise quality assessment
        quality_report = []
        for col in df.columns:
            quality_report.append({
                'Column': col,
                'Data Type': str(df[col].dtype),  # Convert to string to avoid Arrow issues
                'Non-Null Count': df[col].count(),
                'Null Count': df[col].isnull().sum(),
                'Null Percentage': (df[col].isnull().sum() / len(df)) * 100,
                'Unique Values': df[col].nunique(),
                'Uniqueness %': (df[col].nunique() / len(df)) * 100
            })
        
        quality_df = pd.DataFrame(quality_report)
        st.dataframe(quality_df)
        
        # Data quality issues
        st.subheader("⚠️ Potential Data Quality Issues")
        issues = []
        
        for col in df.columns:
            null_pct = (df[col].isnull().sum() / len(df)) * 100
            if null_pct > 50:
                issues.append(f"🔴 **{col}**: High missing values ({null_pct:.1f}%)")
            elif null_pct > 20:
                issues.append(f"🟡 **{col}**: Moderate missing values ({null_pct:.1f}%)")
            
            if df[col].dtype == 'object':
                unique_pct = (df[col].nunique() / len(df)) * 100
                if unique_pct > 95:
                    issues.append(f"🔵 **{col}**: Potentially too unique ({unique_pct:.1f}%)")
        
        if issues:
            for issue in issues:
                st.markdown(f"- {issue}")
        else:
            st.success("✅ No major data quality issues detected!")
    
    elif tool_type == "🧹 Data Cleaning":
        st.subheader("🧹 Data Cleaning Operations")
        
        cleaning_options = st.multiselect("🔧 Select Cleaning Operations", [
            "Remove rows with excessive missing values",
            "Fill missing numeric values with mean",
            "Fill missing categorical values with mode",
            "Remove duplicate rows",
            "Standardize text columns"
        ])
        
        if st.button("🚀 Apply Cleaning Operations"):
            cleaned_df = df.copy()
            operations_performed = []
            
            if "Remove rows with excessive missing values" in cleaning_options:
                threshold = st.slider("Missing value threshold (%)", 0, 100, 50)
                before_count = len(cleaned_df)
                cleaned_df = cleaned_df.dropna(thresh=len(cleaned_df.columns) * (1 - threshold/100))
                operations_performed.append(f"Removed {before_count - len(cleaned_df)} rows with >{threshold}% missing values")
            
            if "Fill missing numeric values with mean" in cleaning_options:
                for col in numeric_cols:
                    if cleaned_df[col].isnull().any():
                        mean_val = cleaned_df[col].mean()
                        cleaned_df[col].fillna(mean_val, inplace=True)
                        operations_performed.append(f"Filled missing values in {col} with mean ({mean_val:.2f})")
            
            if "Fill missing categorical values with mode" in cleaning_options:
                for col in categorical_cols:
                    if cleaned_df[col].isnull().any():
                        mode_val = cleaned_df[col].mode().iloc[0] if not cleaned_df[col].mode().empty else "Unknown"
                        cleaned_df[col].fillna(mode_val, inplace=True)
                        operations_performed.append(f"Filled missing values in {col} with mode ({mode_val})")
            
            if "Remove duplicate rows" in cleaning_options:
                before_count = len(cleaned_df)
                cleaned_df = cleaned_df.drop_duplicates()
                operations_performed.append(f"Removed {before_count - len(cleaned_df)} duplicate rows")
            
            if "Standardize text columns" in cleaning_options:
                for col in categorical_cols:
                    if cleaned_df[col].dtype == 'object':
                        cleaned_df[col] = cleaned_df[col].astype(str).str.strip().str.title()
                        operations_performed.append(f"Standardized text in {col}")
            
            # Show results
            st.success("✅ Cleaning operations completed!")
            for op in operations_performed:
                st.markdown(f"- {op}")
            
            # Display cleaned data sample
            st.subheader("🔍 Cleaned Data Sample")
            st.dataframe(cleaned_df.head())
            
            # Store cleaned data in session state for further use
            st.session_state['cleaned_data'] = cleaned_df
    
    elif tool_type == "📊 Data Export":
        st.subheader("📊 Export Data")
        
        export_format = st.selectbox("📁 Select Export Format", ["CSV", "Excel", "JSON"])
        
        # Select data to export
        data_to_export = st.selectbox("📋 Select Data", ["Original Data", "Cleaned Data (if available)"])
        
        if data_to_export == "Cleaned Data (if available)" and 'cleaned_data' in st.session_state:
            export_df = st.session_state['cleaned_data']
        else:
            export_df = df
        
        # Generate download
        if export_format == "CSV":
            csv_data = export_df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name=f"exported_data_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        elif export_format == "JSON":
            json_data = export_df.to_json(orient='records', indent=2)
            st.download_button(
                label="📥 Download JSON",
                data=json_data,
                file_name=f"exported_data_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    elif tool_type == "🔄 Data Transformation":
        st.subheader("🔄 Data Transformation")
        
        transformation_type = st.selectbox("🔧 Select Transformation", [
            "📊 Pivot Table", "📈 Aggregation", "🔄 Normalization", "📋 Feature Engineering"
        ])
        
        if transformation_type == "📊 Pivot Table":
            if len(categorical_cols) > 0 and len(numeric_cols) > 0:
                index_col = st.selectbox("📋 Index Column", categorical_cols + ['source'])
                columns_col = st.selectbox("📊 Columns", [None] + categorical_cols)
                values_col = st.selectbox("📈 Values", numeric_cols)
                agg_func = st.selectbox("🔧 Aggregation Function", ['mean', 'sum', 'count', 'min', 'max'])
                
                if st.button("🚀 Create Pivot Table"):
                    pivot_table = pd.pivot_table(df, index=index_col, columns=columns_col, 
                                               values=values_col, aggfunc=agg_func, fill_value=0)
                    st.dataframe(pivot_table)
        
        elif transformation_type == "📈 Aggregation":
            if len(categorical_cols) > 0 and len(numeric_cols) > 0:
                group_by_cols = st.multiselect("📊 Group By", categorical_cols + ['source'])
                agg_cols = st.multiselect("📈 Aggregate Columns", numeric_cols)
                agg_funcs = st.multiselect("🔧 Aggregation Functions", ['mean', 'sum', 'count', 'min', 'max', 'std'])
                
                if st.button("🚀 Perform Aggregation") and group_by_cols and agg_cols:
                    agg_result = df.groupby(group_by_cols)[agg_cols].agg(agg_funcs)
                    st.dataframe(agg_result)

# --- Enhanced insights at the bottom ---
if not df.empty:
    st.markdown("---")
    st.subheader("🧠 AI-Powered Insights")
    
    # Generate automated insights
    insights = []
    
    # Data volume insights
    if 'source' in df.columns:
        source_counts = df['source'].value_counts()
        largest_source = source_counts.index[0]
        insights.append(f"📊 **{largest_source}** contains the most data with {source_counts.iloc[0]:,} records ({source_counts.iloc[0]/len(df)*100:.1f}% of total)")
    
    # Numeric insights
    if numeric_cols:
        for col in numeric_cols[:3]:  # Top 3 numeric columns
            col_stats = df[col].describe()
            if col_stats['std'] > 0:
                cv = col_stats['std'] / col_stats['mean'] * 100
                if cv > 100:
                    insights.append(f"📈 **{col}** shows high variability (CV: {cv:.1f}%)")
                
                # Growth trends if we have source data
                if 'source' in df.columns:
                    source_means = df.groupby('source')[col].mean().sort_values(ascending=False)
                    if len(source_means) > 1:
                        best_performer = source_means.index[0]
                        worst_performer = source_means.index[-1]
                        improvement_potential = ((source_means.iloc[0] - source_means.iloc[-1]) / source_means.iloc[-1]) * 100
                        insights.append(f"🎯 **{col}**: {best_performer} outperforms {worst_performer} by {improvement_potential:.1f}%")
    
    # Display insights
    if insights:
        for insight in insights[:5]:  # Show top 5 insights
            st.markdown(f"- {insight}")
    
    # Quick action recommendations
    st.subheader("🚀 Recommended Next Steps")
    recommendations = []
    
    if len(numeric_cols) >= 2:
        recommendations.append("🔗 Explore correlations between numeric variables")
    if date_cols:
        recommendations.append("📈 Analyze time series trends and seasonality")
    if len(df['source'].unique()) > 1:
        recommendations.append("🔍 Compare performance across different data sources")
    if len(numeric_cols) >= 3:
        recommendations.append("🎯 Perform clustering analysis to identify patterns")
    
    for rec in recommendations:
        st.markdown(f"- {rec}")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>� Event Analytics Dashboard | Built with Streamlit & Plotly</p>
    <p>💡 Tip: Use the sidebar navigation to explore different analysis types</p>
</div>
""", unsafe_allow_html=True)
