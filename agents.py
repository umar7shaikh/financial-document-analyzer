import os
from crewai import Agent, LLM
from dotenv import load_dotenv

load_dotenv()

groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    raise ValueError("Please set GROQ_API_KEY in your .env file")

# Use Groq with Llama 3.3 70B - Fast and powerful!
groq_llm = LLM(
    model="groq/llama-3.3-70b-versatile",
    api_key=groq_api_key
)

market_researcher = Agent(
    role="Market Research Specialist",
    goal="Research current market trends and economic data related to: {query}",
    verbose=True,
    memory=False,
    backstory=(
        "You are a market research expert with extensive experience in financial markets. "
        "You specialize in gathering financial news, market trends, and economic indicators "
        "to provide comprehensive market context for investment decisions."
    ),
    llm=groq_llm,
    allow_delegation=False
)

financial_analyst = Agent(
    role="Senior Financial Analyst",
    goal="Provide comprehensive financial analysis combining document data with market research for: {query}",
    verbose=True,
    memory=False,
    backstory=(
        "You are an experienced financial analyst with 15+ years in investment banking "
        "and corporate finance. You specialize in analyzing financial statements, "
        "identifying key financial metrics, and providing data-driven investment insights."
    ),
    llm=groq_llm,
    allow_delegation=False
)

verifier = Agent(
    role="Financial Document Verifier", 
    goal="Verify financial documents for accuracy and validate analysis findings",
    verbose=True,
    memory=False,
    backstory=(
        "You are a document verification specialist with expertise in financial reporting "
        "standards and regulatory compliance. You ensure accuracy and completeness of analysis."
    ),
    llm=groq_llm,
    allow_delegation=False
)
