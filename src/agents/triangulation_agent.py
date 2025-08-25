import os
import logging
import time
import json
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from ..utils.state import SpecExtractionState, get_agents_status, get_agent_results

logger = logging.getLogger(__name__)

class MetaEnsembleAgent:
    """Agent for performing final ensemble triangulation of multiple runs"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            temperature=0.1
        )
    
    def ensemble_triangulate(self, state: SpecExtractionState) -> SpecExtractionState:
        """Perform final ensemble triangulation of 3 run results"""
        start_time = time.time()
        
        try:
            logger.info("Starting meta-ensemble triangulation")
            
            run_results = state["run_results"]
            if len(run_results) != 3:
                raise ValueError(f"Expected 3 run results, got {len(run_results)}")
            
            # Build ensemble prompt
            prompt = self._build_ensemble_prompt(
                product_name=state["product_name"],
                run_results=run_results
            )
            
            logger.info("Sending meta-ensemble triangulation request")
            
            # Call LLM for final ensemble
            response = self.llm.invoke([HumanMessage(content=prompt)])
            final_result = response.content
            
            # Parse the final result into table format
            final_table = self._parse_ensemble_result(final_result)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            logger.info(f"Meta-ensemble triangulation completed in {processing_time:.2f}s")
            
            return {
                "final_ensemble_result": final_result,
                "final_ensemble_table": final_table,
                "current_step": "meta_ensemble_completed",
                "progress_percentage": 100,
                "logs": [f"Meta-ensemble triangulation completed successfully in {processing_time:.2f}s"]
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error during meta-ensemble triangulation: {error_msg}")
            
            return {
                "current_step": "meta_ensemble_failed",
                "logs": [f"Meta-ensemble triangulation failed: {error_msg}"]
            }
    
    def _build_ensemble_prompt(self, product_name: str, run_results: List[Dict[str, Any]]) -> str:
        """Build prompt for final ensemble triangulation"""
        
        # Prepare run results for analysis
        ensemble_data = ""
        for i, run_result in enumerate(run_results, 1):
            ensemble_data += f"\n=== RUN {i} TRIANGULATION RESULT ===\n"
            ensemble_data += run_result.get("triangulated_result", "No result")
            ensemble_data += "\n"
        
        prompt = f"""<role>
You are a meta-ensemble specialist performing the final triangulation of 3 independent specification extraction runs for {product_name}.
</role>

<task>
Analyze 3 triangulation results to identify the most consistent and reliable {product_name} specifications through consensus validation.
</task>

<meta_ensemble_methodology>
Apply this proven consensus-building process:

STEP 1 - CONSISTENCY ANALYSIS:
• Identify specifications that appear in multiple runs (2/3 or 3/3)
• Higher confidence for specs appearing in all 3 runs
• Note variations in option names across runs

STEP 2 - SEMANTIC CONSOLIDATION:
• Merge specifications with same meaning across runs:
  - "Power" = "Power Rating" = "Capacity"
  - "Phase" = "Phase Type" = "Phase Configuration"
• Combine option lists from all runs for comprehensive coverage

STEP 3 - FREQUENCY CONSENSUS:
• For specs appearing in multiple runs, use the most consistent options
• Prioritize options that appear across multiple runs
• Validate business relevance of each specification

STEP 4 - CONFIDENCE RANKING:
Rank specifications by consensus score:
• Appears in 3/3 runs: Highest confidence (weight: 100%)
• Appears in 2/3 runs: Medium confidence (weight: 70%)
• Appears in 1/3 runs: Low confidence (weight: 30%)
</meta_ensemble_methodology>

<validation_rules>
INCLUDE specifications that:
✓ Appear in at least 2/3 runs OR have very high confidence in 1 run
✓ Have consistent options across runs
✓ Directly influence {product_name} purchasing decisions
✓ Represent tangible, measurable attributes

EXCLUDE specifications that:
✗ Appear in only 1/3 runs with low confidence
✗ Have conflicting interpretations across runs
✗ Are generic descriptors or location-specific
✗ Duplicate the product name or are overly broad
</validation_rules>

