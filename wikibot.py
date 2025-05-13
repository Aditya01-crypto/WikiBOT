
import string
import wikipediaapi
from summarizer import summarize_wikipedia as summarize
import random
import re

def fetch_wikipedia_content(topic):
    """
    Fetch content from Wikipedia using wikipedia-api and clean up excessive newlines.
    """
    clean_topic = topic.translate(str.maketrans('', '', string.punctuation)).strip().title()
    
    wiki_wiki = wikipediaapi.Wikipedia(language='en', user_agent='MyWikiBot/1.0 (https://mywikibot.local)')
    page = wiki_wiki.page(clean_topic)
    
    if not page.exists():
        return f"Error: Page '{clean_topic}' not found. Try a more specific topic."
    
    content = page.text

    # ✅ Replace multiple consecutive newlines with a single newline
    content = re.sub(r'\n+', '\n', content)

    return content

def truncate_at_nearest_period(text, limit):
    """
    Truncate text at the nearest period before the limit to avoid cutting sentences.
    """
    if len(text) <= limit:
        return text
    cut_index = text.rfind('.', 0, limit)  # Find last period before limit
    if cut_index == -1:  # No period found → fallback to hard cut
        return text[:limit]
    return text[:cut_index + 1]  # Include the period

def generate_wikipedia_summary_and_questions(topic, max_summary_length=None, max_summary_input_length=10000):  # ✅ renamed param
    """
    Generate a summary from Wikipedia content and generate flashcards.
    """
    content = fetch_wikipedia_content(topic)
    
    if "Error" in content:
        return content

    # Display content stats
    content_length = len(content)
    word_count = len(content.split())
    print(f"\n✅ Retrieved Wikipedia content: {content_length} characters, {word_count} words.")
    
    # ✅ Handle original content truncation for display: 25,000 characters (stop at nearest period)
    display_limit = 25000
    if content_length > display_limit:
        print(f"⚠️ Content exceeds {display_limit} characters. Truncating original content at nearest period before {display_limit}.")
        original_content = truncate_at_nearest_period(content, display_limit)
    else:
        original_content = content

    # ✅ For summarization, limit input to user-defined max_summary_input_length
    if content_length > max_summary_input_length:
        print(f"⚠️ Content exceeds {max_summary_input_length} characters. Truncating for summarization.")
        summary_content = content[:max_summary_input_length]
    else:
        summary_content = content
    
    # Decide summary length dynamically
    if not max_summary_length:
        max_summary_length = 300 if len(summary_content) > 1000 else 150

    summary = summarize(summary_content, max_summary_length=max_summary_length)

    return {
        "original_content": original_content,
        "summary": summary,
        "content_length": len(original_content),
        "word_count": len(original_content.split())
    }

if __name__ == "__main__":
    topic = input("Enter the topic to search: ")
    max_summary_input_length = int(input("Enter the max content size limit for summarization (in characters): "))  # ✅ renamed prompt
    result = generate_wikipedia_summary_and_questions(topic, max_summary_input_length=max_summary_input_length)

    if isinstance(result, dict):
        print(f"\nWikipedia content for {topic} ({result['content_length']} characters, {result['word_count']} words):")
        print(result["original_content"][:500] + "...\n")  # ✅ still previewing first 500 chars

        print("\nSummary:")
        print(result["summary"])
        
    else:
        print(result)
