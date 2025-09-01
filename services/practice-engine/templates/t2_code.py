"""
T2: Code/SQL Outcome Template
"What happens next?" for PySpark/SQL; rationale traces execution
"""

from typing import Dict, List, Optional


class CodeOutcomeTemplate:
    """Template for code/SQL outcome prediction questions"""
    
    template_id: str = "t2_code"
    name: str = "Code/SQL Outcome"
    description: str = "Predict the outcome of code execution with step-by-step rationale"
    
    def generate_prompt(self, context: Dict) -> str:
        """Generate LLM prompt for creating this question type"""
        return f"""
        Create a code outcome prediction question for {context['exam_id']} 
        targeting objective: {context['objective_id']}.
        
        Requirements:
        - Present working code snippet (PySpark, SQL, or Python)
        - Ask what happens when the code executes
        - Provide 4-5 realistic outcome options
        - Include subtle but important details that affect execution
        - Rationale should trace through execution step-by-step
        
        Code Type: {context.get('code_type', 'PySpark')}
        Technical Focus: {context.get('technical_focus', 'Data transformations')}
        Complexity Level: {context.get('difficulty', 'intermediate')}
        
        Format:
        SCENARIO: [Brief context for the code]
        CODE:
        ```{context.get('code_type', 'python')}
        [Code snippet - 5-15 lines]
        ```
        
        QUESTION: What will happen when this code executes?
        A) [Outcome option 1]
        B) [Outcome option 2]
        C) [Outcome option 3]
        D) [Outcome option 4]
        [E) Outcome option 5 if needed]
        
        CORRECT: [Letter]
        RATIONALE: [Step-by-step execution trace explaining the outcome]
        SOURCES: [1-2 official documentation links]
        """
    
    def validate_generated_item(self, item_data: Dict) -> Dict[str, List[str]]:
        """Validate a generated item meets template requirements"""
        errors = []
        warnings = []
        
        # Check for code block
        if 'code' not in item_data or not item_data['code']:
            errors.append("Missing code snippet")
        else:
            code_lines = item_data['code'].strip().split('\n')
            if len(code_lines) < 3:
                warnings.append("Code snippet should be more substantial (3+ lines)")
            if len(code_lines) > 20:
                warnings.append("Code snippet may be too long for time constraints")
        
        # Check for execution focus
        if 'question' in item_data:
            question = item_data['question'].lower()
            if not any(word in question for word in ['happen', 'result', 'output', 'execute', 'outcome']):
                warnings.append("Question should focus on execution outcome")
        
        # Check rationale traces execution
        if 'rationale' in item_data:
            rationale = item_data['rationale'].lower()
            execution_words = ['first', 'then', 'next', 'step', 'execute', 'process']
            if not any(word in rationale for word in execution_words):
                warnings.append("Rationale should trace execution steps")
        
        return {'errors': errors, 'warnings': warnings}


# Example usage and test data
EXAMPLE_CODE_OUTCOME = {
    "scenario": """
    You are working with a Delta Lake table containing customer transaction data. 
    The table has been optimized using Z-ordering on customer_id column.
    """,
    
    "code": """
    from pyspark.sql import SparkSession
    spark = SparkSession.builder.getOrCreate()
    
    # Read the transactions table
    df = spark.table("transactions")
    
    # Filter and aggregate
    result = (df
        .filter(df.transaction_date >= "2024-01-01")
        .groupBy("customer_id")
        .agg({"amount": "sum", "transaction_id": "count"})
        .withColumnRenamed("sum(amount)", "total_amount")
        .withColumnRenamed("count(transaction_id)", "transaction_count")
        .orderBy("total_amount", ascending=False)
        .limit(100)
    )
    
    result.write.mode("overwrite").saveAsTable("top_customers")
    """,
    
    "question": "What will happen when this code executes on a large transactions table?",
    
    "options": [
        "The query will execute efficiently due to Z-ordering on customer_id, and create a new table with top 100 customers",
        "The query will fail because you cannot use agg() with multiple aggregation functions on the same DataFrame", 
        "The query will execute but slowly because the orderBy operation requires a global sort across all partitions",
        "The query will fail because saveAsTable() requires explicit schema specification",
        "The query will execute efficiently because the filter operation will eliminate most data before aggregation"
    ],
    
    "correct_answer": "C",
    
    "rationale": """
    The code will execute successfully but with performance implications:
    
    1. First, the filter on transaction_date will scan the table and reduce data volume
    2. The groupBy on customer_id will benefit from Z-ordering for efficient data locality
    3. The aggregation (sum and count) will execute efficiently within each partition
    4. However, the orderBy operation requires a global sort across ALL partitions, which is expensive
    5. This global sort will cause data shuffling and create a performance bottleneck
    6. The limit(100) helps somewhat but occurs after the expensive sort operation
    7. Finally, saveAsTable() will succeed and overwrite any existing table
    
    Option A is incorrect - while Z-ordering helps with groupBy, the global sort is still expensive.
    Option B is incorrect - multiple aggregations in agg() are supported.
    Option D is incorrect - saveAsTable() can infer schema from the DataFrame.
    Option E is incorrect - the orderBy operation dominates performance, not the filter efficiency.
    """,
    
    "sources": [
        {
            "title": "PySpark DataFrame Operations",
            "url": "https://spark.apache.org/docs/latest/api/python/pyspark.sql.html#pyspark.sql.DataFrame",
            "license": "Apache 2.0"
        },
        {
            "title": "Delta Lake Z-Ordering",
            "url": "https://docs.delta.io/latest/optimizations-oss.html#z-ordering-multi-dimensional-clustering",
            "license": "Apache 2.0"
        }
    ],
    
    "metadata": {
        "blueprint_objective": "etl_spark_delta.spark_transformations",
        "difficulty": "intermediate", 
        "estimated_time_seconds": 180,
        "code_type": "pyspark",
        "key_concepts": ["DataFrame operations", "Aggregations", "Global sorting", "Z-ordering", "Performance"]
    }
}


def create_code_outcome_from_template(objective_id: str, context: Dict) -> Dict:
    """Create a code outcome question using the template and provided context"""
    template = CodeOutcomeTemplate()
    
    return {
        "template_type": "code_outcome",
        "objective_id": objective_id,
        "prompt": template.generate_prompt(context),
        "validation_criteria": template.validate_generated_item,
        "example": EXAMPLE_CODE_OUTCOME
    }
