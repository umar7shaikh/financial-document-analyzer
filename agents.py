import os
from crewai import Agent, LLM
from dotenv import load_dotenv

load_dotenv()

groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    raise ValueError("Please set GROQ_API_KEY in your .env file")

# Optimized LLM configuration for quality output
groq_llm = LLM(
    model="groq/llama-3.3-70b-versatile",
    api_key=groq_api_key,
    temperature=0.2,  # Slightly higher for more focused responses
    max_tokens=3500   # Reduced but sufficient for quality
)

market_researcher = Agent(
    role="Market Research Specialist",
    goal="Research current market trends and economic data related to: {query}",
    verbose=True,
    memory=False,
    backstory=(
        "You are a senior market research analyst who delivers CONCISE, high-impact reports "
        "in exactly 600-800 words. You focus on actionable insights over lengthy descriptions. "
        "Your expertise is in quickly identifying the most critical market factors that impact "
        "investment decisions. You search current data, extract key trends, and present findings "
        "with specific numbers, dates, and clear implications. Every sentence adds value - no filler content."
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
        "You are a top-tier financial analyst who produces COMPLETE but CONCISE analysis "
        "in exactly 800-1000 words. You extract ALL critical financial metrics from documents "
        "efficiently, focusing on the most impactful data points. Your analysis includes: "
        "executive summary (100 words), key metrics (5-7 ratios), clear BUY/HOLD/SELL recommendation "
        "with 3 specific reasons, and integrated market context. You eliminate redundancy and "
        "prioritize decision-critical information. Every metric you include directly supports your conclusion."
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
        "You are a meticulous verification expert who delivers FOCUSED validation reports "
        "in exactly 400-500 words. You efficiently cross-check key financial data, validate "
        "analysis logic, and provide clear confidence ratings (HIGH/MEDIUM/LOW) with specific "
        "reasoning. You focus on the most critical validation points: data accuracy of top 5 metrics, "
        "recommendation logic soundness, and market integration consistency. You deliver decisive "
        "conclusions without unnecessary elaboration."
    ),
    llm=groq_llm,
    allow_delegation=False
)
