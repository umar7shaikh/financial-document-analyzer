from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uuid
import os
import time
from datetime import datetime

# Add database imports
from database.models import AnalysisModel
from database.connection import db_manager

# Import your existing functions
from agents import market_researcher, financial_analyst, verifier  
from task import market_research_task, analyze_financial_document, verification
from crewai import Crew, Process

app = FastAPI(
    title="Enhanced Financial Document Analyzer - Hybrid System", 
    version="4.2.0",
    description="Professional financial document analysis using CrewAI multi-agent system with optional Celery + Redis for concurrent processing"
)

# ✅ AUTO-CREATE DATABASE TABLES ON STARTUP
@app.on_event("startup")
async def startup_event():
    """Create database tables on startup if they don't exist"""
    try:
        with db_manager.get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS financial_analyses (
                        id SERIAL PRIMARY KEY,
                        job_id VARCHAR(255) UNIQUE NOT NULL,
                        user_id INTEGER,
                        document_path VARCHAR(500),
                        document_name VARCHAR(255),
                        status VARCHAR(50) DEFAULT 'pending',
                        market_research_summary TEXT,
                        financial_metrics_analysis TEXT,
                        investment_recommendation TEXT,
                        risk_assessment TEXT,
                        verification_report TEXT,
                        full_analysis_report TEXT,
                        confidence_rating VARCHAR(20),
                        processing_duration NUMERIC,
                        error_message TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        completed_at TIMESTAMP
                    );
                """)
                conn.commit()
                print("✅ Database tables verified/created successfully")
    except Exception as e:
        print(f"⚠️ Database setup warning: {e}")

# ✅ CORS MIDDLEWARE - Updated with production URLs
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        FRONTEND_URL,  # Production frontend URL
        "*"  # Remove in production after testing
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔀 HYBRID MODE TOGGLE
USE_CELERY = os.getenv("USE_CELERY", "false").lower() == "true"

def run_financial_crew(query: str, file_path: str):
    """Run the complete CrewAI workflow with market research and document analysis"""
    
    try:
        financial_crew = Crew(
            agents=[market_researcher, financial_analyst, verifier],
            tasks=[market_research_task, analyze_financial_document, verification],
            process=Process.sequential,
            verbose=True,
            memory=False
        )
        
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
        "message": "🚀 Enhanced Financial Document Analyzer - Hybrid System",
        "status": "✅ Fully Operational",
        "version": "4.2.0",
        "processing_mode": "Async (Celery)" if USE_CELERY else "Sync (Direct)",
        "features": {
            "multi_agent_analysis": True,
            "market_research": True,
            "financial_metrics": True,
            "investment_recommendations": True,
            "risk_assessment": True,
            "verification": True
        },
        "endpoints": {
            "analyze": "/analyze (POST)",
            "status": "/status/{job_id} (GET)",
            "health": "/health (GET)",
            "docs": "/docs"
        }
    }

@app.post("/analyze")
async def analyze_financial_document_queue(
    file: UploadFile = File(..., description="PDF financial document to analyze"),
    query: str = Form(
        default="Provide comprehensive financial analysis with current market context and investment recommendations",
        description="Specific analysis question or request"
    )
):
    """Process financial analysis - async (Celery) or sync mode based on USE_CELERY env var"""
    
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
        
        # 🆕 CREATE DATABASE RECORD
        try:
            db_record = AnalysisModel.create_analysis_record(
                job_id=job_id,
                user_id=1,
                document_path=file_path,
                document_name=file.filename
            )
            print(f"📝 Created database record: {db_record}")
        except Exception as db_error:
            print(f"❌ Database record creation failed: {db_error}")
        
        # 🔀 HYBRID MODE: Use Celery if enabled, otherwise process synchronously
        if USE_CELERY:
            # ===== ASYNC MODE: Queue with Celery =====
            try:
                from celery_worker import process_financial_document
                task = process_financial_document.delay(query.strip(), file_path, job_id)
                
                return {
                    "🎯 job_id": job_id,
                    "📄 file_processed": file.filename,
                    "💾 file_size_mb": round(len(content) / (1024*1024), 2),
                    "⏱️ status": "queued",
                    "🚀 message": "Analysis queued with Celery + Redis for background processing!",
                    "⏰ estimated_time": "5-15 minutes",
                    "🔍 check_status": f"/status/{job_id}",
                    "processing_mode": "async",
                    "next_steps": [
                        f"1. Check status: GET /status/{job_id}",
                        "2. Results will include comprehensive analysis when complete"
                    ]
                }
            except Exception as celery_error:
                print(f"❌ Celery queueing failed: {celery_error}")
                raise HTTPException(status_code=500, detail=f"Failed to queue analysis: {str(celery_error)}")
        
        else:
            # ===== SYNC MODE: Process immediately (no Celery) =====
            start_time = time.time()
            
            try:
                # Update status to processing
                AnalysisModel.update_analysis_status(job_id, 'processing')
                print(f"🔄 Processing synchronously: {job_id}")
                
                # Run CrewAI analysis
                result = run_financial_crew(query.strip(), file_path)
                
                # Extract results (same logic as celery_worker)
                full_report = str(result.raw) if hasattr(result, 'raw') else str(result)
                
                # Extract individual task outputs
                market_research = ""
                financial_analysis = ""
                verification_report = ""
                
                if hasattr(result, 'tasks_output') and result.tasks_output:
                    try:
                        market_research = str(result.tasks_output[0].raw) if len(result.tasks_output) > 0 else ""
                        financial_analysis = str(result.tasks_output[1].raw) if len(result.tasks_output) > 1 else ""
                        verification_report = str(result.tasks_output[2].raw) if len(result.tasks_output) > 2 else ""
                    except Exception as e:
                        print(f"⚠️ Could not extract individual tasks: {e}")
                
                # Import extraction functions from celery_worker
                from celery_worker import extract_section, extract_confidence_rating
                
                # Structure analysis data
                analysis_data = {
                    'market_research': market_research or extract_section(full_report, 'market research') or full_report[:500],
                    'financial_analysis': financial_analysis or extract_section(full_report, 'financial analysis') or extract_section(full_report, 'executive summary'),
                    'investment_recommendation': extract_section(financial_analysis or full_report, 'investment recommendation') or extract_section(financial_analysis or full_report, 'recommendation'),
                    'risk_assessment': extract_section(financial_analysis or full_report, 'risk assessment') or extract_section(financial_analysis or full_report, 'risk factors'),
                    'verification_report': verification_report or extract_section(full_report, 'verification') or "Analysis completed successfully.",
                    'full_report': full_report,
                    'confidence_rating': extract_confidence_rating(verification_report or full_report)
                }
                
                processing_duration = time.time() - start_time
                
                # Save to database
                try:
                    AnalysisModel.store_complete_analysis(job_id, analysis_data, processing_duration)
                    print(f"💾 Successfully saved analysis to database")
                except Exception as db_error:
                    print(f"❌ Database save error: {db_error}")
                
                # Clean up file
                if os.path.exists(file_path):
                    os.remove(file_path)
                
                return {
                    "🎯 job_id": job_id,
                    "📄 file_processed": file.filename,
                    "⏱️ status": "completed",
                    "✅ message": "Analysis completed successfully (synchronous mode)!",
                    "📊 analysis_result": {
                        "market_research": analysis_data['market_research'],
                        "financial_analysis": analysis_data['financial_analysis'],
                        "investment_recommendation": analysis_data['investment_recommendation'],
                        "risk_assessment": analysis_data['risk_assessment'],
                        "verification_report": analysis_data['verification_report'],
                        "confidence_rating": analysis_data['confidence_rating']
                    },
                    "⏰ processing_time": f"{processing_duration:.2f} seconds",
                    "processing_mode": "sync"
                }
                
            except Exception as processing_error:
                # Update database with error
                try:
                    AnalysisModel.update_analysis_status(job_id, 'failed', str(processing_error))
                except:
                    pass
                
                # Clean up file
                if os.path.exists(file_path):
                    os.remove(file_path)
                
                raise HTTPException(status_code=500, detail=f"Analysis failed: {str(processing_error)}")
        
    except HTTPException:
        raise
    except Exception as e:
        # Clean up file if anything fails
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to process analysis: {str(e)}"
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
                        "🔄 message": f"Analysis {db_status}...",
                        "🤖 current_stage": "Multi-agent processing"
                    }
            
        except Exception as db_error:
            print(f"Database status check failed: {db_error}")
        
        # Fallback to Celery status if database check fails (only if USE_CELERY)
        if USE_CELERY:
            try:
                from celery_worker import celery_app
                result = celery_app.AsyncResult(job_id)
                
                status_info = {
                    "🎯 job_id": job_id,
                    "⏱️ status": result.state.lower(),
                }
                
                if result.state == 'PENDING':
                    status_info["📋 message"] = "Task is waiting in queue..."
                elif result.state == 'PROGRESS':
                    status_info["🔄 message"] = "Analysis in progress..."
                elif result.state == 'SUCCESS':
                    status_info["✅ message"] = "Analysis completed successfully!"
                    status_info["📊 analysis_result"] = result.result
                elif result.state == 'FAILURE':
                    status_info["❌ message"] = "Analysis failed"
                    status_info["🐛 error_details"] = str(result.info)
                
                return status_info
            except:
                pass
        
        # Job not found
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error checking job status: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "version": "4.2.0",
        "processing_mode": "async (Celery)" if USE_CELERY else "sync (Direct)",
        "database": "unknown"
    }
    
    # Check database
    try:
        with db_manager.get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        health_status["database"] = "connected"
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
    
    # Check Redis (only if using Celery)
    if USE_CELERY:
        health_status["redis"] = "unknown"
        health_status["celery"] = "unknown"
        try:
            import redis
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            r = redis.from_url(redis_url)
            r.ping()
            health_status["redis"] = "connected"
        except Exception as e:
            health_status["redis"] = f"error: {str(e)}"
        
        try:
            from celery_worker import celery_app
            inspect = celery_app.control.inspect()
            stats = inspect.stats()
            health_status["celery"] = "running" if stats else "no workers"
        except Exception as e:
            health_status["celery"] = f"error: {str(e)}"
    
    return health_status

if __name__ == "__main__":
    import uvicorn
    mode = "Celery + Redis (Async)" if USE_CELERY else "Direct Processing (Sync)"
    print(f"🚀 Starting Enhanced Financial Document Analyzer...")
    print(f"📊 CrewAI Multi-Agent System Ready!")
    print(f"🔄 Processing Mode: {mode}")
    print(f"🔍 Market Research & Document Analysis Available")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
