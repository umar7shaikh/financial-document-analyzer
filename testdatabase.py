from database.models import AnalysisModel

def test_database():
    """Test if database integration works"""
    
    # FIRST: Create a test user
    import psycopg2
    from database.connection import db_manager
    
    with db_manager.get_db_connection() as conn:
        with conn.cursor() as cur:
            # Insert a test user
            cur.execute("""
                INSERT INTO users (username, email, hashed_password, first_name, last_name)
                VALUES ('testuser', 'test@example.com', 'hashed_password_123', 'Test', 'User')
                ON CONFLICT (username) DO NOTHING
                RETURNING user_id
            """)
            result = cur.fetchone()
            if result:
                user_id = result['user_id']
                print(f"✅ Created test user with ID: {user_id}")
            else:
                # User already exists, get the ID
                cur.execute("SELECT user_id FROM users WHERE username = 'testuser'")
                user_id = cur.fetchone()['user_id']
                print(f"✅ Using existing test user with ID: {user_id}")
            
            conn.commit()
    
    # NOW: Test creating analysis record with the actual user_id
    job_id = "test_12345"
    analysis = AnalysisModel.create_analysis_record(
        job_id=job_id,
        user_id=user_id,  # Use the real user_id
        document_path="data/test.pdf",
        document_name="test_document.pdf"
    )
    print(f"✅ Created analysis record: {analysis}")
    
    # Test updating status
    AnalysisModel.update_analysis_status(job_id, 'processing')
    print("✅ Updated status to processing")
    
    # Test storing results
    fake_analysis_data = {
        'market_research': 'This is market research data...',
        'financial_analysis': 'This is financial analysis data...',
        'verification_report': 'This is verification report...',
        'full_report': 'This is the COMPLETE full report without truncation...',
        'confidence_rating': 'HIGH'
    }
    
    AnalysisModel.store_complete_analysis(job_id, fake_analysis_data, 15.5)
    print("✅ Stored complete analysis")
    
    # Test retrieving results
    saved_analysis = AnalysisModel.get_analysis_by_job_id(job_id)
    print(f"✅ Retrieved analysis: Status = {saved_analysis['status']}")
    print(f"📄 Full report length: {len(saved_analysis['full_analysis_report'])} characters")

if __name__ == "__main__":
    test_database()
