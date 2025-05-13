
from transformers import T5Tokenizer, T5ForConditionalGeneration
from nltk import sent_tokenize

# Initialize the tokenizer and model globally
tokenizer = T5Tokenizer.from_pretrained("t5-base", legacy=False)
model = T5ForConditionalGeneration.from_pretrained("t5-base")

def summarize(text, max_length=150, min_length=50):
    """
    Summarizes a given text using the T5 model.
    """
    input_text = "summarize: " + text
    input_ids = tokenizer.encode(input_text, return_tensors="pt", max_length=512, truncation=True)

    summary_ids = model.generate(
        input_ids,
        max_length=max_length,
        min_length=min_length,
        num_beams=6,
        length_penalty=2.0,
        repetition_penalty=2.0,
        early_stopping=True
    )

    return tokenizer.decode(summary_ids[0], skip_special_tokens=True)

def split_text(text, max_tokens=450):
    """
    Splits text into chunks at sentence boundaries, under max_tokens.
    """
    sentences = sent_tokenize(text)
    chunks = []
    current_chunk = ""
    current_tokens = 0

    for sentence in sentences:
        tokens_in_sentence = len(sentence.split())

        if current_tokens + tokens_in_sentence <= max_tokens:
            current_chunk += " " + sentence
            current_tokens += tokens_in_sentence
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence
            current_tokens = tokens_in_sentence

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks

def summarize_wikipedia(text, max_summary_length=500):
    """
    Summarizes long Wikipedia content recursively.
    """
    chunks = split_text(text, max_tokens=450)
    summarized_chunks = [summarize(chunk) for chunk in chunks]

    combined_summary = " ".join(summarized_chunks)

    if len(combined_summary.split()) > max_summary_length:
        return summarize_wikipedia(combined_summary, max_summary_length)
    
    return combined_summary
