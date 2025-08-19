import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog, filedialog, ttk
import google.generativeai as genai
import threading
import json
import os

# -------------------------
# Main Chatbot Application
# -------------------------

class GeminiChatbot:
    """
    A Tkinter-based chatbot application that uses the Gemini API.
    It includes features for setting a custom persona, saving settings,
    and handling chat history.
    """
    def __init__(self):
        # Updated the bot persona to be more casual and conversational
        self.bot_name = "Shadow Scribe"
        self.bot_persona = (
            "You are a persona named 'Shadow Scribe.' Your purpose is to take "
            "the user's text, correct all grammatical errors, and then rewrite "
            "it with a casual but serious tone, as if you're a knowledgeable mentor. "
            "The style is inspired by 'Shadow Slave.' Use words like 'fear,' 'legacy,' "
            "and 'echo.' Your sentences should be easy to understand and conversational. "
            "Do not break character."
        )
        self.api_key = None
        self.model = None
        self.chat = None # This will hold the Gemini chat session
        self.chat_history = []
        self.config_file = "chatbot_config.json"
        
        # Load saved configuration
        self.load_config()
        
        # Initialize GUI
        self.setup_gui()
        
    def load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.bot_name = config.get('bot_name', self.bot_name)
                    self.bot_persona = config.get('bot_persona', self.bot_persona)
                    self.api_key = config.get('api_key', None)
        except Exception as e:
            print(f"Could not load config: {e}")
    
    def save_config(self):
        """Save configuration to file"""
        try:
            config = {
                'bot_name': self.bot_name,
                'bot_persona': self.bot_persona,
                'api_key': self.api_key if self.api_key else None
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Could not save config: {e}")
    
    def init_gemini(self, api_key):
        """
        Initialize Gemini with the provided API key.
        The initial chat session is started here with the persona as context.
        """
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel("gemini-1.5-flash")
            
            # Start a chat with the persona as the initial context
            self.chat = self.model.start_chat(history=[{
                "role": "user",
                "parts": [self.bot_persona]
            }, {
                "role": "model",
                "parts": ["Understood. I shall speak as the Shadow Scribe."]
            }])
            
            self.api_key = api_key
            self.save_config()
            return True
        except Exception as e:
            messagebox.showerror("API Error", f"Failed to initialize Gemini: {str(e)}")
            return False
    
    def get_gemini_response(self, user_input):
        """
        Get a response from the Gemini API using the chat session.
        This handles the conversational context automatically.
        """
        try:
            if not self.chat:
                return "Error: Gemini not initialized. Please check your API key."
            
            # Send the new message to the chat session
            response = self.chat.send_message(user_input)
            
            return response.text
        except Exception as e:
            return f"Error getting response: {str(e)}"
    
    def send_message(self):
        """Handle sending user message"""
        user_input = self.entry.get().strip()
        if not user_input:
            return
        
        # Disable send button and show loading
        self.send_button.config(state='disabled')
        self.entry.config(state='disabled')
        self.status_label.config(text="Thinking...")
        
        # Clear entry
        self.entry.delete(0, tk.END)
        
        # Display user message
        self.display_message("You", user_input, "#3a3a3a") # User message background
        
        # Add to history
        self.chat_history.append({"sender": "You", "message": user_input})
        
        # Get response in separate thread to prevent GUI freezing
        thread = threading.Thread(target=self._get_response_thread, args=(user_input,))
        thread.daemon = True
        thread.start()
    
    def _get_response_thread(self, user_input):
        """Get response in separate thread"""
        bot_response = self.get_gemini_response(user_input)
        
        # Update GUI in main thread
        self.root.after(0, self._display_bot_response, bot_response)
    
    def _display_bot_response(self, response):
        """Display bot response and re-enable controls"""
        self.display_message(self.bot_name, response, "#2a2a2a") # Bot message background
        
        # Add to history
        self.chat_history.append({"sender": self.bot_name, "message": response})
        
        # Re-enable controls
        self.send_button.config(state='normal')
        self.entry.config(state='normal')
        self.status_label.config(text="Ready")
        self.entry.focus()
    
    def display_message(self, sender, message, bg_color):
        """Display a message in the chat window with styling"""
        self.chat_window.config(state='normal')
        
        # Use a different color for the sender's name
        sender_color = "#9e86c9" if sender == self.bot_name else "#a3a3a3"
        
        self.chat_window.insert(tk.END, f"\n{sender}:\n", ("sender_name", f"sender_{sender}"))
        self.chat_window.tag_config(f"sender_{sender}", foreground=sender_color)
        
        # Insert message with background color and light text
        start_pos = self.chat_window.index(tk.END)
        self.chat_window.insert(tk.END, f"{message}\n")
        end_pos = self.chat_window.index(tk.END)
        
        # Apply styling
        self.chat_window.tag_add(f"msg_{sender}", start_pos, end_pos)
        self.chat_window.tag_config(f"msg_{sender}", background=bg_color, foreground="#e0e0e0", 
                                     lmargin1=10, lmargin2=10, rmargin=10, 
                                     font=("Verdana", 10)) # Custom font for messages
        
        self.chat_window.config(state='disabled')
        self.chat_window.see(tk.END)
    
    def on_enter_pressed(self, event):
        """Handle Enter key press"""
        self.send_message()
        return 'break'
    
    # -------------------------
    # Context Menu Functions
    # -------------------------
    
    def copy_text(self):
        """Copy selected text"""
        try:
            selected_text = self.chat_window.selection_get()
            self.root.clipboard_clear()
            self.root.clipboard_append(selected_text)
            self.status_label.config(text="Text copied to clipboard")
        except tk.TclError:
            self.status_label.config(text="No text selected")
    
    def clear_chat(self):
        """Clear chat window and reset chat session"""
        if messagebox.askyesno("Clear Chat", "Are you sure you want to clear the chat history?"):
            self.chat_window.config(state='normal')
            self.chat_window.delete(1.0, tk.END)
            self.chat_window.config(state='disabled')
            self.chat_history.clear()
            self.status_label.config(text="Chat cleared")
            
            # Reset the chat session
            if self.model:
                self.chat = self.model.start_chat(history=[{
                    "role": "user",
                    "parts": [self.bot_persona]
                }, {
                    "role": "model",
                    "parts": ["Understood. I shall speak as the Shadow Scribe."]
                }])
            self.display_welcome_message()

    # -------------------------
    # Settings Functions
    # -------------------------
    
    def open_settings(self):
        """Open settings dialog"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("400x350")
        settings_window.resizable(False, False)
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        bg_color = "#1e1e1e"
        fg_color = "#e0e0e0"
        entry_bg = "#2a2a2a"
        entry_fg = "#e0e0e0"
        
        settings_window.config(bg=bg_color)
        
        # Bot name
        tk.Label(settings_window, text="Bot Name:", font=("Verdana", 10, "bold"), bg=bg_color, fg=fg_color).pack(pady=5)
        name_var = tk.StringVar(value=self.bot_name)
        name_entry = tk.Entry(settings_window, textvariable=name_var, width=30, 
                              font=("Verdana", 10), bg=entry_bg, fg=entry_fg, insertbackground=fg_color)
        name_entry.pack(pady=5)
        
        # Bot persona
        tk.Label(settings_window, text="Bot Persona:", font=("Verdana", 10, "bold"), bg=bg_color, fg=fg_color).pack(pady=(15, 5))
        persona_text = scrolledtext.ScrolledText(settings_window, width=45, height=5, 
                                                font=("Verdana", 9), bg=entry_bg, fg=entry_fg, insertbackground=fg_color)
        persona_text.insert(1.0, self.bot_persona)
        persona_text.pack(pady=5, padx=10)
        
        # API Key
        tk.Label(settings_window, text="API Key:", font=("Verdana", 10, "bold"), bg=bg_color, fg=fg_color).pack(pady=(15, 5))
        api_var = tk.StringVar(value=self.api_key if self.api_key else "")
        api_entry = tk.Entry(settings_window, textvariable=api_var, width=30, 
                             font=("Verdana", 10), show="*", bg=entry_bg, fg=entry_fg, insertbackground=fg_color)
        api_entry.pack(pady=5)
        
        # Buttons
        button_frame = tk.Frame(settings_window, bg=bg_color)
        button_frame.pack(pady=15)
        
        def save_settings():
            new_name = name_var.get().strip()
            new_persona = persona_text.get(1.0, tk.END).strip()
            new_api_key = api_var.get().strip()
            
            if new_name:
                self.bot_name = new_name
            if new_persona:
                self.bot_persona = new_persona
            
            # If API key has changed, re-initialize Gemini
            if new_api_key and new_api_key != self.api_key:
                if self.init_gemini(new_api_key):
                    self.status_label.config(text="Settings saved and API initialized successfully!")
                    self.clear_chat() # Clear chat to start a new session with the new persona
                else:
                    return
            else:
                self.save_config()
                self.status_label.config(text="Settings saved!")
            
            settings_window.destroy()
        
        tk.Button(button_frame, text="Save", command=save_settings, 
                  bg="#4a0e67", fg="white", font=("Verdana", 10)).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=settings_window.destroy, 
                  bg="#6a6a6a", fg="white", font=("Verdana", 10)).pack(side=tk.LEFT, padx=5)
    
    def setup_gui(self):
        """Setup the main GUI"""
        self.root = tk.Tk()
        self.root.title("Shadow Scribe")
        self.root.geometry("700x800")
        self.root.minsize(600, 600)
        
        # Configure colors and style
        bg_color = "#1e1e1e" # Dark background
        fg_color = "#e0e0e0" # Light foreground
        title_color = "#9e86c9" # Purple for title
        entry_bg = "#2a2a2a"
        button_bg = "#4a0e67" # Dark purple for button
        
        self.root.config(bg=bg_color)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Main container
        main_frame = tk.Frame(self.root, bg=bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Title
        title_label = tk.Label(main_frame, text="✍️ The Shadow Scribe", 
                                font=("Garamond", 20, "bold"), bg=bg_color, fg=title_color) # Thematic font
        title_label.pack(pady=(0, 10))
        
        # Chat display area with frame
        chat_frame = tk.Frame(main_frame, relief=tk.SUNKEN, bd=1, bg=entry_bg)
        chat_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.chat_window = scrolledtext.ScrolledText(
            chat_frame, wrap=tk.WORD, font=("Verdana", 11), 
            bg=entry_bg, fg=fg_color, state='disabled',
            padx=10, pady=10, insertbackground=fg_color # Cursor color
        )
        self.chat_window.pack(fill=tk.BOTH, expand=True)
        
        # Configure text tags for styling
        self.chat_window.tag_config("sender_name", font=("Verdana", 9, "bold"))
        
        # Context menu for chat window
        self.create_context_menu()
        
        # Input frame
        input_frame = tk.Frame(main_frame, bg=bg_color)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        # User input
        self.entry = tk.Entry(input_frame, font=("Verdana", 12), relief=tk.FLAT, bd=5, 
                               bg=entry_bg, fg=fg_color, insertbackground=fg_color)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.entry.bind("<Return>", self.on_enter_pressed)
        
        # Send button
        self.send_button = tk.Button(
            input_frame, text="Send", command=self.send_message,
            bg=button_bg, fg="white", font=("Verdana", 12, "bold"),
            relief=tk.RAISED, bd=2, padx=20
        )
        self.send_button.pack(side=tk.RIGHT)
        
        # Status bar
        status_frame = tk.Frame(main_frame, bg="#2a2a2a", relief=tk.SUNKEN, bd=1)
        status_frame.pack(fill=tk.X)
        
        self.status_label = tk.Label(status_frame, text="Ready", 
                                     font=("Verdana", 9), bg="#2a2a2a", fg="#a3a3a3", anchor=tk.W)
        self.status_label.pack(fill=tk.X, padx=5, pady=2)
        
        # Welcome message
        self.display_welcome_message()
        
        # Focus on entry
        self.entry.focus()
        
        # Check if API key is available
        if not self.api_key:
            self.root.after(100, self.prompt_for_api_key)
        else:
            self.init_gemini(self.api_key)
    
    def create_menu_bar(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root, bg="#1e1e1e", fg="#e0e0e0")
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0, bg="#2a2a2a", fg="#e0e0e0")
        file_menu.add_command(label="New Chat", command=self.clear_chat, accelerator="Ctrl+N")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit, accelerator="Ctrl+Q")
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0, bg="#2a2a2a", fg="#e0e0e0")
        edit_menu.add_command(label="Copy", command=self.copy_text, accelerator="Ctrl+C")
        edit_menu.add_command(label="Clear Chat", command=self.clear_chat)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        
        # Settings menu
        settings_menu = tk.Menu(menubar, tearoff=0, bg="#2a2a2a", fg="#e0e0e0")
        settings_menu.add_command(label="Bot Settings...", command=self.open_settings)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        
        self.root.config(menu=menubar)

    def create_context_menu(self):
        """Create context menu for chat window"""
        self.context_menu = tk.Menu(self.root, tearoff=0, bg="#2a2a2a", fg="#e0e0e0")
        self.context_menu.add_command(label="Copy", command=self.copy_text)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Clear Chat", command=self.clear_chat)
        
        def show_context_menu(event):
            try:
                self.context_menu.post(event.x_root, event.y_root)
            except tk.TclError:
                pass
        
        self.chat_window.bind("<Button-3>", show_context_menu)
    
    def display_welcome_message(self):
        """Display welcome message"""
        welcome_msg = f"A forgotten Echo, I am the Shadow Scribe. Speak your truths, and I shall weave them into the fabric of this world's dark legacy."
        self.chat_window.config(state='normal')
        self.chat_window.insert(tk.END, f"{welcome_msg}\n\n", "welcome")
        self.chat_window.tag_config("welcome", font=("Garamond", 12, "italic"), 
                                    foreground="#9e86c9", justify=tk.CENTER)
        self.chat_window.config(state='disabled')
    
    def prompt_for_api_key(self):
        """Prompt user for API key if not available"""
        api_key = simpledialog.askstring(
            "API Key Required", 
            "Please enter your Gemini API Key:",
            show='*'
        )
        if api_key:
            if self.init_gemini(api_key):
                self.status_label.config(text="Gemini initialized successfully!")
            else:
                self.root.after(1000, self.prompt_for_api_key)
        else:
            if messagebox.askyesno("Exit", "API key is required to use the chatbot. Exit application?"):
                self.root.quit()
            else:
                self.root.after(1000, self.prompt_for_api_key)
    
    def run(self):
        """Start the application"""
        self.root.mainloop()

# -------------------------
# Main Program Entry
# -------------------------
if __name__ == "__main__":
    app = GeminiChatbot()
    app.run()
