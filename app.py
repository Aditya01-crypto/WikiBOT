
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
# from wikibot import generate_wikipedia_content  # We'll use this directly for better control
from wikibot import fetch_wikipedia_content  # We'll use this directly for better control
import threading
import time

class WikipediaSummarizerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("WikiBOT")
        self.root.geometry("900x700")
        
        # Thread control variables
        self.fetch_thread = None
        self.summarize_thread = None
        self.stop_fetching = False
        
        # Configure styles
        self.style = ttk.Style()
        self.style.configure('TButton', font=('Arial', 10))
        self.style.configure('TLabel', font=('Arial', 10))
        
        # Create main frames
        self.top_frame = ttk.Frame(root, padding="10")
        self.top_frame.pack(fill=tk.X)
        
        self.middle_frame = ttk.Frame(root, padding="10")
        self.middle_frame.pack(fill=tk.BOTH, expand=True)
        
        self.bottom_frame = ttk.Frame(root, padding="10")
        self.bottom_frame.pack(fill=tk.X)
        
        # Topic input
        ttk.Label(self.top_frame, text="Enter Topic:").grid(row=0, column=0, sticky=tk.W)
        self.topic_entry = ttk.Entry(self.top_frame, width=50)
        self.topic_entry.grid(row=0, column=1, padx=5, sticky=tk.W)
        
        # Max content size input
        ttk.Label(self.top_frame, text="Max Content Size (chars):").grid(row=1, column=0, sticky=tk.W)
        self.max_content_entry = ttk.Entry(self.top_frame, width=10)
        self.max_content_entry.insert(0, "10000")  # Default value
        self.max_content_entry.grid(row=1, column=1, padx=5, sticky=tk.W)
        
        # Buttons
        self.fetch_btn = ttk.Button(self.top_frame, text="Fetch Content", command=self.fetch_content)
        self.fetch_btn.grid(row=0, column=2, padx=5)
        
        self.summarize_btn = ttk.Button(self.top_frame, text="Summarize", command=self.start_summarize, state=tk.DISABLED)
        self.summarize_btn.grid(row=0, column=3, padx=5)
        
        self.clear_btn = ttk.Button(self.top_frame, text="Clear All", command=self.clear_all)
        self.clear_btn.grid(row=0, column=4, padx=5)
        
        # Content display
        self.content_label = ttk.Label(self.middle_frame, text="Original Content:")
        self.content_label.pack(anchor=tk.W)
        
        self.content_text = scrolledtext.ScrolledText(self.middle_frame, wrap=tk.WORD, height=15)
        self.content_text.pack(fill=tk.BOTH, expand=True)
        
        # Summary display
        self.summary_label = ttk.Label(self.middle_frame, text="Summary:")
        self.summary_label.pack(anchor=tk.W)
        
        self.summary_text = scrolledtext.ScrolledText(self.middle_frame, wrap=tk.WORD, height=15)
        self.summary_text.pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(self.bottom_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        self.status_bar.pack(fill=tk.X)
        
        # Store fetched content
        self.fetched_content = None
    
    def fetch_content(self):
        topic = self.topic_entry.get().strip()
        if not topic:
            messagebox.showerror("Error", "Please enter a topic to search")
            return
        
        try:
            max_content_size = int(self.max_content_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number for max content size")
            return
        
        # Reset stop flag
        self.stop_fetching = False
        
        self.status_var.set("Fetching Wikipedia content...")
        self.root.update()
        
        # Disable buttons during fetch
        self.fetch_btn.config(state=tk.DISABLED)
        self.summarize_btn.config(state=tk.DISABLED)
        
        # Clear any existing content
        self.content_text.delete(1.0, tk.END)
        self.summary_text.delete(1.0, tk.END)
        self.fetched_content = None
        
        # Run in a separate thread to prevent GUI freezing
        self.fetch_thread = threading.Thread(
            target=self._fetch_content_thread,
            args=(topic, max_content_size),
            daemon=True
        )
        self.fetch_thread.start()
        
        # Start checking the thread status
        self.check_fetch_thread()
    
    def check_fetch_thread(self):
        if self.fetch_thread and self.fetch_thread.is_alive():
            # Thread is still running, check again after 100ms
            self.root.after(100, self.check_fetch_thread)
        else:
            # Thread has finished, clean up
            self.fetch_thread = None
    
    def _fetch_content_thread(self, topic, max_content_size):
        try:
            # Get the raw content first (we'll process it ourselves)
            content = fetch_wikipedia_content(topic)
            
            # Check if we should stop
            if self.stop_fetching:
                self.status_var.set("Fetch cancelled")
                return
            
            if "Error" in content:
                self.status_var.set(content)
                messagebox.showerror("Error", content)
                return
            
            # Process the content
            content_length = len(content)
            word_count = len(content.split())
            
            # Handle original content truncation for display: 25,000 characters
            display_limit = 25000
            if content_length > display_limit:
                original_content = self.truncate_at_nearest_period(content, display_limit)
            else:
                original_content = content
            
            # For summarization, limit input to user-defined max_summary_input_length
            if content_length > max_content_size:
                summary_content = content[:max_content_size]
            else:
                summary_content = content
            
            # Store the results
            self.fetched_content = {
                "original_content": original_content,
                "summary_content": summary_content,
                "content_length": len(original_content),
                "word_count": word_count
            }
            
            # Update the GUI
            if not self.stop_fetching:
                self.content_text.delete(1.0, tk.END)
                self.content_text.insert(tk.END, original_content)
                self.summarize_btn.config(state=tk.NORMAL)
                self.status_var.set(f"Fetched {word_count} words. Ready to summarize.")
            
        except Exception as e:
            if not self.stop_fetching:
                self.status_var.set("Error occurred during fetch")
                messagebox.showerror("Error", f"An error occurred: {str(e)}")
        finally:
            if not self.stop_fetching:
                self.fetch_btn.config(state=tk.NORMAL)
    
    def truncate_at_nearest_period(self, text, limit):
        """Helper method to truncate text at the nearest period before limit"""
        if len(text) <= limit:
            return text
        cut_index = text.rfind('.', 0, limit)
        if cut_index == -1:
            return text[:limit]
        return text[:cut_index + 1]
    
    def start_summarize(self):
        if not self.fetched_content:
            messagebox.showerror("Error", "No content to summarize")
            return
        
        self.status_var.set("Generating summary... Please wait")
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(tk.END, "Generating summary... Please wait...")
        self.root.update()
        
        # Disable buttons during summarization
        self.summarize_btn.config(state=tk.DISABLED)
        self.fetch_btn.config(state=tk.DISABLED)
        
        # Run in a separate thread to prevent GUI freezing
        self.summarize_thread = threading.Thread(
            target=self._summarize_thread,
            daemon=True
        )
        self.summarize_thread.start()
        
        # Start checking the thread status
        self.check_summarize_thread()
    
    def check_summarize_thread(self):
        if self.summarize_thread and self.summarize_thread.is_alive():
            # Thread is still running, check again after 100ms
            self.root.after(100, self.check_summarize_thread)
        else:
            # Thread has finished, clean up
            self.summarize_thread = None
    
    def _summarize_thread(self):
        try:
            # Simulate longer processing time for demonstration
            time.sleep(1)
            
            # Check if we should stop (though summarization is usually quick)
            if self.stop_fetching:
                return
            
            # Get the summary (using the imported summarizer function)
            from summarizer import summarize_wikipedia as summarize
            summary = summarize(self.fetched_content["summary_content"])
            
            # Update the GUI
            self.summary_text.delete(1.0, tk.END)
            self.summary_text.insert(tk.END, summary)
            self.status_var.set("Summary generated successfully")
            
        except Exception as e:
            self.status_var.set("Error occurred during summarization")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        finally:
            self.summarize_btn.config(state=tk.NORMAL)
            self.fetch_btn.config(state=tk.NORMAL)
    
    def clear_all(self):
        # Set the stop flag to cancel any ongoing operations
        self.stop_fetching = True
        
        # Clear the UI elements
        self.topic_entry.delete(0, tk.END)
        self.max_content_entry.delete(0, tk.END)
        self.max_content_entry.insert(0, "10000")
        self.content_text.delete(1.0, tk.END)
        self.summary_text.delete(1.0, tk.END)
        self.fetched_content = None
        self.summarize_btn.config(state=tk.DISABLED)
        self.status_var.set("Ready")
        
        # Re-enable buttons in case they were disabled
        self.fetch_btn.config(state=tk.NORMAL)
        self.summarize_btn.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = WikipediaSummarizerGUI(root)
    root.mainloop()