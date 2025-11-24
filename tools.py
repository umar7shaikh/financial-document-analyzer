import os
import pypdf
import requests
import json
from dotenv import load_dotenv

load_dotenv()

class FinancialDocumentTool:
    """Enhanced financial document reader with better error handling"""
    
    @staticmethod
    def read_data_tool(path: str = 'data/sample.pdf') -> str:
        """Read PDF content and format for financial analysis"""
        try:
            print("I am in the read data,the path is ",(path))

            if not os.path.exists(path):
                return f"Error: File not found at path: {path}"
            
            with open(path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                full_report = ""
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    try:
                        page_content = page.extract_text()
                        if page_content.strip():
                            # Clean and format content
                            while "\n\n" in page_content:
                                page_content = page_content.replace("\n\n", "\n")
                            full_report += f"\n--- Page {page_num} ---\n{page_content}\n"
                    except Exception as e:
                        full_report += f"\n--- Page {page_num} (Reading Error: {str(e)}) ---\n"
                
                if not full_report.strip():
                    return "Error: No readable text found in PDF"
                
                
                
                # Add document metadata
                metadata = f"""
Document Analysis Summary:
- Total Pages: {len(pdf_reader.pages)}
- File Path: {path}
- Content Length: {len(full_report)} characters
- Processing Status: Successfully extracted text content

Financial Document Content:
{full_report}
"""
                return metadata
                
        except Exception as e:
            return f"Error reading PDF: {str(e)}"


def search_web(query: str) -> str:
    """Search the web using Serper API - simple function version"""
    try:
        api_key = os.getenv("SERPER_API_KEY")
        
        if not api_key:
            return "Error: SERPER_API_KEY not configured in environment variables"
        
        url = "https://google.serper.dev/search"
        payload = json.dumps({"q": query, "num": 5})
        headers = {
            'X-API-KEY': api_key,
            'Content-Type': 'application/json'
        }
        
        response = requests.post(url, headers=headers, data=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            results = []
            
            # Extract organic results
            if 'organic' in data:
                for result in data['organic'][:5]:
                    title = result.get('title', 'No title')
                    link = result.get('link', 'No link')
                    snippet = result.get('snippet', 'No description')
                    results.append(f"Title: {title}\nURL: {link}\nDescription: {snippet}\n")
            
            if results:
                return f"Search Results for '{query}':\n\n" + "\n" + "="*50 + "\n".join(results)
            else:
                return f"No search results found for query: {query}"
        else:
            return f"Search API returned error code: {response.status_code}"
            
    except Exception as e:
        return f"Search error occurred: {str(e)}"
    
    
