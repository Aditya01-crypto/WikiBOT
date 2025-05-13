import string
import wikipediaapi
from summarizer import summarize_wikipedia as summarize
import re
from typing import Dict, Union

def clean_text(text: str) -> str:
    """
    Clean text by removing excessive spaces, control characters, and invalid unicode.
    Returns: Cleaned text string
    """
    if not text:
        return ""
    
    # Remove control characters and weird unicode
    text = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Remove random character sequences (like "0 | } A J k")
    text = re.sub(r'[^a-zA-Z0-9\s.,;:!?\'"()-]', '', text)
    
    return text

def fetch_wikipedia_content(topic: str) -> Union[str, Dict[str, str]]:
    """
    Fetch and clean Wikipedia content with robust error handling.
    Returns: Cleaned content or error message
    """
    try:
        # Clean the topic name
        clean_topic = topic.translate(str.maketrans('', '', string.punctuation)).strip().title()
        if not clean_topic:
            return "Error: Empty topic after cleaning"
        
        # Initialize Wikipedia API with timeout
        wiki_wiki = wikipediaapi.Wikipedia(
            language='en',
            user_agent='WikiBot/1.0',
            extract_format=wikipediaapi.ExtractFormat.WIKI,  # Simplified format
            timeout=10  # 10 second timeout
        )
        
        page = wiki_wiki.page(clean_topic)
        if not page.exists():
            return f"Error: Wikipedia page for '{clean_topic}' not found"
        
        # Get and clean content
        content = page.text
        content = clean_text(content)
        
        # Ensure we have valid content
        if not content or len(content.split()) < 10:
            return "Error: Retrieved content is too short or invalid"
            
        return content
    
    except Exception as e:
        return f"Error fetching content: {str(e)}"

def truncate_content(content: str, max_length: int) -> str:
    """Safely truncate content at sentence boundary"""
    if len(content) <= max_length:
        return content
    
    truncated = content[:max_length]
    last_period = truncated.rfind('.')
    return truncated[:last_period + 1] if last_period > 0 else truncated

def generate_wikipedia_summary(topic: str, max_input_length: int = 15000, summary_length: int = 300) -> Dict[str, Union[str, int]]:
    """Generate cleaned Wikipedia content and summary."""
    content = fetch_wikipedia_content(topic)
    
    if isinstance(content, str) and content.startswith("Error"):
        return {"error": content}
    
    # Clean and truncate original content for display
    display_content = truncate_content(content, 25000)
    
    # Prepare content for summarization (respect max_input_length)
    summary_content = truncate_content(content, max_input_length)
    
    # Generate summary with specified length
    try:
        summary = summarize(summary_content, max_summary_length=summary_length)
        summary = clean_text(summary)
    except Exception as e:
        summary = f"Error generating summary: {str(e)}"
    
    return {
        "original_content": display_content,
        "summary": summary,
        "content_length": len(display_content),
        "word_count": len(display_content.split())
    }

if __name__ == "__main__":
    # Command-line interface for testing
    topic = input("Enter the topic to search: ")
    try:
        max_input = int(input("Enter max content size for summarization (characters): "))
    except ValueError:
        max_input = 10000
    
    result = generate_wikipedia_summary(topic, max_input_length=max_input)
    
    if "error" in result:
        print(result["error"])
    else:
        print(f"\nWikipedia content for {topic}:")
        print(f"Length: {result['content_length']} chars, {result['word_count']} words")
        print("\nFirst 500 characters:")
        print(result["original_content"][:500] + "...")
        print("\nSummary:")
        print(result["summary"])
