from typing import Dict, List, Any, Optional
from typing_extensions import TypedDict, Annotated
import json
import operator

class SpecExtractionState(TypedDict):
    """State for the Spec Extraction LangGraph workflow"""
    
    # User inputs - these should not be updated after initialization
    product_name: str
    uploaded_files: Dict[str, str]  # {source_name: file_content}
    
    # Meta-ensemble tracking
    meta_ensemble_enabled: bool
    current_run: int  # 1, 2, or 3
    total_runs: int   # Always 3 for meta-ensemble
    run_results: List[Dict[str, Any]]  # Store results from each run
    
    # Processing state - each agent updates its own unique key
    search_keywords_status: str
    whatsapp_specs_status: str
    pns_calls_status: str
    rejection_comments_status: str
    lms_chats_status: str
    
    current_step: str
    
    # Agent outputs - each agent has its own unique key
    search_keywords_result: Dict[str, Any]
    whatsapp_specs_result: Dict[str, Any]
    pns_calls_result: Dict[str, Any]
    rejection_comments_result: Dict[str, Any]
    lms_chats_result: Dict[str, Any]
    
    # Final triangulation
    triangulated_result: str
    triangulated_table: List[Dict[str, Any]]  # For CSV download
    
    # Meta-ensemble final result
    final_ensemble_result: str
    final_ensemble_table: List[Dict[str, Any]]
    
    # Progress & logging - using annotations for concurrent updates
    progress_percentage: int
    logs: Annotated[List[str], operator.add]  # Allow concurrent log additions
    
    # Errors - each agent has its own unique error key
    search_keywords_error: str
    whatsapp_specs_error: str
    pns_calls_error: str
    rejection_comments_error: str
    lms_chats_error: str

# Dataset type mapping
DATASET_TYPE_MAPPING = {
    "search_keywords": "internal-search",      # Uses pageviews
    "whatsapp_specs": "buyer-specs",          # Uses occurrences  
    "pns_calls": "call-transcripts",          # Uses occurrences
    "rejection_comments": "rejection-reasons", # Uses occurrences
    "lms_chats": "chat-data"                  # Uses occurrences
}

# Column mappings for CSV files
COLUMN_MAPPINGS = {
    "search_keywords": {
        "data_column": "decoded_keyword",
        "frequency_column": "pageviews"
    },
    "whatsapp_specs": {
        "data_column": "fk_im_spec_options_desc",
         "frequency_column": "Frequency"
    },
    "pns_calls": {
        "data_column": "transcribed_text"
    },
    "rejection_comments": {
        "data_column": "eto_ofr_reject_comment",
        "frequency_column": "Frequency"
    },
    "lms_chats": {
        "data_column": "message_text_json",
        "frequency_column": "Frequency"
    }
}

# Source names mapping
SOURCE_NAMES = {
    "search_keywords": "Internal Search Keywords",
    "whatsapp_specs": "WhatsApp Conversations", 
    "pns_calls": "PNS Call Transcript",
    "rejection_comments": "BLNI Comments/QRF Data",
    "lms_chats": "LMS Chat Logs"
}

def create_initial_state(product_name: str, files: Dict[str, str]) -> SpecExtractionState:
    """Create initial state for the workflow"""
    return SpecExtractionState(
        product_name=product_name,
        uploaded_files=files,
        meta_ensemble_enabled=True,  # Always enable meta-ensemble
        current_run=0,
        total_runs=3,
        run_results=[],
        search_keywords_status="idle" if "search_keywords" in files else "not_uploaded",
        whatsapp_specs_status="idle" if "whatsapp_specs" in files else "not_uploaded",
        pns_calls_status="idle" if "pns_calls" in files else "not_uploaded",
        rejection_comments_status="idle" if "rejection_comments" in files else "not_uploaded",
        lms_chats_status="idle" if "lms_chats" in files else "not_uploaded",
        current_step="initialization",
        search_keywords_result={},
        whatsapp_specs_result={},
        pns_calls_result={},
        rejection_comments_result={},
        lms_chats_result={},
        triangulated_result="",
        triangulated_table=[],
        final_ensemble_result="",
        final_ensemble_table=[],
        progress_percentage=0,
        logs=[f"Initialized meta-ensemble workflow for product: {product_name}"],
        search_keywords_error="",
        whatsapp_specs_error="",
        pns_calls_error="",
        rejection_comments_error="",
        lms_chats_error=""
    )

def get_agents_status(state: SpecExtractionState) -> Dict[str, str]:
    """Get agents status from individual status fields"""
    return {
        "search_keywords": state["search_keywords_status"],
        "whatsapp_specs": state["whatsapp_specs_status"],
        "pns_calls": state["pns_calls_status"],
        "rejection_comments": state["rejection_comments_status"],
        "lms_chats": state["lms_chats_status"]
    }

def get_agent_results(state: SpecExtractionState) -> Dict[str, Dict[str, Any]]:
    """Get agent results from individual result fields"""
    return {
        "search_keywords": state["search_keywords_result"],
        "whatsapp_specs": state["whatsapp_specs_result"],
        "pns_calls": state["pns_calls_result"],
        "rejection_comments": state["rejection_comments_result"],
        "lms_chats": state["lms_chats_result"]
    }

def get_errors(state: SpecExtractionState) -> Dict[str, str]:
    """Get errors from individual error fields"""
    return {
        "search_keywords": state["search_keywords_error"],
        "whatsapp_specs": state["whatsapp_specs_error"],
        "pns_calls": state["pns_calls_error"],
        "rejection_comments": state["rejection_comments_error"],
        "lms_chats": state["lms_chats_error"]
    } 