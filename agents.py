import os
from dotenv import load_dotenv
load_dotenv()

from crewai import Agent

# Configure Hugging Face as OpenAI-compatible API
hf_token = os.getenv("HF_TOKEN")
if not hf_token:
    raise ValueError("Please set HF_TOKEN in your .env file")

# Set up CrewAI to use Hugging Face's OpenAI-compatible endpoint
os.environ["OPENAI_API_KEY"] = hf_token
os.environ["OPENAI_API_BASE"] = "https://api-inference.huggingface.co/v1"

# Now your agents will work with HF models!
financial_analyst = Agent(
    role="Senior Financial Analyst",
    goal="Provide comprehensive financial analysis based on the query: {query}",
    verbose=True,
    memory=True,
    backstory=(
        "You are an experienced financial analyst with 15+ years in investment banking "
        "and corporate finance. You specialize in analyzing financial statements, "
        "identifying key financial metrics, and providing data-driven investment insights."
    ),
    allow_delegation=False
)

verifier = Agent(
    role="Financial Document Verifier",
    goal="Verify and validate financial documents for accuracy and completeness",
    verbose=True,
    memory=True,
    backstory=(
        "You are a document verification specialist with expertise in financial reporting standards."
    ),
    allow_delegation=False
)
