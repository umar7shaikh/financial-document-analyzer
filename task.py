from crewai import Task
from agents import market_researcher, financial_analyst, verifier
from tools import FinancialDocumentTool, search_web


# Market Research Task - Uses function call instead of tool
market_research_task = Task(
    description=(
        "Research the latest market trends and economic data related to: {query}\n\n"
        "You have access to web search functionality. Use it to search for:\n"
        "1. Current market conditions and sector trends\n"
        "2. Recent economic indicators (inflation, interest rates, GDP)\n"
        "3. Industry-specific news and analysis\n"
        "4. Recent financial news and market movements\n\n"
        "Search for relevant information and provide comprehensive market context."
    ),
    expected_output=(
        "A detailed market research report including:\n"
        "- Current market trends and conditions\n"
        "- Relevant economic indicators and implications\n"
        "- Sector-specific news and competitive landscape\n"
        "- Key market movements and potential impact\n"
        "- Sources and dates for all information\n"
        "- Summary of key insights for investment decisions"
    ),
    agent=market_researcher,
    async_execution=False
)

# Financial Analysis Task
analyze_financial_document = Task(
    description=(
        "Analyze the financial document to answer: {query}\n\n"
        "1. Extract key financial metrics from the document at path: {file_path}\n"
        "2. Use market research context from the previous task\n"
        "3. Analyze financial performance and trends\n"
        "4. Identify investment opportunities and risks\n"
        "5. Provide data-driven investment recommendations\n\n"
        "Read the document content and provide comprehensive analysis."
    ),
    expected_output=(
        "A comprehensive financial analysis report including:\n"
        "- Executive summary of key findings\n"
        "- Key financial metrics and ratios analysis\n"
        "- Investment recommendation (BUY/HOLD/SELL) with rationale\n"
        "- Risk assessment (LOW/MEDIUM/HIGH) with factors\n"
        "- Market context integration\n"
        "- Actionable investment insights"
    ),
    agent=financial_analyst,
    context=[market_research_task],
    async_execution=False
)

# Verification Task
verification = Task(
    description=(
        "Verify and validate the financial analysis for accuracy and completeness:\n"
        "1. Review the financial data extraction\n"
        "2. Cross-check analysis conclusions\n"
        "3. Ensure recommendations are well-supported\n"
        "4. Validate market research integration\n"
        "5. Provide confidence rating"
    ),
    expected_output=(
        "A verification report including:\n"
        "- Document quality assessment\n"
        "- Data accuracy validation\n"
        "- Analysis consistency review\n"
        "- Investment recommendation validation\n"
        "- Overall confidence rating (High/Medium/Low)\n"
        "- Final approval or revision recommendations"
    ),
    agent=verifier,
    context=[analyze_financial_document],
    async_execution=False
)
