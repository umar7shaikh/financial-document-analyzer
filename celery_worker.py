import os
import sys
from celery import Celery
import time
from database.models import AnalysisModel

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure Celery with Redis
celery_app = Celery('financial_analyzer')
celery_app.config_from_object({
    'broker_url': 'redis://localhost:6379/0',
    'result_backend': 'redis://localhost:6379/0',
    'task_serializer': 'json',
    'accept_content': ['json'],
    'result_serializer': 'json',
    'timezone': 'UTC',
    'enable_utc': True,
})

@celery_app.task(bind=True)
def process_financial_document(self, query: str, file_path: str, analysis_id: str):
    """Complete database integration with proper CrewAI result extraction"""
    
    # 1. Create initial analysis record
    try:
        document_name = os.path.basename(file_path) if file_path else "unknown.pdf"
        document_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        
        record = AnalysisModel.create_analysis_record(
            job_id=analysis_id,
            user_id=1,
            document_path=file_path,
            document_name=document_name
        )
        print(f"📝 Created initial analysis record: {record}")
        
    except Exception as db_error:
        print(f"❌ Failed to create initial record: {db_error}")
        # Continue anyway - don't let DB issues stop the analysis
    
    # 2. Update status to processing
    try:
        AnalysisModel.update_analysis_status(analysis_id, 'processing')
        print(f"🔄 Updated status to processing for {analysis_id}")
    except Exception as e:
        print(f"⚠️ Status update failed: {e}")
    
    start_time = time.time()
    
    try:
        print(f"🚀 Starting CrewAI analysis for job {analysis_id}")
        
        # Update task state
        self.update_state(state='PROGRESS', meta={'status': 'Processing with CrewAI agents'})
        
        # Import and run CrewAI function
        from main import run_financial_crew
        result = run_financial_crew(query, file_path)
        
        # ✅ PROPER CrewAI RESULT EXTRACTION
        print(f"🔍 CrewAI result type: {type(result)}")
        
        # Extract results based on CrewAI structure
        if hasattr(result, 'raw'):
            full_report = str(result.raw)
            print(f"📄 Using result.raw: {len(full_report)} characters")
            # Add this after getting the CrewAI result:
            print(f"🔍 ACTUAL CONTENT PREVIEW:")
            print(f"{'='*50}")
            print(f"{full_report[:1000]}...")  # First 1000 characters
            print(f"{'='*50}")

            # Find all possible headers
            import re
            headers = re.findall(r'(##[^\n]+|#[^\n]+|\*\*[^\n]+\*\*)', full_report)
            print(f"📋 Found headers: {headers[:10]}")  # First 10 headers

            
            # Try to extract individual task outputs if available
            if hasattr(result, 'tasks_output') and result.tasks_output:
                try:
                    market_research = str(result.tasks_output[0].raw) if len(result.tasks_output) > 0 else ""
                    financial_analysis = str(result.tasks_output[1].raw) if len(result.tasks_output) > 1 else ""
                    verification_report = str(result.tasks_output[2].raw) if len(result.tasks_output) > 2 else ""
                    print(f"📊 Individual task outputs extracted successfully")
                except Exception as e:
                    print(f"⚠️ Could not extract individual tasks: {e}")
                    market_research = ""
                    financial_analysis = ""
                    verification_report = ""
            else:
                market_research = ""
                financial_analysis = ""
                verification_report = ""
                
        elif hasattr(result, 'tasks_output') and result.tasks_output:
            # Extract individual task outputs
            market_research = str(result.tasks_output[0].raw) if len(result.tasks_output) > 0 else ""
            financial_analysis = str(result.tasks_output[1].raw) if len(result.tasks_output) > 1 else ""
            verification_report = str(result.tasks_output[2].raw) if len(result.tasks_output) > 2 else ""
            full_report = f"{market_research}\n\n--- FINANCIAL ANALYSIS ---\n\n{financial_analysis}\n\n--- VERIFICATION REPORT ---\n\n{verification_report}"
            print(f"📄 Using tasks_output: {len(full_report)} characters")
            
        else:
            full_report = str(result)
            market_research = extract_section(full_report, 'market research')
            financial_analysis = extract_section(full_report, 'financial analysis')
            verification_report = extract_section(full_report, 'verification')
            print(f"📄 Using str(result): {len(full_report)} characters")
        
        # Calculate processing duration
        processing_duration = time.time() - start_time
        
        # ✅ STRUCTURED DATA EXTRACTION
        analysis_data = {
            'market_research': market_research or extract_section(full_report, 'market research'),
            'financial_analysis': financial_analysis or extract_section(full_report, 'financial analysis'),
            'investment_recommendation': extract_section(full_report, 'investment recommendation'),
            'risk_assessment': extract_section(full_report, 'risk assessment'),
            'verification_report': verification_report or extract_section(full_report, 'verification'),
            'full_report': full_report,  # Complete actual result
            'confidence_rating': extract_confidence_rating(full_report) or 'HIGH'
        }
        
        print(f"📊 Extracted sections:")
        print(f"   Market research: {len(analysis_data['market_research'])} chars")
        print(f"   Financial analysis: {len(analysis_data['financial_analysis'])} chars")
        print(f"   Investment recommendation: {len(analysis_data['investment_recommendation'])} chars")
        print(f"   Risk assessment: {len(analysis_data['risk_assessment'])} chars")
        print(f"   Verification report: {len(analysis_data['verification_report'])} chars")
        print(f"   Full report: {len(analysis_data['full_report'])} chars")
        
        # Save to database
        try:
            rows_updated = AnalysisModel.store_complete_analysis(analysis_id, analysis_data, processing_duration)
            if rows_updated > 0:
                print(f"💾 Successfully saved complete analysis to database")
            else:
                print(f"⚠️ No rows updated - analysis might not have been saved")
                
        except Exception as db_error:
            print(f"❌ Database save error: {db_error}")
        
        # Verify the data was actually saved
        try:
            saved_record = AnalysisModel.get_analysis_by_job_id(analysis_id)
            if saved_record:
                print(f"✅ VERIFIED: Analysis {analysis_id} saved with status: {saved_record['status']}")
                print(f"📊 Database record contains {len(saved_record.get('full_analysis_report', ''))} characters")
            else:
                print(f"❌ VERIFICATION FAILED: Analysis {analysis_id} NOT found in database!")
        except Exception as e:
            print(f"❌ Database verification error: {e}")
        
        print(f"✅ Analysis completed successfully for job {analysis_id}")
        
        # Clean up file
        if os.path.exists(file_path):
            os.remove(file_path)
            
        return {
            "status": "completed", 
            "analysis": analysis_data['full_report'],  # Return the extracted content
            "analysis_id": analysis_id,
            "processing_time": processing_duration
        }
        
    except Exception as e:
        processing_duration = time.time() - start_time
        error_message = str(e)
        
        # Update database with error
        try:
            AnalysisModel.update_analysis_status(analysis_id, 'failed', error_message)
            print(f"💾 Updated database with failure status")
        except Exception as db_error:
            print(f"❌ Failed to update error status: {db_error}")
        
        print(f"❌ Analysis failed for job {analysis_id}: {error_message}")
        
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        
        self.update_state(state='FAILURE', meta={'error': error_message})
        raise