<run_results>
{ensemble_data}
</run_results>

<output_requirements>
Create the final consensus specification table with EXACTLY this format:

| Specification Name | Top Options (consensus across runs) | Why it matters in the market | Impacts Pricing? |

Requirements:
1. Specification Name: Most consistent name across runs
2. Top Options: 3-5 options with highest consensus (comma-separated)
3. Why it matters: Business justification based on market analysis
4. Impacts Pricing: "✅ Yes" or "❌ No" based on consensus assessment

CRITICAL INSTRUCTIONS:
• Limit to 3-5 highest confidence specifications
• Use options that appeared in multiple runs when possible
• Ensure each specification has multiple distinct options
• Focus on specifications with strong consensus
• Provide clear business justifications
</output_requirements>

<final_validation>
Before submitting, ensure:
□ All specifications have strong consensus (2/3 or 3/3 runs)
□ Options represent the best consensus across runs
□ Business justifications are market-focused
□ Pricing impact assessment is defensible
□ Output matches the required table format exactly
</final_validation>"""
        
        return prompt
    
    def _parse_ensemble_result(self, result: str) -> List[Dict[str, Any]]:
        """Parse ensemble result into structured table format"""
        try:
            lines = result.strip().split('\n')
            table_data = []
            rank = 1
            
            logger.info(f"Processing {len(lines)} lines for ensemble parsing")
            
            for i, line in enumerate(lines):
                line = line.strip()
                
                # Skip empty lines, headers, and separator lines
                if not line:
                    continue
                if 'Specification Name' in line:
                    continue
                if line.startswith('|--') or line.startswith('|-'):
                    continue
                if line.count('|') < 3:
                    continue
                
                # Look for table rows
                if '|' in line:
                    cleaned_line = line
                    if cleaned_line.startswith('|'):
                        cleaned_line = cleaned_line[1:]
                    if cleaned_line.endswith('|'):
                        cleaned_line = cleaned_line[:-1]
                    
                    parts = [part.strip() for part in cleaned_line.split('|')]
                    
                    if len(parts) >= 4:
                        table_data.append({
                            'Rank': rank,
                            'Specification': parts[0],
                            'Top Options': parts[1].replace('(consensus across runs)', '').strip(),
                            'Why it matters': parts[2].replace('in the market', '').strip(),
                            'Impacts Pricing?': parts[3]
                        })
                        rank += 1
                        logger.info(f"Added ensemble row {rank-1}: {parts[0]}")
            
            logger.info(f"Successfully parsed {len(table_data)} ensemble table rows")
            return table_data
            
        except Exception as e:
            logger.error(f"Error parsing ensemble result: {e}")
            return [{
                'Rank': 1,
                'Specification': 'Ensemble Parse Error',
                'Top Options': 'Could not parse ensemble result',
                'Why it matters': 'Error in parsing',
                'Impacts Pricing?': 'Unknown'
            }]

class TriangulationAgent:
    """Agent for triangulating results from all sources"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            temperature=0.1
        )
    
    def triangulate_results(self, state: SpecExtractionState) -> SpecExtractionState:
        """Triangulate results from all completed agents"""
        start_time = time.time()
        
        try:
            logger.info("Starting triangulation process")
            
            # Get all completed agent results using helper function
            agent_results = get_agent_results(state)
            completed_agents = {
                source: result for source, result in agent_results.items()
                if result.get("status") == "completed"
            }
            
            if not completed_agents:
                raise ValueError("No completed agent results to triangulate")
            
            # Prepare datasets for triangulation prompt
            datasets = []
            all_dataset_outputs = {}
            
            for source, result in completed_agents.items():
                dataset_info = {
                    "source": source,
                    "type": result["source_type"],
                    "rows_processed": result["raw_data_count"],
                    "extracted_specs": result["extracted_specs"]
                }
                datasets.append(dataset_info)
                all_dataset_outputs[source] = result["extracted_specs"]
            
            # Build triangulation prompt using multi-agent consensus and validation techniques
            prompt = self._build_triangulation_prompt(
                product_name=state["product_name"],
                datasets=datasets,
                all_dataset_outputs=all_dataset_outputs
            )
            
            logger.info(f"Sending triangulation request for {len(datasets)} datasets")
            
            # Call LLM for triangulation
            response = self.llm.invoke([HumanMessage(content=prompt)])
            triangulated_result = response.content
            
            # Debug: Log the raw LLM output
            logger.info(f"Raw LLM triangulation output: {triangulated_result}")
            
            # Parse the triangulated result into table format for export
            triangulated_table = self._parse_triangulation_result(triangulated_result)
            
            # Debug: Log the parsed table
            logger.info(f"Parsed triangulation table: {triangulated_table}")
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            logger.info(f"Triangulation completed in {processing_time:.2f}s")
            
            # Return only the keys this function should update
            return {
                "triangulated_result": triangulated_result,
                "triangulated_table": triangulated_table,
                "current_step": "completed",
                "progress_percentage": 100,
                "logs": [f"Triangulation completed successfully in {processing_time:.2f}s"]
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error during triangulation: {error_msg}")
            
            # Return error state updates
            return {
                "current_step": "triangulation_failed",
                "logs": [f"Triangulation failed: {error_msg}"]
            }
    
    def _build_triangulation_prompt(self, product_name: str, datasets: List[Dict], all_dataset_outputs: Dict) -> str:
        """Build triangulation prompt using multi-agent consensus and validation techniques"""
        
        # Research-backed triangulation prompt with enhanced accuracy
        prompt = f"""<role>
You are a senior data triangulation specialist with expertise in multi-source B2B specification analysis. You excel at identifying patterns across diverse datasets and determining which specifications truly drive purchasing decisions for {product_name}.
</role>

<task>
Analyze {len(datasets)} independent extraction results to identify the most critical {product_name} specifications through cross-validation and consensus building.
</task>

<triangulation_methodology>

For the triangulation, give me results and top specifications that came from these datasets. Don't give 
the dataset itself in your response.
Merge Semantically same Specification options and name. Duplicate Specifications name should not be 
there. At least 2 options should be there to display any specification important and Specification name 
and Specification options should not be same or contain same words as in {product_name}.

</triangulation_methodology>

<validation_rules>
INCLUDE specifications that:
✓ Appear in 2+ sources OR have very high frequency in 1 source
✓ Have at least 2 meaningful options
✓ Directly influence {product_name} selection
✓ Represent tangible product attributes

EXCLUDE specifications that:
✗ Are generic descriptors (e.g., "Good Quality", "Best")
✗ Duplicate the product name (e.g., "Generator Type" for generators)
✗ Represent brands/companies (unless brand is a key differentiator)
✗ Are location-specific (unless critical for the product)
</validation_rules>

<datasets_to_analyze>
{json.dumps(all_dataset_outputs, indent=2)}
</datasets_to_analyze>

<output_requirements>
Create a business-focused specification table with EXACTLY this format:

| Specification Name | Top Options (based on data) | Why it matters in the market | Impacts Pricing? |

Requirements for each row:
1. Specification Name: Clear, professional terminology
2. Top Options: 3-5 most frequent options from the data (comma-separated)
3. Why it matters: Concise business justification (buying behavior, compatibility, regulations)
4. Impacts Pricing: "✅ Yes" or "❌ No" based on market analysis

CRITICAL INSTRUCTIONS:
• Limit to 3-5 most impactful specifications
• Use exact options from the data (don't invent new ones)
• Ensure each specification has multiple real options
• Focus on specifications that differentiate products
• Keep explanations concise and business-oriented
</output_requirements>

<example_output>
| Material | Aluminium, Steel, Stainless Steel, Cast Iron | Affects durability, weight, and corrosion resistance - key factors in industrial applications | ✅ Yes |
| Power Rating | 5 KVA, 7.5 KVA, 10 KVA, 15 KVA | Determines suitable applications and load capacity - primary selection criteria | ✅ Yes |
| Phase Configuration | Single Phase, Three Phase | Must match facility electrical infrastructure - non-negotiable compatibility requirement | ✅ Yes |
</example_output>

<final_validation>
Before submitting, ensure:
□ All options come directly from the provided datasets
□ Specifications represent consensus across multiple sources
□ Business justifications are specific to {product_name} market
□ Pricing impact assessment is logical and defensible
□ Output matches the required table format exactly
</final_validation>"""
        
        return prompt
    
    def _parse_triangulation_result(self, result: str) -> List[Dict[str, Any]]:
        """Parse triangulation result into structured table format for export"""
        try:
            lines = result.strip().split('\n')
            table_data = []
            rank = 1
            
            # Debug: log each line being processed
            logger.info(f"Processing {len(lines)} lines for parsing")
            
            # Look for table format in the result
            for i, line in enumerate(lines):
                line = line.strip()
                
                # Debug: log the line being processed
                logger.info(f"Line {i}: '{line}' - Pipe count: {line.count('|')}")
                
                # Skip empty lines, headers, and separator lines
                if not line:
                    continue
                if 'Specification Name' in line:
                    continue
                if line.startswith('|--') or line.startswith('|-'):
                    continue
                if line.count('|') < 3:
                    continue
                
                # Look for table rows (containing | separator)
                if '|' in line:
                    # Clean up the line
                    cleaned_line = line
                    if cleaned_line.startswith('|'):
                        cleaned_line = cleaned_line[1:]
                    if cleaned_line.endswith('|'):
                        cleaned_line = cleaned_line[:-1]
                    
                    parts = [part.strip() for part in cleaned_line.split('|')]
                    
                    # Debug: log the parts
                    logger.info(f"Parsed parts: {parts} (count: {len(parts)})")
                    
                    # Ensure we have at least 4 parts (spec, options, why, pricing)
                    if len(parts) >= 4:
                        # Map to competitor's format
                        table_data.append({
                            'Rank': rank,
                            'Specification': parts[0],  # Changed from 'Specification Name'
                            'Top Options': parts[1].replace('(based on data)', '').strip(),  # Remove "(based on data)"
                            'Why it matters': parts[2].replace('in the market', '').strip(),  # Remove "in the market"
                            'Impacts Pricing?': parts[3]  # Changed to include question mark
                        })
                        rank += 1
                        logger.info(f"Successfully added row {rank-1}: {parts[0]}")
            
            # Debug log
            logger.info(f"Successfully parsed {len(table_data)} table rows")
            
            return table_data
            
        except Exception as e:
            logger.error(f"Error parsing triangulation result: {e}")
            # Return a fallback structure with competitor's format
            return [{
                'Rank': 1,
                'Specification': 'Parse Error',
                'Top Options': 'Could not parse result',
                'Why it matters': 'Error in parsing',
                'Impacts Pricing?': 'Unknown'
            }]


def triangulate_all_results(state: SpecExtractionState) -> SpecExtractionState:
    """LangGraph node function for triangulation"""
    agent = TriangulationAgent()
    return agent.triangulate_results(state)

def meta_ensemble_triangulate(state: SpecExtractionState) -> SpecExtractionState:
    """LangGraph node function for meta-ensemble triangulation"""
    agent = MetaEnsembleAgent()
    return agent.ensemble_triangulate(state)

def check_all_agents_completed(state: SpecExtractionState) -> str:
    """Check if all agents have completed processing"""
    uploaded_sources = set(state["uploaded_files"].keys())
    agents_status = get_agents_status(state)
    
    completed_sources = {
        source for source, status in agents_status.items()
        if status == "completed"
    }
    failed_sources = {
        source for source, status in agents_status.items()
        if status == "failed"
    }
    
    # If all uploaded sources are either completed or failed, we can proceed
    if uploaded_sources <= (completed_sources | failed_sources):
        if completed_sources:  # At least one completed successfully
            return "triangulate"
        else:  # All failed
            return "all_failed"
    else:
        return "wait"  # Still processing 
