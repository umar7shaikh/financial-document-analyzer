from crewai import Task
from agents import financial_analyst, verifier

analyze_financial_document = Task(
    description=(
        "Analyze the financial document to answer: {query}\n"
        "Extract key financial metrics and provide professional analysis."
    ),
    expected_output=(
        "A comprehensive financial analysis report with key findings and recommendations."
    ),
    agent=financial_analyst,
    async_execution=False
)

verification = Task(
    description=(
        "Verify the financial document for completeness and accuracy."
    ),
    expected_output=(
        "Document verification report with quality assessment."
    ),
    agent=verifier,
    async_execution=False
)
