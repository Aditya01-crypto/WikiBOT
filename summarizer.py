
from transformers import T5Tokenizer, T5ForConditionalGeneration
from nltk import sent_tokenize
import logging
from typing import List
import re

logging.basicConfig(filename="wikibot.log", level=logging.DEBUG, 
                    format="%(asctime)s - %(levelname)s - %(message)s")

# Load model once at startup
tokenizer = T5Tokenizer.from_pretrained("t5-base", legacy=False)
model = T5ForConditionalGeneration.from_pretrained("t5-base")

def clean_summary(summary: str) -> str:
    """
    Cleans and trims the summary to ensure it ends with a complete sentence.
    """
    sentences = re.findall(r'[^.!?]*[.!?]', summary)
    if sentences:
        return ''.join(sentences).strip()
    else:
        return summary.strip()

def summarize(text: str, max_length: int = 150, min_length: int = 50) -> str:
    """
    Summarize a single chunk of text using T5 model
    Args:
        text: Input text to summarize
        max_length: Maximum length of summary (in tokens)
        min_length: Minimum length of summary (in tokens)
    Returns:
        Generated summary text
    """
    try:
        input_text = "summarize: " + text
        inputs = tokenizer.encode(
            input_text,
            return_tensors="pt",
            max_length=512,
            truncation=True
        )
        
        summary_ids = model.generate(
            inputs,
            max_length=max_length,
            min_length=min_length,
            num_beams=4,
            length_penalty=2.0,
            early_stopping=True
        )
        summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        return clean_summary(summary)
    except Exception as e:
        logging.error(f"Error summarizing chunk: {str(e)}")
        raise RuntimeError(f"Summarization failed: {str(e)}")

def split_text(text: str, max_tokens: int = 500) -> List[str]:
    """
    Split text into chunks of approximately max_tokens length
    respecting sentence boundaries
    """
    try:
        sentences = sent_tokenize(text)
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(tokenizer.tokenize(sentence))
            
            if current_length + sentence_length > max_tokens and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_length = 0
                
            current_chunk.append(sentence)
            current_length += sentence_length
            
        if current_chunk:
            chunks.append(" ".join(current_chunk))
            
        return chunks
        
    except Exception as e:
        logging.error(f"Error splitting text: {str(e)}")
        raise RuntimeError(f"Text splitting failed: {str(e)}")

def summarize_wikipedia(text: str, max_summary_length: int = 500) -> str:
    """
    Generate a summary of specified length from Wikipedia text
    Args:
        text: Full Wikipedia article text
        max_summary_length: Desired approximate word count for summary
    Returns:
        Generated summary text
    """
    try:
        if not text or len(text.strip()) < 10:
            raise ValueError("Input text is too short or empty")

        # Adjust parameters based on requested summary size
        if max_summary_length <= 1500:  # Small summary
            chunk_size = 300  # Smaller chunks for more focused summaries
            chunk_max_length = 100
            chunk_min_length = 50
            num_beams = 4
        elif max_summary_length <= 3000:  # Medium summary
            chunk_size = 500
            chunk_max_length = 150
            chunk_min_length = 75
            num_beams = 4
        else:  # Large summary (up to 6000 words)
            chunk_size = 800
            chunk_max_length = 200
            chunk_min_length = 100
            num_beams = 6

        # Split into appropriate chunks
        chunks = split_text(text, max_tokens=chunk_size)
        if not chunks:
            raise ValueError("Failed to split text into chunks")

        # Summarize each chunk
        summaries = []
        total_words = 0
        for chunk in chunks:
            summary = summarize(
                chunk,
                max_length=chunk_max_length,
                min_length=chunk_min_length
            )
            summaries.append(summary)
            total_words += len(summary.split())
            
            # Early stopping if we have enough material
            if total_words >= max_summary_length * 1.2:
                break

        # Combine and trim to exact length
        combined = " ".join(summaries)
        words = combined.split()
        
        if len(words) > max_summary_length:
            combined = " ".join(words[:max_summary_length])
            
        # Final quality check
        if len(combined.split()) < max_summary_length * 0.8:
            raise ValueError(f"Failed to generate sufficient summary content "
                           f"(requested: {max_summary_length}, got: {len(combined.split())})")

        logging.info(f"Generated summary: {len(combined.split())} words "
                    f"(requested: {max_summary_length})")
        
        # Clean the final summary
        return clean_summary(combined)

    except Exception as e:
        logging.error(f"Error in summarize_wikipedia: {str(e)}")
        raise RuntimeError(f"Wikipedia summarization failed: {str(e)}")

