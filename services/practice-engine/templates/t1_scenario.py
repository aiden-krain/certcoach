"""
T1: Scenario Multiple Choice Question Template
One best answer; ties to blueprint decision points
"""

from typing import Dict, List, Optional
from pydantic import BaseModel


class ScenarioMCQTemplate(BaseModel):
    """Template for scenario-based multiple choice questions"""
    
    template_id: str = "t1_scenario"
    name: str = "Scenario MCQ"
    description: str = "Scenario-based multiple choice with one best answer"
    
    # Template structure
    scenario_context: str
    question_stem: str
    options: List[str]  # 4-5 options typically
    correct_option_index: int
    rationale: str
    difficulty_factors: List[str]
    blueprint_alignment: str
    
    def generate_prompt(self, context: Dict) -> str:
        """Generate LLM prompt for creating this question type"""
        return f"""
        Create a scenario-based multiple choice question for {context['exam_id']} 
        targeting objective: {context['objective_id']}.
        
        Requirements:
        - Present a realistic workplace scenario
        - Include relevant technical details and constraints
        - Provide 4-5 plausible options with only one clearly best answer
        - Focus on decision-making and application of concepts
        - Align with blueprint decision point: {context.get('decision_point', 'N/A')}
        
        Scenario Context: {context.get('scenario_context', 'Professional working environment')}
        Technical Focus: {context.get('technical_focus', 'General concept application')}
        Difficulty Level: {context.get('difficulty', 'intermediate')}
        
        Format:
        SCENARIO: [Detailed scenario description]
        QUESTION: [What should be done/recommended/implemented?]
        A) [Option 1]
        B) [Option 2] 
        C) [Option 3]
        D) [Option 4]
        [E) Option 5 if needed]
        
        CORRECT: [Letter]
        RATIONALE: [Detailed explanation why the correct answer is best and why others are incorrect]
        SOURCES: [1-2 official documentation links]
        """
    
    def validate_generated_item(self, item_data: Dict) -> Dict[str, List[str]]:
        """Validate a generated item meets template requirements"""
        errors = []
        warnings = []
        
        # Check required fields
        required_fields = ['scenario', 'question', 'options', 'correct_answer', 'rationale']
        for field in required_fields:
            if field not in item_data or not item_data[field]:
                errors.append(f"Missing required field: {field}")
        
        # Validate options
        if 'options' in item_data:
            options = item_data['options']
            if len(options) < 4 or len(options) > 5:
                warnings.append("Should have 4-5 options for optimal difficulty")
            
            # Check for option length balance
            option_lengths = [len(opt) for opt in options]
            if max(option_lengths) > 2 * min(option_lengths):
                warnings.append("Option lengths vary significantly - may indicate answer")
        
        # Check rationale quality
        if 'rationale' in item_data:
            rationale = item_data['rationale']
            if len(rationale) < 100:
                warnings.append("Rationale should be more detailed (>100 chars)")
            
            # Look for explanation of incorrect options
            if not any(word in rationale.lower() for word in ['incorrect', 'wrong', 'not', 'however']):
                warnings.append("Rationale should explain why incorrect options are wrong")
        
        return {'errors': errors, 'warnings': warnings}
    
    def get_difficulty_factors(self) -> List[str]:
        """Return factors that influence question difficulty"""
        return [
            "Number of variables in scenario",
            "Depth of technical knowledge required", 
            "Number of plausible distractors",
            "Complexity of decision-making process",
            "Integration of multiple concepts",
            "Real-world application complexity"
        ]


# Example usage and test data
EXAMPLE_SCENARIO_MCQ = {
    "scenario": """
    Your organization is implementing a new data analytics solution using Microsoft Fabric. 
    The solution needs to process 500GB of daily transaction data from multiple sources 
    (SQL databases, REST APIs, and CSV files) and make it available for real-time 
    dashboards and weekly reports. The data has varying schemas and includes sensitive 
    customer information that must comply with GDPR requirements.
    """,
    
    "question": """
    What is the BEST approach for implementing this data analytics solution?
    """,
    
    "options": [
        "Create a Fabric warehouse with scheduled data pipelines and implement row-level security",
        "Use a Fabric lakehouse with Auto Loader for ingestion and Unity Catalog for governance", 
        "Set up separate Fabric workspaces for each data source with individual security policies",
        "Implement a hybrid approach using both lakehouse and warehouse with data virtualization",
        "Create a single data pipeline that transforms all data into a common schema before storage"
    ],
    
    "correct_answer": "A",
    
    "rationale": """
    Option A is correct because a Fabric warehouse provides the structured environment 
    needed for real-time dashboards and reporting, while scheduled data pipelines can 
    handle the 500GB daily volume efficiently. Row-level security directly addresses 
    GDPR compliance requirements for sensitive customer data.
    
    Option B is incorrect because Unity Catalog is Databricks-specific, not Fabric.
    Option C creates unnecessary complexity and governance overhead.
    Option D adds complexity without clear benefits for this use case.
    Option E is too rigid and doesn't handle schema variations effectively.
    """,
    
    "sources": [
        {
            "title": "Microsoft Fabric Warehouse Overview",
            "url": "https://learn.microsoft.com/en-us/fabric/data-warehouse/",
            "license": "Microsoft Documentation License"
        },
        {
            "title": "Row-level Security in Fabric",
            "url": "https://learn.microsoft.com/en-us/fabric/data-warehouse/row-level-security",
            "license": "Microsoft Documentation License"
        }
    ],
    
    "metadata": {
        "blueprint_objective": "impl_manage_analytics.security_governance",
        "difficulty": "intermediate",
        "estimated_time_seconds": 120,
        "decision_point": "Choosing architecture for analytics workloads",
        "key_concepts": ["Fabric warehouse", "Data pipelines", "Row-level security", "GDPR compliance"]
    }
}


def create_scenario_mcq_from_template(objective_id: str, context: Dict) -> Dict:
    """Create a scenario MCQ using the template and provided context"""
    template = ScenarioMCQTemplate()
    
    # This would integrate with LLM service to generate the actual question
    # For now, return template structure
    return {
        "template_type": "scenario_mcq",
        "objective_id": objective_id,
        "prompt": template.generate_prompt(context),
        "validation_criteria": template.get_difficulty_factors(),
        "example": EXAMPLE_SCENARIO_MCQ
    }
