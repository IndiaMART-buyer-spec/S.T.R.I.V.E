import streamlit as st
import os
import logging
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import our application components
from src.ui.components import (
    render_header,
    render_product_input,
    render_upload_section,
    render_processing_status,
    render_triangulation_section,
    render_individual_results,
    render_final_results,
    render_logs_section
)
from src.utils.state import create_initial_state, get_agent_results
from src.agents.workflow import stream_spec_extraction

def initialize_session_state():
    """Initialize session state variables"""
    if "processing_active" not in st.session_state:
        st.session_state.processing_active = False
    
    if "final_results" not in st.session_state:
        st.session_state.final_results = None
    
    if "restart_triangulation" not in st.session_state:
        st.session_state.restart_triangulation = False

def validate_inputs(product_name: str, uploaded_files: dict) -> tuple[bool, str]:
    """Validate user inputs"""
    if not product_name or not product_name.strip():
        return False, "Please enter a product name (Mcat Name)"
    
    if not uploaded_files:
        return False, "Please upload at least one CSV file"
    
    # Validate OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        return False, "OpenAI API key not configured. Please check your environment variables."
    
    return True, ""

def run_extraction_workflow(product_name: str, uploaded_files: dict):
    """Run the extraction workflow with real-time updates"""
    try:
        # Create initial state
        initial_state = create_initial_state(product_name, uploaded_files)
        
        # Create placeholders for real-time updates
        status_placeholder = st.empty()
        progress_placeholder = st.empty()
        logs_placeholder = st.empty()
        
        # Track processing state
        st.session_state.processing_active = True
        current_state = initial_state.copy()
        
        # Stream the workflow
        logger.info(f"Starting workflow for product: {product_name}")
        
        try:
            for chunk in stream_spec_extraction(initial_state):
                # Handle error chunks
                if "error" in chunk:
                    st.error("❌ Workflow failed")
                    st.session_state.processing_active = False
                    return
                
                # Update current state with chunk data
                for node_name, node_state in chunk.items():
                    if isinstance(node_state, dict):
                        current_state.update(node_state)
                
                # Update UI with current state
                with status_placeholder.container():
                    render_processing_status(current_state)
                
                with progress_placeholder.container():
                    progress = current_state.get("progress_percentage", 0)
                    st.progress(progress / 100)
                    st.markdown(f"**{progress}% Complete**")
                
                with logs_placeholder.container():
                    logs = current_state.get("logs", [])
                    if logs:
                        with st.expander("📋 Real-time Logs", expanded=True):
                            for log in logs[-5:]:  # Show last 5 logs
                                st.text(log)
                
                # Check if completed
                if current_state.get("current_step") == "completed":
                    st.session_state.processing_active = False
                    st.session_state.final_results = current_state
                    st.success("✅ Processing completed successfully!")
                    st.rerun()
                    break
                
                # Small delay to prevent UI flooding
                time.sleep(0.1)
                
        except GeneratorExit:
            # Handle graceful generator closure - this is normal in Streamlit
            logger.info("Workflow streaming stopped - generator closed by Streamlit")
            
            # Check if we have final results in current_state
            if current_state.get("current_step") == "completed":
                st.session_state.processing_active = False
                st.session_state.final_results = current_state
                st.success("✅ Processing completed successfully!")
                st.rerun()
            else:
                # Process was interrupted
                st.warning("⚠️ Processing was interrupted. You may need to restart.")
                st.session_state.processing_active = False
            return
            
        except StopIteration:
            # Normal completion
            logger.info("Workflow streaming completed normally")
            if current_state.get("current_step") == "completed":
                st.session_state.processing_active = False
                st.session_state.final_results = current_state
                st.success("✅ Processing completed successfully!")
                st.rerun()
            return
        
    except Exception as e:
        logger.error(f"Workflow execution failed: {str(e)}")
        st.error(f"❌ Workflow failed: {str(e)}")
        st.session_state.processing_active = False

