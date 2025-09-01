"""
T3: Troubleshooting Template
Logs/errors → root-cause/next step
"""

from typing import Dict, List, Optional


class TroubleshootingTemplate:
    """Template for troubleshooting questions with logs/errors"""
    
    template_id: str = "t3_troubleshoot"
    name: str = "Troubleshooting"
    description: str = "Analyze logs/errors to identify root cause and solution"
    
    def generate_prompt(self, context: Dict) -> str:
        """Generate LLM prompt for creating this question type"""
        return f"""
        Create a troubleshooting question for {context['exam_id']} 
        targeting objective: {context['objective_id']}.
        
        Requirements:
        - Present realistic error logs, stack traces, or performance metrics
        - Include enough context to diagnose the issue
        - Ask for root cause identification or next troubleshooting step
        - Provide plausible but incorrect diagnoses as distractors
        - Rationale should explain diagnostic reasoning
        
        Error Type: {context.get('error_type', 'Performance issue')}
        Technology Focus: {context.get('technology', 'Spark/Delta Lake')}
        Complexity Level: {context.get('difficulty', 'intermediate')}
        
        Format:
        SITUATION: [Context of the problem]
        ERROR/LOGS:
        ```
        [Realistic error messages, logs, or metrics]
        ```
        
        QUESTION: What is the most likely root cause / What should you do next?
        A) [Diagnosis/Solution 1]
        B) [Diagnosis/Solution 2] 
        C) [Diagnosis/Solution 3]
        D) [Diagnosis/Solution 4]
        [E) Diagnosis/Solution 5 if needed]
        
        CORRECT: [Letter]
        RATIONALE: [Diagnostic reasoning and troubleshooting steps]
        SOURCES: [1-2 official documentation links]
        """
    
    def validate_generated_item(self, item_data: Dict) -> Dict[str, List[str]]:
        """Validate a generated item meets template requirements"""
        errors = []
        warnings = []
        
        # Check for error/log content
        if 'error_logs' not in item_data or not item_data['error_logs']:
            errors.append("Missing error logs or diagnostic information")
        
        # Check question focuses on troubleshooting
        if 'question' in item_data:
            question = item_data['question'].lower()
            troubleshoot_words = ['cause', 'issue', 'problem', 'troubleshoot', 'debug', 'fix', 'solve']
            if not any(word in question for word in troubleshoot_words):
                warnings.append("Question should focus on troubleshooting/diagnosis")
        
        # Check for technical depth in rationale
        if 'rationale' in item_data:
            rationale = item_data['rationale'].lower()
            if len(rationale) < 150:
                warnings.append("Troubleshooting rationale should be detailed (>150 chars)")
            
            diagnostic_words = ['because', 'indicates', 'suggests', 'shows', 'evidence']
            if not any(word in rationale for word in diagnostic_words):
                warnings.append("Rationale should explain diagnostic reasoning")
        
        return {'errors': errors, 'warnings': warnings}


# Example usage and test data
EXAMPLE_TROUBLESHOOTING = {
    "situation": """
    Your Databricks job that processes daily sales data has been failing intermittently. 
    The job reads from Delta Lake tables, performs aggregations, and writes results to 
    a new table. It worked fine for months but started failing after data volume increased.
    """,
    
    "error_logs": """
    Exception in thread "main" org.apache.spark.SparkException: Job aborted due to stage failure
        at org.apache.spark.scheduler.DAGScheduler.handleJobSubmitted(DAGScheduler.scala:1234)
        
    Caused by: org.apache.spark.shuffle.MetadataFetchFailedException: Missing an output location for shuffle 0
        at org.apache.spark.shuffle.BlockStoreShuffleReader.read(BlockStoreShuffleReader.scala:165)
        
    Driver logs:
    24/01/15 10:30:45 WARN TaskSetManager: Lost task 15.3 in stage 2.0 (TID 487, 10.0.1.123, executor 4): 
    java.io.IOException: No space left on device
        at java.io.FileOutputStream.writeBytes(Native Method)
    
    Spark UI shows:
    - Total data processed: 2.1 TB
    - Shuffle write: 856 GB  
    - Peak executor memory usage: 95%
    - Task failures: 23 out of 200 tasks
    """,
    
    "question": "What is the most likely root cause of this job failure?",
    
    "options": [
        "The Delta Lake table is corrupted and needs to be rebuilt using VACUUM command",
        "Insufficient executor memory causing spill to disk and eventual disk space exhaustion", 
        "Network connectivity issues between driver and executors causing shuffle failures",
        "Outdated Databricks runtime version incompatible with current Delta Lake format",
        "Concurrent writes to the target table creating lock conflicts and transaction failures"
    ],
    
    "correct_answer": "B",
    
    "rationale": """
    The root cause is insufficient executor memory leading to disk space exhaustion:
    
    Key diagnostic evidence:
    1. "No space left on device" error directly indicates disk space issues
    2. "Missing an output location for shuffle 0" suggests shuffle files couldn't be written
    3. Peak executor memory usage at 95% indicates memory pressure
    4. Large shuffle write (856 GB) with high memory usage forces spilling to disk
    5. The issue started when data volume increased, confirming memory/disk relationship
    
    The sequence: increased data → memory pressure → excessive spill to disk → disk full → shuffle failure → job abort
    
    Option A is incorrect - no corruption indicators in the logs
    Option C is incorrect - network issues would show different error patterns
    Option D is incorrect - runtime compatibility issues would fail consistently, not intermittently
    Option E is incorrect - lock conflicts show different error messages and patterns
    
    Solution: Increase executor memory or reduce data processed per partition.
    """,
    
    "sources": [
        {
            "title": "Databricks Spark Performance Tuning",
            "url": "https://docs.databricks.com/optimizations/spark-performance-tuning.html",
            "license": "Databricks Documentation License"
        },
        {
            "title": "Apache Spark Memory Management",
            "url": "https://spark.apache.org/docs/latest/tuning.html#memory-management-overview",
            "license": "Apache 2.0"
        }
    ],
    
    "metadata": {
        "blueprint_objective": "troubleshooting_optimization.debugging",
        "difficulty": "advanced",
        "estimated_time_seconds": 240,
        "error_type": "memory_performance",
        "key_concepts": ["Memory management", "Shuffle operations", "Disk spilling", "Error analysis", "Performance tuning"]
    }
}

