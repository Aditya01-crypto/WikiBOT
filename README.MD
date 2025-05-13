# WikiBot  
*Your personal Wikipedia-powered knowledge assistant, with automatic summarization and flashcards!*

WikiBot is a Python-based tool that allows you to fetch information from Wikipedia and automatically summarize it using AI models to assist with studying and information retention. It’s designed to help students, researchers, or curious minds quickly digest and retain knowledge from Wikipedia articles.

##  Features

- Fetch Wikipedia content for any topic
- AI-powered summarization using Hugging Face's T5 model
- Adjustable content length and summary size
- Clean GUI built with Tkinter
- Multithreading to prevent UI freezing

## Installation

To install WikiBot and its dependencies:

1. **Clone the repository:**

```bash
git clone https://github.com/yourusername/wikibot.git
cd wikibot
```

2.**Install dependencies:**

```bash

pip install -r requirements.txt
```
3.**Download NLTK tokenizer data (required for sentence splitting):**

Open a Python shell and run:
```bash
import nltk
nltk.download('punkt')
```

4.**Run the app:**

```bash
python app.py
```
5.**How to Use**

Enter a topic (e.g., "Quantum Computing")

Click 'Fetch Content' to retrieve the Wikipedia article

Click 'Summarize' to generate an AI summary

**Credits**

Hugging Face Transformers for the T5 model

Wikipedia-API for content fetching