def run_extraction_workflow_blocking(product_name: str, uploaded_files: dict):
    """Run the extraction workflow without streaming - blocking approach"""
    try:
        # Create initial state
        initial_state = create_initial_state(product_name, uploaded_files)
        
        # Show progress indicator
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("🚀 Starting extraction workflow...")
        progress_bar.progress(5)
        
        # Run workflow without streaming
        logger.info(f"Starting blocking workflow for product: {product_name}")
        
        from src.agents.workflow import run_spec_extraction
        final_state = run_spec_extraction(initial_state)
        
        # Update progress to complete
        progress_bar.progress(100)
        status_text.text("✅ Processing completed!")
        
        # Store results
        st.session_state.processing_active = False
        st.session_state.final_results = final_state
        
        st.success("✅ Processing completed successfully!")
        st.rerun()
        
    except Exception as e:
        logger.error(f"Blocking workflow execution failed: {str(e)}")
        st.error(f"❌ Workflow failed: {str(e)}")
        st.session_state.processing_active = False

def main():
    """Main application function"""
    
    # Initialize session state
    initialize_session_state()
    
    # Render header
    render_header()
    
    # Main content area
    if st.session_state.processing_active:
        # Show processing view
        st.markdown("## 🔄 Processing in Progress")
        st.info("The extraction workflow is running. Please wait for completion...")
        
        # The processing status will be updated by run_extraction_workflow
        # We just need placeholders here
        st.empty()  # For status
        st.empty()  # For progress
        st.empty()  # For logs
        
    elif st.session_state.final_results:
        # Show results view
        render_results_view()
        
    else:
        # Show input/upload view
        render_input_view()

def render_input_view():
    """Render the input and upload view"""
    
    # Product name input
    product_name = render_product_input()
    
    # File upload section
    uploaded_files = render_upload_section()
    
    # Triangulation section
    if uploaded_files:
        start_processing, workflow_mode = render_triangulation_section()
        
        if start_processing:
            # Validate inputs
            is_valid, error_msg = validate_inputs(product_name, uploaded_files)
            
            if not is_valid:
                st.error(f"❌ {error_msg}")
                return
            
            # Start processing with blocking mode
            st.info("🚀 Starting extraction workflow...")
            run_extraction_workflow_blocking(product_name, uploaded_files)

def render_results_view():
    """Render the results view"""
    
    final_results = st.session_state.final_results
    
    # Header with restart option
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("## 🎯 Analysis Results")
        product_name = final_results.get("product_name", "Unknown Product")
        st.markdown(f"**Product:** {product_name}")
    
    with col2:
        if st.button("🔄 Start New Analysis", type="primary"):
            # Clear session state and restart
            st.session_state.processing_active = False
            st.session_state.final_results = None
            st.session_state.restart_triangulation = False
            
            # Clear uploaded files
            keys_to_remove = [key for key in st.session_state.keys() if key.startswith("uploaded_")]
            for key in keys_to_remove:
                del st.session_state[key]
            
            st.rerun()
    
    # Render individual results using helper function
    agent_results = get_agent_results(final_results)
    render_individual_results(agent_results)
    
    # Render final triangulated results
    triangulated_result = final_results.get("triangulated_result", "")
    triangulated_table = final_results.get("triangulated_table", [])
    render_final_results(triangulated_result, triangulated_table)
    
    # Render logs
    logs = final_results.get("logs", [])
    render_logs_section(logs)
    
    # Handle restart triangulation
    if st.session_state.restart_triangulation:
        st.session_state.restart_triangulation = False
        
        # Get uploaded files from session state
        uploaded_files = {}
        for key in st.session_state.keys():
            if key.startswith("uploaded_"):
                source_key = key.replace("uploaded_", "")
                file_data = st.session_state[key]
                uploaded_files[source_key] = file_data["content"]
        
        if uploaded_files:
            product_name = final_results.get("product_name", "")
            st.info("🔄 Restarting triangulation...")
            run_extraction_workflow_blocking(product_name, uploaded_files)

if __name__ == "__main__":
    # Check for required environment variables
    if not os.getenv("OPENAI_API_KEY"):
        st.error("""
        ❌ **OpenAI API Key Required**
        
        Please set your OpenAI API key in the environment:
        1. Copy `env_example.txt` to `.env`
        2. Add your OpenAI API key to the `.env` file
        3. Restart the application
        """)
        st.stop()
    
    try:
        main()
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        st.error(f"❌ Application error: {str(e)}")
        
        # Show debug info in development
        if os.getenv("DEBUG", "").lower() == "true":
            st.exception(e) 
