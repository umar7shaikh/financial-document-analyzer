from fastapi import FastAPI, File, UploadFile, Form, HTTPException
import uuid
import os
from datetime import datetime

# Add database imports
from database.models import AnalysisModel

# Import your existing functions
from agents import market_researcher, financial_analyst, verifier  
from task import market_research_task, analyze_financial_document, verification
from crewai import Crew, Process

app = FastAPI(
    title="Enhanced Financial Document Analyzer - Celery + Redis System", 
    version="4.1.0",
    description="Professional financial document analysis using CrewAI multi-agent system with Celery + Redis for concurrent processing"
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
            memory=False
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
        "message": "🚀 Enhanced Financial Document Analyzer - Celery + Redis System",
        "status": "✅ Fully Operational",
        "version": "4.1.0", 
        # ... rest of your existing code
    }

@app.post("/analyze")
async def analyze_financial_document_queue(
    file: UploadFile = File(..., description="PDF financial document to analyze"),
    query: str = Form(
        default="Provide comprehensive financial analysis with current market context and investment recommendations",
        description="Specific analysis question or request"
    )
):
    """Queue financial analysis for background processing using Celery"""
    
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400, 
            detail="Only PDF files are supported. Please upload a PDF document."
        )
    
    # Generate unique job ID
    job_id = str(uuid.uuid4())[:8]
    file_path = f"data/financial_document_{job_id}.pdf"
    
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
        
        # 🆕 CREATE DATABASE RECORD FIRST
        try:
            db_record = AnalysisModel.create_analysis_record(
                job_id=job_id,
                user_id=1,
                document_path=file_path,
                document_name=file.filename
                # ✅ Removed document_size parameter
            )
            print(f"📝 Created database record: {db_record}")
        except Exception as db_error:
            print(f"❌ Database record creation failed: {db_error}")
            # Don't fail the entire request, but log the error
        
        # Import and queue the Celery task
        from celery_worker import process_financial_document
        task = process_financial_document.delay(query.strip(), file_path, job_id)
        
        return {
            "🎯 job_id": job_id,  # Use our job_id, not task.id
            "📄 file_processed": file.filename,
            "💾 file_size_mb": round(len(content) / (1024*1024), 2),
            "⏱️ status": "queued",
            "🚀 message": "Analysis queued with Celery + Redis for background processing!",
            "⏰ estimated_time": "5-15 minutes",
            "🔍 check_status": f"/status/{job_id}",
            "database_record": "created" if 'db_record' in locals() else "failed",
            "system_info": {
                "queue_system": "Celery + Redis (Windows Compatible)",
                "processing_type": "Background/Asynchronous",
                "agents": ["Market Research", "Financial Analysis", "Verification"],
                "concurrent_support": True
            },
            "next_steps": [
                f"1. Check status: GET /status/{job_id}",
                "2. Results will include comprehensive analysis when complete"
            ]
        }
        
    except Exception as e:
        # Clean up file if job queuing fails
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to queue analysis: {str(e)}"
        )

@app.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """Check the status and results of a queued analysis job"""
    
    try:
        # 🆕 CHECK DATABASE FIRST
        try:
            db_record = AnalysisModel.get_analysis_by_job_id(job_id)
            if db_record:
                db_status = db_record['status']
                
                # If completed, return database results
                if db_status == 'completed':
                    return {
                        "🎯 job_id": job_id,
                        "⏱️ status": "completed",
                        "✅ message": "Analysis completed successfully!",
                        "📊 analysis_result": {
                            "market_research": db_record['market_research_summary'],
                            "financial_analysis": db_record['financial_metrics_analysis'],
                            "investment_recommendation": db_record['investment_recommendation'],
                            "risk_assessment": db_record['risk_assessment'],
                            "verification_report": db_record['verification_report'],
                            "full_report": db_record['full_analysis_report'],
                            "confidence_rating": db_record['confidence_rating']
                        },
                        "processing_summary": {
                            "processing_duration": float(db_record['processing_duration']) if db_record['processing_duration'] else None,
                            "completed_at": db_record['completed_at'].isoformat() if db_record['completed_at'] else None,
                            "agents_executed": 3,
                            "tasks_completed": 3,
                            "analysis_type": "Comprehensive Financial Analysis"
                        }
                    }
                
                elif db_status == 'failed':
                    return {
                        "🎯 job_id": job_id,
                        "⏱️ status": "failed",
                        "❌ message": "Analysis failed",
                        "🐛 error_details": db_record.get('error_message', 'Unknown error'),
                        "retry_suggestion": "You can upload the document again for retry"
                    }
                
                else:
                    return {
                        "🎯 job_id": job_id,
                        "⏱️ status": db_status,
                        "🔄 message": f"Analysis {db_status}... CrewAI agents working",
                        "🤖 current_stage": "Multi-agent processing",
                        "agents_active": ["Market Research", "Financial Analysis", "Verification"]
                    }
            
        except Exception as db_error:
            print(f"Database status check failed: {db_error}")
        
        # Fallback to Celery status if database check fails
        from celery_worker import celery_app
        result = celery_app.AsyncResult(job_id)
        
        # Build status response based on Celery task state
        status_info = {
            "🎯 job_id": job_id,
            "⏱️ status": result.state.lower(),
        }
        
        if result.state == 'PENDING':
            status_info.update({
                "📋 message": "Task is waiting in queue...",
                "queue_info": "Analysis will start automatically"
            })
            
        elif result.state == 'PROGRESS':
            status_info.update({
                "🔄 message": "Analysis in progress... CrewAI agents working",
                "🤖 current_stage": "Multi-agent processing",
                "agents_active": ["Market Research", "Financial Analysis", "Verification"],
                "progress_info": result.info
            })
            
        elif result.state == 'SUCCESS':
            status_info.update({
                "✅ message": "Analysis completed successfully!",
                "📊 analysis_result": result.result,
                "processing_summary": {
                    "agents_executed": 3,
                    "tasks_completed": 3,
                    "analysis_type": "Comprehensive Financial Analysis"
                }
            })
            
        elif result.state == 'FAILURE':
            status_info.update({
                "❌ message": "Analysis failed",
                "🐛 error_details": str(result.info),
                "retry_suggestion": "You can upload the document again for retry"
            })
        
        else:
            status_info["🔄 message"] = f"Task state: {result.state}"
        
        return status_info
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error checking job status: {str(e)}"
        )

# Keep your existing health_check endpoint as is
@app.get("/health")
async def health_check():
    # ... your existing health check code
    pass

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Enhanced Financial Document Analyzer with Celery + Redis...")
    print("📊 CrewAI Multi-Agent System Ready!")
    print("🔄 Celery Queue System for Concurrent Processing (Windows Compatible)")
    print("🔍 Market Research & Document Analysis Available")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
