from fastapi import FastAPI, File, UploadFile, Form, HTTPException
import os
import uuid
from datetime import datetime
from crewai import Crew, Process
from agents import market_researcher, financial_analyst, verifier
from task import market_research_task, analyze_financial_document, verification
from tools import FinancialDocumentTool

app = FastAPI(
    title="Enhanced Financial Document Analyzer - CrewAI Multi-Agent System", 
    version="3.0.0",
    description="Professional financial document analysis using CrewAI multi-agent system with real-time market research"
)

def run_financial_crew(query: str, file_path: str):
    """Run the complete CrewAI workflow with market research and document analysis"""
    
    try:
        # Create the financial analysis crew
        financial_crew = Crew(
            agents=[market_researcher, financial_analyst, verifier],
            tasks=[market_research_task, analyze_financial_document, verification],
            process=Process.sequential,
            verbose=True,
            memory=False  # Changed from True to False
        )
        
        # Execute the crew with context
        inputs = {
            'query': query,
            'file_path': file_path
        }
        
        result = financial_crew.kickoff(inputs)
        return result
        
    except Exception as e:
        raise Exception(f"CrewAI execution error: {str(e)}")

@app.get("/")
async def root():
    """API information and health check"""
    return {
        "message": "🚀 Enhanced Financial Document Analyzer - CrewAI Multi-Agent System",
        "status": "✅ Fully Operational",
        "version": "3.0.0",
        "features": [
            "🤖 Multi-Agent CrewAI System (3 specialized agents)",
            "🔍 Real-time Market Research with SerperDevTool",
            "🧠 Free Hugging Face LLM Integration (Llama-3.2-3B)",
            "📊 Comprehensive Financial Document Analysis",
            "✅ Document Verification & Quality Control",
            "💰 100% Free Tier Compatible"
        ],
        "agents": [
            {
                "name": "Market Research Specialist",
                "role": "Gathers current market data and economic indicators"
            },
            {
                "name": "Senior Financial Analyst", 
                "role": "Combines document analysis with market research"
            },
            {
                "name": "Document Verifier",
                "role": "Quality control and validation of analysis"
            }
        ],
        "endpoints": [
            {
                "path": "/analyze",
                "method": "POST", 
                "description": "Upload PDF and get comprehensive financial analysis"
            }
        ]
    }

@app.post("/analyze")
async def analyze_financial_document_endpoint(
    file: UploadFile = File(..., description="PDF financial document to analyze"),
    query: str = Form(
        default="Provide comprehensive financial analysis with current market context and investment recommendations",
        description="Specific analysis question or request"
    )
):
    """
    Enhanced financial analysis with CrewAI multi-agent system
    
    Uploads a PDF financial document and returns comprehensive analysis including:
    - Market research and current trends
    - Detailed financial metrics analysis
    - Investment recommendations
    - Risk assessment
    - Document verification
    """
    
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400, 
            detail="Only PDF files are supported. Please upload a PDF document."
        )
    
    # Generate unique file ID
    file_id = str(uuid.uuid4())
    file_path = f"data/financial_document_{file_id}.pdf"
    
    try:
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        
        # Save uploaded file
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Validate query
        if not query or query.strip() == "":
            query = "Provide comprehensive financial analysis with current market context and investment recommendations"
        
        # Extract PDF content for preview (optional)
        doc_tool = FinancialDocumentTool()
        pdf_preview = doc_tool.read_data_tool(file_path)
        
        # Run the CrewAI workflow
        print(f"Starting CrewAI analysis for query: {query}")
        analysis_result = run_financial_crew(query.strip(), file_path)
        
        return {
            "status": "✅ SUCCESS - CrewAI Multi-Agent Analysis Complete",
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "file_processed": file.filename,
            "file_size_mb": round(len(content) / (1024*1024), 2),
            "analysis": str(analysis_result),
            "system_details": {
                "framework": "CrewAI Multi-Agent System",
                "agents_executed": [
                    "Market Research Specialist",
                    "Senior Financial Analyst", 
                    "Document Verifier"
                ],
                "tools_integrated": [
                    "SerperDevTool (Web Search)",
                    "FinancialDocumentTool (PDF Reader)"
                ],
                "llm_model": "Hugging Face Llama-3.2-3B-Instruct",
                "process_type": "Sequential Agent Workflow",
                "features": [
                    "Real-time market research",
                    "Document analysis", 
                    "Quality verification",
                    "Investment recommendations"
                ]
            },
            "processing_metrics": {
                "pdf_pages_processed": len(content) // 2000,  # Rough estimate
                "characters_in_document": len(pdf_preview) if 'Error' not in pdf_preview else 0,
                "agents_executed": 3,
                "tasks_completed": 3,
                "total_cost": "$0.00 (Free Tier)",
                "processing_time": "Variable (depends on document complexity)"
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Analysis processing error: {str(e)}"
        )
    
    finally:
        # Clean up uploaded file
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as cleanup_error:
                print(f"Warning: Could not cleanup file {file_path}: {cleanup_error}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Financial Document Analyzer",
        "version": "3.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Enhanced Financial Document Analyzer...")
    print("📊 CrewAI Multi-Agent System Ready!")
    print("🔍 Market Research & Document Analysis Available")
    print("💰 Running on Free Tier (HuggingFace + Serper)")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
