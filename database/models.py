from database.connection import db_manager
import logging

logger = logging.getLogger(__name__)

class AnalysisModel:
    @staticmethod
    def create_analysis_record(job_id, user_id, document_path, document_name):
        """Create initial analysis record when job starts"""
        query = """
            INSERT INTO financial_analyses 
            (job_id, user_id, document_path, document_name, status)
            VALUES (%s, %s, %s, %s, 'pending')
            RETURNING analysis_id, job_id
        """
        
        with db_manager.get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (job_id, user_id, document_path, document_name))
                result = cur.fetchone()
                conn.commit()
                return result
    
    @staticmethod
    def update_analysis_status(job_id, status, error_message=None):
        """Update job status (pending -> processing -> completed/failed)"""
        query = """
            UPDATE financial_analyses 
            SET status = %s, error_message = %s, updated_at = CURRENT_TIMESTAMP
            WHERE job_id = %s
        """
        
        with db_manager.get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (status, error_message, job_id))
                conn.commit()
                return cur.rowcount
    
    @staticmethod
    def store_complete_analysis(job_id, analysis_data, processing_duration):
        """Store the COMPLETE analysis results (this prevents truncation!)"""
        query = """
            UPDATE financial_analyses 
            SET 
                market_research_summary = %s,
                financial_metrics_analysis = %s,
                investment_recommendation = %s,
                risk_assessment = %s,
                verification_report = %s,
                full_analysis_report = %s,
                confidence_rating = %s,
                status = 'completed',
                processing_duration = %s,
                completed_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE job_id = %s
        """
        
        with db_manager.get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (
                    analysis_data.get('market_research', ''),
                    analysis_data.get('financial_analysis', ''),
                    analysis_data.get('investment_recommendation', ''),
                    analysis_data.get('risk_assessment', ''),
                    analysis_data.get('verification_report', ''),
                    analysis_data.get('full_report', ''),  # Complete untruncated version!
                    analysis_data.get('confidence_rating', ''),
                    processing_duration,
                    job_id
                ))
                conn.commit()
                return cur.rowcount
    
    @staticmethod
    def get_analysis_by_job_id(job_id):
        """Get complete analysis results"""
        query = "SELECT * FROM financial_analyses WHERE job_id = %s"
        
        with db_manager.get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (job_id,))
                return cur.fetchone()
