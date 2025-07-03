import streamlit as st
import pandas as pd
from typing import Dict, Any, List, Optional
import io
import base64
from ..utils.state import SOURCE_NAMES, DATASET_TYPE_MAPPING, get_agents_status, get_agent_results

def render_header():
    """Render the application header"""
    st.set_page_config(
        page_title="DataFlow Analytics - Buyer Spec Extractor", 
        page_icon="📊",
        layout="wide"
    )
    
    # Header with blue background
    st.markdown("""
        <div style="background-color: #4A90E2; padding: 1rem; border-radius: 10px; margin-bottom: 2rem;">
            <h1 style="color: white; margin: 0; font-size: 1.8rem;">
                📊 DataFlow Analytics
            </h1>
            <p style="color: white; margin: 0; opacity: 0.9; font-size: 0.9rem;">
                IndiaMart Intelligent Spec Platform
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Dashboard title
    st.markdown("""
        <div style="background-color: #f8f9fa; padding: 1.5rem; border-radius: 10px; border-left: 4px solid #4A90E2; margin-bottom: 2rem;">
            <h2 style="color: #2c3e50; margin: 0; font-size: 1.5rem;">
                🔍 Buyer Spec Extractor Dashboard
            </h2>
            <p style="color: #7f8c8d; margin: 0.5rem 0 0 0; font-size: 0.9rem;">
                Extract and triangulate buyer specifications from multiple datasources
            </p>
        </div>
    """, unsafe_allow_html=True)

def render_product_input() -> str:
    """Render product name input section"""
    st.markdown("### 📝 Analysis Configuration")
    
    with st.container():
        col1, col2 = st.columns([2, 1])
        
        with col1:
            product_name = st.text_input(
                "**Mcat Name** *",
                placeholder="e.g., Kirloskar Generator, Hydraulic Gear Pump, 63 KVA Transformer",
                help="Enter the product category name for analysis"
            )
        
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if product_name:
                st.success("✅ Product specified")
            else:
                st.info("ℹ️ Enter product name")
    
    return product_name

def render_upload_section() -> Dict[str, str]:
    """Render the file upload section with professional layout"""
    st.markdown("### 📂 Dataset Upload & Analysis")
    st.markdown("*Upload your CSV datasets to extract and analyze buyer specifications*")
    
    uploaded_files = {}
    
    # Create professional grid layout
    row1_col1, row1_col2 = st.columns(2, gap="large")
    row2_col1, row2_col2 = st.columns(2, gap="large")
    row3_col1, row3_col2, row3_col3 = st.columns([1, 1, 1], gap="large")
    
    # Upload areas configuration with cleaner titles
    upload_configs = [
        {
            "key": "search_keywords",
            "title": "🔍 Internal Search Keywords",
            "desc": "CSV with internal search queries and pageview metrics",
            "metric": "Pageviews",
            "container": row1_col1
        },
        {
            "key": "lms_chats", 
            "title": "💬 LMS Chat Logs",
            "desc": "CSV with learning management system conversations",
            "metric": "Occurrences",
            "container": row1_col2
        },
        {
            "key": "rejection_comments",
            "title": "❌ BLNI Comments/QRF", 
            "desc": "CSV with business logic and quality feedback",
            "metric": "Occurrences",
            "container": row2_col1
        },
        {
            "key": "pns_calls",
            "title": "📞 PNS Call Transcripts",
            "desc": "CSV with phone call transcription data", 
            "metric": "Occurrences",
            "container": row2_col2
        },
        {
            "key": "whatsapp_specs",
            "title": "📱 WhatsApp Conversations",
            "desc": "CSV with WhatsApp chat conversation data",
            "metric": "Occurrences", 
            "container": row3_col2
        }
    ]
    
    # Render each upload area
    for config in upload_configs:
        with config["container"]:
            uploaded_file = render_single_upload_area(
                config["key"],
                config["title"], 
                config["desc"],
                config["metric"]
            )
            
            if uploaded_file:
                uploaded_files[config["key"]] = uploaded_file
    
    # Add spacing
    st.markdown("<br>", unsafe_allow_html=True)
    
    return uploaded_files

def render_single_upload_area(source_key: str, title: str, description: str, metric_type: str) -> Optional[str]:
    """Render a single upload area with proper container styling"""
    
    # Add container-specific CSS
    container_id = f"upload-{source_key}"
    
    st.markdown(
        f"""
        <style>
        div[data-testid="stVerticalBlock"] > div[data-testid="stContainer"] {{
            border: 2px dashed #cbd5e0;
            border-radius: 12px;
            padding: 1.5rem;
            background: linear-gradient(135deg, #f8fafc 0%, #edf2f7 100%);
            margin-bottom: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            min-height: 180px;
        }}
        
        .uploaded-container {{
            border: 2px solid #48bb78 !important;
            background: linear-gradient(135deg, #f0fff4 0%, #e6fffa 100%) !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )
    
    # Check if file is already uploaded
    if f"uploaded_{source_key}" in st.session_state:
        return render_uploaded_file_card_clean(source_key, title, description, metric_type)
    else:
        return render_upload_card_clean(source_key, title, description, metric_type)

def render_upload_card_clean(source_key: str, title: str, description: str, metric_type: str) -> Optional[str]:
    """Render clean upload card using native Streamlit containers"""
    
    with st.container():
        # Title and description
        st.markdown(f"**{title}**")
        st.caption(description)
        
        # File uploader
        uploaded_file = st.file_uploader(
            f"Choose CSV file",
            type=['csv'],
            key=f"uploader_{source_key}",
            label_visibility="collapsed"
        )
        
        # Info section
        col1, col2 = st.columns(2)
        with col1:
            st.caption(f"📊 {metric_type}")
        with col2:
            st.caption("📁 .csv • Max 10MB")
        
        if uploaded_file:
            # Validate and store file with robust encoding handling
            raw_content = uploaded_file.read()
            
            # Try multiple encodings to handle different file formats
            encodings_to_try = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252', 'iso-8859-1']
            file_content = None
            
            for encoding in encodings_to_try:
                try:
                    file_content = raw_content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            # If all encodings fail, use error handling
            if file_content is None:
                try:
                    file_content = raw_content.decode('utf-8', errors='replace')
                    st.warning(f"⚠️ File encoding detected as non-UTF-8. Some characters may be replaced.")
                except Exception as e:
                    st.error(f"❌ Failed to read file: {str(e)}")
                    return None
            
            # Validate file is not empty
            if not file_content.strip():
                st.error(f"❌ Uploaded file appears to be empty")
                return None
                
            # Basic CSV validation
            if not any(delimiter in file_content[:1000] for delimiter in [',', ';', '\t']):
                st.warning(f"⚠️ File doesn't appear to be a valid CSV format")
            
            # Store in session state
            st.session_state[f"uploaded_{source_key}"] = {
                "content": file_content,
                "name": uploaded_file.name,
                "size": len(file_content),
                "metric_type": metric_type
            }
            
            st.rerun()
    
    return None

def render_uploaded_file_card_clean(source_key: str, title: str, description: str, metric_type: str) -> str:
    """Render clean uploaded file card"""
    
    file_data = st.session_state[f"uploaded_{source_key}"]
    
    # Add success styling to container
    st.markdown(
        f"""
        <style>
        .success-container-{source_key} {{
            border: 2px solid #48bb78 !important;
            border-radius: 12px !important;
            background: linear-gradient(135deg, #f0fff4 0%, #e6fffa 100%) !important;
            padding: 1.5rem !important;
            margin-bottom: 1rem !important;
            box-shadow: 0 2px 8px rgba(72, 187, 120, 0.15) !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )
    
    with st.container():
        # Success indicator
        st.markdown(f"**✅ {title}**")
        st.caption(f"📁 {file_data['name']}")
        st.caption(f"📊 {file_data['size'] / 1024:.1f} KB • {metric_type}")
        
        # Remove button
        if st.button(f"🗑️ Remove File", key=f"remove_{source_key}", type="secondary", use_container_width=True):
            del st.session_state[f"uploaded_{source_key}"]
            st.rerun()
    
    return file_data["content"]

def render_processing_status(state: Dict[str, Any]):
    """Render processing status sidebar and progress"""
    
    # Sidebar processing status
    with st.sidebar:
        st.markdown("### 🔄 Processing Dataset")
        
        current_step = state.get("current_step", "idle")
        progress = state.get("progress_percentage", 0)
        
        # Progress bar
        st.progress(progress / 100)
        st.markdown(f"**{progress}% Complete**")
        
        # Current activity
        if current_step.startswith("processing"):
            st.info(f"📊 {current_step}")
        elif current_step == "triangulation":
            st.info("🔗 Running triangulation...")
        elif current_step == "completed":
            st.success("✅ Processing complete!")
        elif "failed" in current_step:
            st.error("❌ Processing failed")
        
        # Individual agent status using helper function
        st.markdown("#### Agent Status")
        
        agents_status = get_agents_status(state)
        for source_key, status in agents_status.items():
            # Only show status for uploaded files
            if source_key in state.get("uploaded_files", {}):
                source_name = SOURCE_NAMES.get(source_key, source_key)
                
                if status == "processing":
                    st.markdown(f"⏳ {source_name}: Processing...")
                elif status == "completed":
                    st.markdown(f"✅ {source_name}: Completed")
                elif status == "failed":
                    st.markdown(f"❌ {source_name}: Failed")
                else:
                    st.markdown(f"⚪ {source_name}: Waiting")

def render_triangulation_section() -> tuple[bool, str]:
    """Render the triangulation section"""
    st.markdown("### 🔗 Cross-Dataset Triangulation")
    st.markdown("*Combine insights from multiple datasets to identify weighted ISQ priorities*")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Status indicators
        uploaded_count = len([k for k in st.session_state.keys() if k.startswith("uploaded_")])
        if uploaded_count > 0:
            st.info(f"📊 {uploaded_count} datasets uploaded • ✅ Analysis completed • Ready for triangulation")
        else:
            st.warning("⚠️ Upload at least one dataset to proceed")
    
    with col2:
        start_triangulation = st.button(
            "🚀 Start Triangulation",
            type="primary",
            disabled=uploaded_count == 0,
            use_container_width=True
        )
    
    # Return blocking mode by default
    return start_triangulation, "blocking"

def render_individual_results(agent_results: Dict[str, Dict[str, Any]]):
    """Render individual dataset analysis results"""
    if not agent_results:
        return
        
    st.markdown("## 📊 Individual Dataset Analysis")
    
    for source_key, result in agent_results.items():
        if result.get("status") != "completed":
            continue
            
        source_name = SOURCE_NAMES.get(source_key, source_key)
        
        # Expandable card for each dataset
        with st.expander(f"📋 {source_name} Analysis", expanded=False):
            
            # Summary stats
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("📄 Total Rows", result.get("raw_data_count", 0))
            with col2:
                # Count ISQs from result
                specs = result.get("extracted_specs", "")
                isq_count = len([line for line in specs.split('\n') if line.strip() and '|' in line]) - 1
                st.metric("🎯 Top ISQs", max(0, isq_count))
            with col3:
                st.metric("⏱️ Processing Time", f"{result.get('processing_time', 0)}s")
            
            # Excel download button
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button(f"📥 Excel", key=f"download_{source_key}"):
                    download_individual_result(source_key, result)
            
            # Display results table
            specs_text = result.get("extracted_specs", "")
            if specs_text:
                display_specs_table(specs_text)

def render_final_results(triangulated_result: str, triangulated_table: List[Dict[str, Any]]):
    """Render final triangulated results (handles both single and meta-ensemble results)"""
    
    # Check if we have meta-ensemble results
    final_results = st.session_state.get("final_results", {})
    has_meta_ensemble = final_results.get("final_ensemble_result") or final_results.get("run_results")
    
    if has_meta_ensemble:
        render_meta_ensemble_results(final_results)
    elif triangulated_result:
        render_single_triangulation_results(triangulated_result, triangulated_table)

def render_meta_ensemble_results(final_results: Dict[str, Any]):
    """Render meta-ensemble results with run breakdown"""
    
    st.markdown("## 🔗 Meta-Ensemble Triangulation Results")
    st.markdown("*High-accuracy results from 3 independent runs with final consensus triangulation*")
    
    # Header with stats and export
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        run_results = final_results.get("run_results", [])
        successful_runs = len([r for r in run_results if r.get("triangulated_result") != "Run failed"])
        
        st.info(f"✅ Meta-ensemble completed • {successful_runs}/3 successful runs • Final consensus achieved")
    
    with col2:
        if st.button("🔄 Re-run Meta-Ensemble", type="secondary"):
            st.session_state["restart_triangulation"] = True
            st.rerun()
    
    with col3:
        if st.button("📥 Export All Results", type="primary"):
            download_meta_ensemble_results(final_results)
    
    # Display final ensemble result
    final_ensemble_result = final_results.get("final_ensemble_result", "")
    final_ensemble_table = final_results.get("final_ensemble_table", [])
    
    if final_ensemble_result:
        st.markdown("### 🎯 Final Consensus Results")
        st.markdown("*Highest confidence specifications validated across multiple runs*")
        
        if final_ensemble_table:
            df = pd.DataFrame(final_ensemble_table)
            
            # Enhanced styling for meta-ensemble results
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Rank": st.column_config.NumberColumn("Rank", width="small"),
                    "Specification": st.column_config.TextColumn("Specification", width="medium"),
                    "Top Options": st.column_config.TextColumn("Top Options (Consensus)", width="large"),
                    "Why it matters": st.column_config.TextColumn("Why it matters", width="large"),
                    "Impacts Pricing?": st.column_config.TextColumn("Impacts Pricing?", width="small")
                }
            )
        else:
            st.markdown(final_ensemble_result)
    
    # Show individual run results in expandable sections
    run_results = final_results.get("run_results", [])
    if run_results:
        st.markdown("### 📊 Individual Run Results")
        
        for run_data in run_results:
            run_num = run_data.get("run_number", 0)
            triangulated_result = run_data.get("triangulated_result", "")
            
            if triangulated_result == "Run failed":
                with st.expander(f"🔴 Run {run_num} - Failed", expanded=False):
                    st.error("This run failed to complete successfully")
            else:
                with st.expander(f"✅ Run {run_num} Results", expanded=False):
                    # Show triangulated result first
                    st.markdown("#### 🎯 Triangulated Result for this Run")
                    triangulated_table = run_data.get("triangulated_table", [])
                    
                    if triangulated_table:
                        df = pd.DataFrame(triangulated_table)
                        st.dataframe(df, use_container_width=True, hide_index=True)
                    else:
                        st.markdown(triangulated_result)
                    
                    # Show individual agent outputs for this run
                    st.markdown("#### 📋 Individual Agent Outputs")
                    
                    # Get agent results from this run's stored data
                    agent_results = run_data.get("agent_results", {})
                    
                    if agent_results:
                        # Create tabs for each agent
                        agent_tabs = []
                        agent_data = []
                        
                        for source_key, result in agent_results.items():
                            if result.get("status") == "completed":
                                source_name = SOURCE_NAMES.get(source_key, source_key)
                                agent_tabs.append(f"📊 {source_name}")
                                agent_data.append((source_key, result))
                        
                        if agent_tabs:
                            tabs = st.tabs(agent_tabs)
                            
                            for tab, (source_key, result) in zip(tabs, agent_data):
                                with tab:
                                    # Agent summary stats
                                    col1, col2, col3 = st.columns(3)
                                    
                                    with col1:
                                        st.metric("📄 Total Rows", result.get("raw_data_count", 0))
                                    with col2:
                                        # Count specifications from result
                                        specs = result.get("extracted_specs", "")
                                        spec_count = len([line for line in specs.split('\n') if line.strip() and '|' in line and 'Rank' not in line]) if specs else 0
                                        st.metric("🎯 Specifications", max(0, spec_count))
                                    with col3:
                                        st.metric("⏱️ Processing Time", f"{result.get('processing_time', 0):.1f}s")
                                    
                                    # Display agent's extracted specifications
                                    specs_text = result.get("extracted_specs", "")
                                    if specs_text:
                                        display_specs_table(specs_text)
                                    else:
                                        st.info("No specifications extracted for this agent in this run")
                    else:
                        st.info("No individual agent results available for this run")

def render_single_triangulation_results(triangulated_result: str, triangulated_table: List[Dict[str, Any]]):
    """Render single triangulation results (fallback for non-meta-ensemble)"""
    
    st.markdown("## 🔗 Cross-Dataset Triangulation")
    st.markdown("*Combine insights from multiple datasets to identify weighted ISQ priorities*")
    
    # Header with re-run and export buttons
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        # Get agent results from the final results state
        final_results = st.session_state.get("final_results", {})
        agent_results = get_agent_results(final_results)
        
        # Calculate totals from completed agents
        completed_results = {k: v for k, v in agent_results.items() if v.get("status") == "completed"}
        total_rows = sum([int(result.get("raw_data_count", 0)) for result in completed_results.values()])
        datasets_count = len(completed_results)
        
        st.info(f"✅ Analysis completed • {total_rows:,} total rows from {datasets_count} datasets")
    
    with col2:
        if st.button("🔄 Re-run Triangulation", type="secondary"):
            st.session_state["restart_triangulation"] = True
            st.rerun()
    
    with col3:
        if st.button("📥 Export Full Results", type="primary"):
            download_final_results(triangulated_result, triangulated_table)
    
    st.markdown("### 🎯 Triangulated Results")
    
    # Display final results table
    if triangulated_table:
        df = pd.DataFrame(triangulated_table)
        
        # Custom styling for the table to match competitor format
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Rank": st.column_config.NumberColumn("Rank", width="small"),
                "Specification": st.column_config.TextColumn("Specification", width="medium"),
                "Top Options": st.column_config.TextColumn("Top Options", width="large"),
                "Why it matters": st.column_config.TextColumn("Why it matters", width="large"),
                "Impacts Pricing?": st.column_config.TextColumn("Impacts Pricing?", width="small")
            }
        )
    else:
        # Fallback: display raw text
        st.markdown(triangulated_result)

def display_specs_table(specs_text: str):
    """Display specifications in a nice table format"""
    try:
        lines = specs_text.strip().split('\n')
        if len(lines) < 2:
            st.text(specs_text)
            return
        
        # Parse table data
        data = []
        headers = []
        
        for i, line in enumerate(lines):
            if '|' in line:
                parts = [part.strip() for part in line.split('|')]
                if i == 0 or 'Rank' in line:  # Header row
                    headers = parts
                else:
                    if len(parts) >= len(headers):
                        data.append(parts[:len(headers)])
        
        if data and headers:
            df = pd.DataFrame(data, columns=headers)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.text(specs_text)
            
    except Exception:
        st.text(specs_text)

def download_meta_ensemble_results(final_results: Dict[str, Any]):
    """Generate download for meta-ensemble results with all runs and individual agent outputs"""
    try:
        # Create Excel file with multiple sheets
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            
            # Sheet 1: Final Consensus Results
            final_ensemble_table = final_results.get("final_ensemble_table", [])
            if final_ensemble_table:
                df_final = pd.DataFrame(final_ensemble_table)
                df_final.to_excel(writer, sheet_name='Final_Consensus', index=False)
            
            # Sheets for Individual Run Results and Agent Outputs
            run_results = final_results.get("run_results", [])
            for run_data in run_results:
                run_num = run_data.get("run_number", 0)
                
                # Sheet: Run triangulated results
                triangulated_table = run_data.get("triangulated_table", [])
                if triangulated_table:
                    df_run = pd.DataFrame(triangulated_table)
                    df_run.to_excel(writer, sheet_name=f'Run_{run_num}_Triangulated', index=False)
                else:
                    # Create a simple sheet with the text result
                    df_text = pd.DataFrame([{"Result": run_data.get("triangulated_result", "No data")}])
                    df_text.to_excel(writer, sheet_name=f'Run_{run_num}_Triangulated', index=False)
                
                # Sheets: Individual agent results for this run
                agent_results = run_data.get("agent_results", {})
                for source_key, result in agent_results.items():
                    if result.get("status") == "completed":
                        source_name = SOURCE_NAMES.get(source_key, source_key)
                        specs_text = result.get("extracted_specs", "")
                        
                        if specs_text:
                            # Parse the specs table into DataFrame
                            try:
                                lines = specs_text.strip().split('\n')
                                data = []
                                headers = []
                                
                                for i, line in enumerate(lines):
                                    if '|' in line:
                                        parts = [part.strip() for part in line.split('|')]
                                        if i == 0 or 'Rank' in line:  # Header row
                                            headers = [h for h in parts if h]  # Remove empty parts
                                        else:
                                            if len(parts) >= len(headers) and any(parts):
                                                clean_parts = [p for p in parts if p][:len(headers)]
                                                if len(clean_parts) == len(headers):
                                                    data.append(clean_parts)
                                
                                if data and headers:
                                    df_agent = pd.DataFrame(data, columns=headers)
                                    # Add metadata
                                    metadata = pd.DataFrame([
                                        ["Total Rows", result.get("raw_data_count", 0)],
                                        ["Processing Time (s)", result.get("processing_time", 0)],
                                        ["Status", result.get("status", "unknown")]
                                    ], columns=["Metric", "Value"])
                                    
                                    # Write to separate sheets
                                    sheet_name = f'R{run_num}_{source_key[:10]}'  # Truncate for Excel limits
                                    df_agent.to_excel(writer, sheet_name=f'{sheet_name}_Data', index=False)
                                    metadata.to_excel(writer, sheet_name=f'{sheet_name}_Meta', index=False)
                                else:
                                    # Fallback: raw text
                                    df_raw = pd.DataFrame([{"Raw_Output": specs_text}])
                                    sheet_name = f'R{run_num}_{source_key[:10]}'
                                    df_raw.to_excel(writer, sheet_name=f'{sheet_name}_Raw', index=False)
                                    
                            except Exception:
                                # Fallback: raw text
                                df_raw = pd.DataFrame([{"Raw_Output": specs_text}])
                                sheet_name = f'R{run_num}_{source_key[:10]}'
                                df_raw.to_excel(writer, sheet_name=f'{sheet_name}_Raw', index=False)
            
            # Final Sheet: Meta-Ensemble Summary
            summary_data = {
                "Metric": ["Total Runs", "Successful Runs", "Final Consensus Specs", "Total Datasets Processed"],
                "Value": [
                    len(run_results),
                    len([r for r in run_results if r.get("triangulated_result") != "Run failed"]),
                    len(final_ensemble_table),
                    len([k for k in ["search_keywords", "whatsapp_specs", "pns_calls", "rejection_comments", "lms_chats"] 
                         if final_results.get("uploaded_files", {}).get(k)])
                ]
            }
            df_summary = pd.DataFrame(summary_data)
            df_summary.to_excel(writer, sheet_name='Meta_Summary', index=False)
        
        st.download_button(
            label="📥 Download Complete Meta-Ensemble Results (Excel)",
            data=output.getvalue(),
            file_name="complete_meta_ensemble_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    except Exception as e:
        st.error(f"Error preparing meta-ensemble download: {str(e)}")

def download_individual_result(source_key: str, result: Dict[str, Any]):
    """Generate download for individual result"""
    try:
        specs_text = result.get("extracted_specs", "")
        
        # Convert to CSV format
        output = io.StringIO()
        output.write(specs_text)
        csv_data = output.getvalue()
        
        # Create download
        st.download_button(
            label=f"Download {SOURCE_NAMES.get(source_key, source_key)} Results",
            data=csv_data,
            file_name=f"{source_key}_results.csv",
            mime="text/csv",
            key=f"download_btn_{source_key}"
        )
        
    except Exception as e:
        st.error(f"Error preparing download: {str(e)}")

def download_final_results(triangulated_result: str, triangulated_table: List[Dict[str, Any]]):
    """Generate download for final results"""
    try:
        if triangulated_table:
            df = pd.DataFrame(triangulated_table)
            
            # Create Excel file
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Triangulated_Results', index=False)
            
            st.download_button(
                label="📥 Download Triangulated Results (Excel)",
                data=output.getvalue(),
                file_name="triangulated_spec_results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            # Fallback: text download
            st.download_button(
                label="📥 Download Results (Text)",
                data=triangulated_result,
                file_name="triangulated_results.txt", 
                mime="text/plain"
            )
            
    except Exception as e:
        st.error(f"Error preparing download: {str(e)}")

def render_logs_section(logs: List[str]):
    """Render logs section"""
    if logs:
        with st.expander("📋 Processing Logs", expanded=False):
            for log in logs[-10:]:  # Show last 10 logs
                st.text(log) 