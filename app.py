import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, Menu
from wikibot import generate_wikipedia_summary
import threading
import queue
import logging

logging.basicConfig(filename="wikibot.log", level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

class WikipediaSummarizerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("WikiBOT - Wikipedia Content Summarizer")
        self.root.geometry("1000x800")
        self.root.minsize(800, 600)
        
        self.task_queue = queue.Queue()
        self.running = False
        self.current_content = None
        
        self.style = ttk.Style()
        self.style.configure('TButton', font=('Arial', 10), padding=5)
        self.style.configure('TLabel', font=('Arial', 10))
        self.style.configure('TEntry', padding=5)
        
        self.create_widgets()
        self.root.after(100, self.process_queue)
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Control Frame
        control_frame = ttk.Frame(main_frame, padding="10")
        control_frame.pack(fill=tk.X)
        
        ttk.Label(control_frame, text="Enter Topic:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.topic_entry = ttk.Entry(control_frame, width=40)
        self.topic_entry.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        ttk.Label(control_frame, text="Max Content Size:").grid(row=0, column=2, sticky=tk.W, padx=(10, 5))
        max_size_label = ttk.Label(control_frame, text="15,000 chars (fixed)", foreground="gray")
        max_size_label.grid(row=0, column=3, sticky=tk.W, padx=5)
        
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=0, column=4, sticky=tk.E, padx=(10, 0))
        
        self.fetch_btn = ttk.Button(button_frame, text="Fetch Content", command=self.start_fetch)
        self.fetch_btn.pack(side=tk.LEFT, padx=5)
        
        self.summarize_btn = ttk.Button(
            button_frame, 
            text="Summarize", 
            command=self.show_summary_options,
            state=tk.DISABLED
        )
        self.summarize_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_btn = ttk.Button(button_frame, text="Clear All", command=self.clear_all)
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        
        # Display Area
        display_frame = ttk.Frame(main_frame)
        display_frame.pack(fill=tk.BOTH, expand=True)
        
        # Content Display
        content_frame = ttk.Frame(display_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        self.content_label = ttk.Label(content_frame, text="Original Content:")
        self.content_label.pack(anchor=tk.W)
        
        self.content_text = scrolledtext.ScrolledText(
            content_frame,
            wrap=tk.WORD,
            font=('Arial', 10),
            padx=10,
            pady=10,
            state=tk.DISABLED
        )
        self.content_text.pack(fill=tk.BOTH, expand=True)
        
        # Status Panel
        self.status_panel = ttk.Label(
            display_frame,
            text="Status: Ready",
            font=('Arial', 10),
            padding=5,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_panel.pack(fill=tk.X, pady=5)
        
        # Summary Display
        summary_frame = ttk.Frame(display_frame)
        summary_frame.pack(fill=tk.BOTH, expand=True)
        
        self.summary_label = ttk.Label(summary_frame, text="Summary:")
        self.summary_label.pack(anchor=tk.W)
        
        self.summary_text = scrolledtext.ScrolledText(
            summary_frame,
            wrap=tk.WORD,
            font=('Arial', 10),
            padx=10,
            pady=10,
            state=tk.DISABLED
        )
        self.summary_text.pack(fill=tk.BOTH, expand=True)
        
        # Status Bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(
            main_frame,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            padding=(5, 5, 5, 5),
            anchor=tk.W
        )
        self.status_bar.pack(fill=tk.X)
    
    def show_summary_options(self):
        """Show Small/Medium/Large options when Summarize is clicked."""
        if not self.current_content:
            messagebox.showerror("Error", "No content to summarize. Fetch content first!")
            return

        menu = Menu(self.root, tearoff=0)
        menu.add_command(label="Small (150 words)", command=lambda: self.start_summarize(150))
        menu.add_command(label="Medium (300 words)", command=lambda: self.start_summarize(300))
        menu.add_command(label="Large (500 words)", command=lambda: self.start_summarize(500))
        menu.tk_popup(self.summarize_btn.winfo_rootx(), self.summarize_btn.winfo_rooty() + 30)

    
    def start_fetch(self):
        """Fetch Wikipedia content (fixed at 15,000 chars)."""
        if self.running:
            messagebox.showwarning("Warning", "Operation already in progress")
            return
            
        topic = self.topic_entry.get().strip()
        if not topic:
            messagebox.showerror("Error", "Please enter a topic")
            return
            
        self.running = True
        self.update_status("Fetching content... Please wait")
        self._set_ui_state(fetching=True)
        
        self.content_text.config(state=tk.NORMAL)
        self.content_text.delete(1.0, tk.END)
        self.content_text.insert(tk.END, "Fetching content... Please wait")
        self.content_text.config(state=tk.DISABLED)
        
        self.summary_text.config(state=tk.NORMAL)
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.config(state=tk.DISABLED)
        
        threading.Thread(
            target=self._fetch_content,
            args=(topic, 15000),  # Fixed at 15,000 chars
            daemon=True
        ).start()
    
    def _fetch_content(self, topic: str, max_chars: int):
        logging.debug(f"Fetching content for topic: {topic}, max_chars: {max_chars}")
        try:
            result = generate_wikipedia_summary(topic, max_input_length=max_chars)
            if "error" in result:
                self.task_queue.put(("error", result["error"]))
            else:
                self.task_queue.put(("content", {
                    "original_content": result["original_content"],
                    "content_for_summary": result["original_content"][:max_chars],
                    "word_count": result["word_count"]
                }))
        except Exception as e:
            self.task_queue.put(("error", f"Fetch error: {str(e)}"))
        finally:
            self.task_queue.put(("done", None))
    
    def start_summarize(self, summary_length: int):
        """Generate summary with selected length."""
        if not self.current_content or self.running:
            messagebox.showerror("Error", "No content to summarize or operation in progress")
            return
            
        self.running = True
        self.update_status(f"Generating {summary_length}-word summary... Please wait")
        self._set_ui_state(summarizing=True)
        
        self.summary_text.config(state=tk.NORMAL)
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(tk.END, f"Generating {summary_length}-word summary... Please wait...")
        self.summary_text.config(state=tk.DISABLED)
        
        # Pass both max_content_size AND summary_length to wikibot
        threading.Thread(
            target=self._generate_summary,
            args=(self.topic_entry.get().strip(), 15000, summary_length),  # Fixed 15k chars, variable summary length
            daemon=True
        ).start()

    def _generate_summary(self, topic: str, max_chars: int, summary_length: int):
        logging.debug(f"Summarizing {max_chars} chars to {summary_length} words")
        try:
            result = generate_wikipedia_summary(topic, 
                                            max_input_length=max_chars,
                                            summary_length=summary_length)
            if "error" in result:
                self.task_queue.put(("error", result["error"]))
            else:
                self.task_queue.put(("summary", result["summary"]))
        except Exception as e:
            self.task_queue.put(("error", f"Summary error: {str(e)}"))
        finally:
            self.task_queue.put(("done", None))
        
    def process_queue(self):
        try:
            while True:
                task_type, data = self.task_queue.get_nowait()
                if task_type == "content":
                    self.current_content = data
                    self._display_content(data["original_content"])
                    self.update_status(f"Fetched {data['word_count']} words. Ready to summarize.")
                    self.summarize_btn.config(state=tk.NORMAL)
                elif task_type == "summary":
                    self._display_summary(data)
                    self.update_status("Summary complete")
                elif task_type == "error":
                    messagebox.showerror("Error", data)
                    self.update_status("Error occurred", bar=False)
                elif task_type == "done":
                    self.running = False
                    self._set_ui_state(idle=True)
        except queue.Empty:
            pass
        self.root.after(100, self.process_queue)
    
    def _display_content(self, content: str):
        self.content_text.config(state=tk.NORMAL)
        self.content_text.delete(1.0, tk.END)
        self.content_text.insert(tk.END, content)
        self.content_text.config(state=tk.DISABLED)
        self.content_text.see(tk.END)
    
    def _display_summary(self, summary: str):
        self.summary_text.config(state=tk.NORMAL)
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(tk.END, summary)
        self.summary_text.config(state=tk.DISABLED)
        self.summary_text.see(tk.END)
    
    def update_status(self, message, panel=True, bar=True):
        if panel:
            self.status_panel.config(text=f"Status: {message}")
        if bar:
            self.status_var.set(message)
        self.root.update()
    
    def _set_ui_state(self, fetching=False, summarizing=False, idle=False):
        if idle:
            self.fetch_btn.config(state=tk.NORMAL)
            self.summarize_btn.config(state=tk.NORMAL if self.current_content else tk.DISABLED)
        elif fetching:
            self.fetch_btn.config(state=tk.DISABLED)
            self.summarize_btn.config(state=tk.DISABLED)
        elif summarizing:
            self.summarize_btn.config(state=tk.DISABLED)
            self.fetch_btn.config(state=tk.DISABLED)
    
    def clear_all(self):
        logging.debug("Clearing all GUI elements")
        if self.running:
            if messagebox.askyesno("Confirm", "Cancel current operation?"):
                self.running = False
                self.task_queue.queue.clear()
        self.topic_entry.delete(0, tk.END)
        self.current_content = None
        self.content_text.config(state=tk.NORMAL)
        self.content_text.delete(1.0, tk.END)
        self.content_text.config(state=tk.DISABLED)
        self.summary_text.config(state=tk.NORMAL)
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.config(state=tk.DISABLED)
        self.update_status("Ready")
        self._set_ui_state(idle=True)

if __name__ == "__main__":
    root = tk.Tk()
    app = WikipediaSummarizerGUI(root)
    root.mainloop()
