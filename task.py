from crewai import Task
from agents import market_researcher, financial_analyst, verifier
from tools import FinancialDocumentTool, search_web


# Market Research Task - Shortened
market_research_task = Task(
    description=(
        "Research current market trends for: {query}\n"
        "Focus on: market conditions, economic indicators, sector news, key movements.\n"
        "Keep response under 1000 words, prioritize actionable insights."
    ),
    expected_output=(
        "Concise market research (800-1000 words):\n"
        "- Current market conditions (3-4 bullet points)\n"
        "- Key economic indicators (2-3 main ones)\n"
        "- Sector news relevance (2-3 key points)\n"
        "- Investment implications (summary)"
    ),
    agent=market_researcher,
    async_execution=False
)

# Financial Analysis Task - Shortened
analyze_financial_document = Task(
    description=(
        "Analyze financial document for: {query}\n"
        "Extract key metrics, integrate market context, provide clear recommendation.\n"
        "Limit to 1200 words maximum, focus on decision-critical information."
    ),
    expected_output=(
        "Financial analysis (1000-1200 words):\n"
        "- Executive summary (150 words)\n"
        "- Key financial metrics (5-7 main ratios)\n"
        "- Investment recommendation with 3 key reasons\n"
        "- Risk factors (3-5 main risks)\n"
        "- Market integration (brief)"
    ),
    agent=financial_analyst,
    context=[market_research_task],
    async_execution=False
)

# Verification Task - Shortened  
verification = Task(
    description=(
        "Verify analysis accuracy and provide confidence rating.\n"
        "Focus on data validation and final assessment.\n"
        "Keep under 600 words."
    ),
    expected_output=(
        "Verification report (400-600 words):\n"
        "- Data accuracy check (pass/concerns)\n"
        "- Analysis consistency (validated/issues)\n"
        "- Confidence rating (High/Medium/Low) with reason\n"
        "- Final recommendation validation"
    ),
    agent=verifier,
    context=[analyze_financial_document],
    async_execution=False
)