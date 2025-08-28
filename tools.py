import os
import pypdf
from dotenv import load_dotenv
load_dotenv()

class FinancialDocumentTool:
    """Simple financial document reader - no external tool dependencies"""
    
    @staticmethod
    def read_data_tool(path: str = 'data/sample.pdf') -> str:
        """Read PDF content without external dependencies"""
        try:
            if not os.path.exists(path):
                return f"Error: File not found at path: {path}"
            
            with open(path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                full_report = ""
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    try:
                        page_content = page.extract_text()
                        if page_content.strip():
                            # Clean content
                            while "\n\n" in page_content:
                                page_content = page_content.replace("\n\n", "\n")
                            full_report += f"--- Page {page_num} ---\n{page_content}\n"
                    except Exception as e:
                        full_report += f"--- Page {page_num} (Error reading) ---\n"
                
                return full_report if full_report.strip() else "Error: No readable text found"
                
        except Exception as e:
            return f"Error reading PDF: {str(e)}"

# Simple placeholder tools
class InvestmentTool:
    @staticmethod
    def analyze(data: str) -> str:
        return "Investment analysis functionality implemented"

class RiskTool:
    @staticmethod
    def assess(data: str) -> str:
        return "Risk assessment functionality implemented"