def extract_section(text, section_name):
    """Enhanced section extraction with more patterns"""
    if not text or not section_name:
        return ""
    
    try:
        text_lower = text.lower()
        section_lower = section_name.lower()
        
        # Expanded search patterns for different header formats
        start_markers = [
            f"## {section_lower}",
            f"# {section_lower}",  
            f"**{section_lower}",
            f"{section_lower}:",
            f"{section_lower} report",
            f"{section_lower} analysis", 
            f"--- {section_lower}",
            f"**{section_lower.title()}**",
            f"# {section_lower.title()}",
            # More specific patterns for investment/risk
            f"investment recommendation",
            f"investment advice", 
            f"recommended investment",
            f"risk analysis",
            f"risk evaluation",
            f"risk factors",
            # Try without spaces
            section_lower.replace(' ', ''),
            # Try with underscores  
            section_lower.replace(' ', '_'),
        ]
        
        start_pos = -1
        used_marker = ""
        for marker in start_markers:
            pos = text_lower.find(marker)
            if pos != -1:
                start_pos = pos
                used_marker = marker
                break
        
        if start_pos == -1:
            # If no exact match, try partial matching
            for marker in [section_lower[:10], section_lower.split(' ')[0]]:
                pos = text_lower.find(marker)
                if pos != -1:
                    start_pos = pos
                    used_marker = marker
                    break
        
        if start_pos == -1:
            return ""
        
        # Find section end
        end_markers = ['##', '#', '**', '---', '\n\n']
        end_pos = len(text)
        
        for marker in end_markers:
            pos = text.find(marker, start_pos + len(used_marker) + 10)
            if pos != -1 and pos < end_pos:
                end_pos = pos
        
        extracted = text[start_pos:end_pos].strip()
        
        # Return if substantial content
        if len(extracted) > len(used_marker) + 30:
            return extracted
        else:
            return ""
            
    except Exception as e:
        print(f"⚠️ Section extraction error for '{section_name}': {e}")
        return ""

def extract_confidence_rating(text):
    """Extract confidence rating from verification report"""
    if not text:
        return 'HIGH'
    
    try:
        text_upper = text.upper()
        
        # Look for explicit confidence ratings
        if ('HIGH' in text_upper and ('CONFIDENCE' in text_upper or 'RATING' in text_upper)) or \
           'HIGH CONFIDENCE' in text_upper or 'CONFIDENCE: HIGH' in text_upper:
            return 'HIGH'
        elif ('MEDIUM' in text_upper and ('CONFIDENCE' in text_upper or 'RATING' in text_upper)) or \
             'MEDIUM CONFIDENCE' in text_upper or 'CONFIDENCE: MEDIUM' in text_upper:
            return 'MEDIUM'
        elif ('LOW' in text_upper and ('CONFIDENCE' in text_upper or 'RATING' in text_upper)) or \
             'LOW CONFIDENCE' in text_upper or 'CONFIDENCE: LOW' in text_upper:
            return 'LOW'
        else:
            # Default to HIGH for successful analyses
            return 'HIGH'
            
    except Exception as e:
        print(f"⚠️ Confidence rating extraction error: {e}")
        return 'HIGH'

if __name__ == '__main__':
    print("🔧 Starting Enhanced Celery Worker with Database Integration...")
    print("📊 CrewAI Result Extraction Enabled")
    print("💾 PostgreSQL Database Integration Active")
    celery_app.worker_main(['worker', '--loglevel=info'])