EXAMPLE_TROUBLESHOOTING_FABRIC = {
    "situation": """
    Your Microsoft Fabric data pipeline runs daily to load customer data from multiple 
    sources into a lakehouse. Recently, the pipeline has been completing successfully 
    but downstream reports show missing data for certain customer segments.
    """,
    
    "error_logs": """
    Pipeline Run Status: Succeeded (with warnings)
    
    Activity: Copy Data from SQL Server
    Status: Succeeded
    Rows processed: 1,247,832
    
    Activity: Copy Data from REST API  
    Status: Succeeded with warnings
    Warning: Rate limit exceeded, retrying...
    Warning: Timeout on request to https://api.customer-service.com/v2/customers?page=47
    Final status: Partial data retrieved (estimated 85% completion)
    
    Activity: Merge to Delta Table
    Status: Succeeded  
    Rows inserted: 934,567
    Rows updated: 298,421
    
    Data validation check:
    Expected customer count (based on source system counts): 1,247,832
    Actual customer count in lakehouse: 1,233,988
    Missing records: 13,844 (1.1%)
    """,
    
    "question": "What is the most likely cause of the missing customer data?",
    
    "options": [
        "The Delta Lake merge operation failed to handle duplicate customer IDs correctly",
        "The REST API data source has intermittent connectivity issues causing incomplete data retrieval",
        "The SQL Server source connection is dropping rows due to incompatible data types", 
        "The lakehouse storage is approaching capacity limits causing write failures",
        "The pipeline schedule is running too frequently causing data consistency issues"
    ],
    
    "correct_answer": "B",
    
    "rationale": """
    The missing data is caused by incomplete REST API data retrieval:
    
    Evidence analysis:
    1. REST API activity shows "Partial data retrieved (estimated 85% completion)"
    2. Timeout error on page 47 indicates pagination retrieval failure
    3. Rate limiting warnings suggest API throttling issues  
    4. SQL Server data loaded completely (1,247,832 rows as expected)
    5. Missing record count (13,844) aligns with ~15% REST API failure (15% of ~92k API records ≈ 13.8k)
    
    The REST API source couldn't complete full data extraction due to:
    - Rate limiting by the API provider
    - Timeout on specific pagination requests
    - Pipeline not configured to handle API throttling properly
    
    Option A is incorrect - merge succeeded and processed expected row counts
    Option C is incorrect - SQL Server data loaded completely
    Option D is incorrect - no storage capacity errors reported
    Option E is incorrect - scheduling frequency doesn't explain the specific REST API failures
    
    Solution: Implement exponential backoff, increase timeout settings, or request higher API rate limits.
    """,
    
    "sources": [
        {
            "title": "Fabric Data Pipeline Error Handling",
            "url": "https://learn.microsoft.com/en-us/fabric/data-factory/pipeline-troubleshoot-guide",
            "license": "Microsoft Documentation License"
        }
    ],
    
    "metadata": {
        "blueprint_objective": "ingest_transform_data.data_pipelines", 
        "difficulty": "intermediate",
        "estimated_time_seconds": 200,
        "error_type": "data_completeness",
        "key_concepts": ["Pipeline troubleshooting", "API rate limiting", "Data validation", "Error analysis"]
    }
}


def create_troubleshooting_from_template(objective_id: str, context: Dict) -> Dict:
    """Create a troubleshooting question using the template and provided context"""
    template = TroubleshootingTemplate()
    
    return {
        "template_type": "troubleshooting",
        "objective_id": objective_id,
        "prompt": template.generate_prompt(context),
        "validation_criteria": template.validate_generated_item,
        "examples": [EXAMPLE_TROUBLESHOOTING, EXAMPLE_TROUBLESHOOTING_FABRIC]
    }
