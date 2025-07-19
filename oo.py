import tkinter as tk
from tkinter import ttk
import cohere
import logging
import requests
import webbrowser
import pyautogui
import psutil
import socket
import os
import subprocess
import datetime
import time
import mss
from pyttsx3 import init as tts_init
import winsound
import uuid

# ---------------------- Logging Setup ----------------------
logging.basicConfig(filename="jarvis.log", level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# ---------------------- Cohere Setup ----------------------
try:
    co = cohere.Client("MLwMfd8NNIHQu4XCKc9g5exdVw0SIAYbD0oaZZj9")
    logging.info("Cohere client initialized successfully.")
except Exception as e:
    logging.error(f"Cohere initialization failed: {e}")
    co = None

# ---------------------- TTS Setup ----------------------
engine = tts_init()

# ---------------------- GUI ----------------------
class JarvisGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Jarvis AI")
        self.root.geometry("900x600")
        self.root.minsize(400, 300)
        self.is_dark_mode = True
        self.bg_colors = ["#0a0a0a", "#1c2526"]
        self.root.configure(bg=self.bg_colors[0])

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        self.main_frame = tk.Frame(self.root, bg=self.bg_colors[0])
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(1, weight=1)

        self.header_label = tk.Label(
            self.main_frame,
            text="JARVIS AI",
            font=("Arial", 28, "bold"),
            fg="#00ffcc",
            bg=self.bg_colors[0],
            pady=10
        )
        self.header_label.grid(row=0, column=0, sticky="ew")
        self.header_label.configure(anchor="center")
        self.fade_in_widget(self.header_label)

        self.toggle_button = tk.Button(
            self.main_frame,
            text="Toggle Light Mode",
            command=self.toggle_theme,
            font=("Arial", 10),
            bg="#00ffcc",
            fg="#0a0a0a",
            bd=0,
            relief=tk.FLAT,
            activebackground="#00ccaa",
            width=15
        )
        self.toggle_button.grid(row=0, column=1, sticky="e", padx=10)
        self.toggle_button.bind("<Enter>", lambda e: self.toggle_button.config(bg="#00ccaa"))
        self.toggle_button.bind("<Leave>", lambda e: self.toggle_button.config(bg="#00ffcc"))

        self.chat_frame = tk.Frame(self.main_frame, bg=self.bg_colors[1], highlightbackground="#00ffcc", highlightthickness=2)
        self.chat_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=10)
        self.chat_frame.columnconfigure(0, weight=1)
        self.chat_frame.rowconfigure(0, weight=1)

        self.chat_canvas = tk.Canvas(self.chat_frame, bg=self.bg_colors[1], highlightthickness=0)
        self.chat_canvas.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.scrollbar = ttk.Scrollbar(self.chat_frame, orient=tk.VERTICAL, command=self.chat_canvas.yview)
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.chat_canvas.configure(yscrollcommand=self.scrollbar.set)

        self.chat_inner_frame = tk.Frame(self.chat_canvas, bg=self.bg_colors[1])
        self.chat_window = self.chat_canvas.create_window((0, 0), window=self.chat_inner_frame, anchor="nw", tags="chat_inner")
        self.chat_inner_frame.bind("<Configure>", self.update_scrollregion)

        self.chat_frame.bind("<Configure>", self.adjust_message_widths)

        self.typing_label = tk.Label(
            self.chat_inner_frame,
            text="",
            font=("Courier New", 10, "italic"),
            fg="#00ccaa",
            bg=self.bg_colors[1]
        )

        self.input_frame = tk.Frame(self.main_frame, bg=self.bg_colors[0])
        self.input_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=10)
        self.input_frame.columnconfigure(0, weight=1)
        self.input_frame.columnconfigure(1, weight=0)

        self.entry = tk.Entry(
            self.input_frame,
            font=("Courier New", 14),
            bg="#1c2526",
            fg="#00ffcc",
            insertbackground="#00ffcc",
            bd=2,
            relief=tk.FLAT,
            highlightthickness=2,
            highlightbackground="#00ffcc",
            highlightcolor="#00ffcc"
        )
        self.entry.grid(row=0, column=0, sticky="ew", padx=10, ipady=8)
        self.entry.insert(0, "Type your command...")
        self.entry.bind("<FocusIn>", self.clear_placeholder)
        self.entry.bind("<FocusOut>", self.restore_placeholder)
        self.entry.bind("<Return>", lambda event: self.submit_command())

        self.submit_button = tk.Button(
            self.input_frame,
            text="Send",
            command=self.submit_command,
            font=("Arial", 12, "bold"),
            bg="#00ffcc",
            fg="#0a0a0a",
            bd=0,
            relief=tk.FLAT,
            activebackground="#00ccaa",
            width=10
        )
        self.submit_button.grid(row=0, column=1, padx=10)
        self.submit_button.bind("<Enter>", lambda e: self.submit_button.config(bg="#00ccaa"))
        self.submit_button.bind("<Leave>", lambda e: self.submit_button.config(bg="#00ffcc"))
        self.submit_button.bind("<Button-1>", self.animate_button_click)

        self.append_to_chat("Jarvis: Greetings! I'm Jarvis, your AI companion. How can I assist you today?", is_jarvis=True)

    def update_scrollregion(self, event):
        try:
            self.root.update_idletasks()
            self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all"))
            self.chat_canvas.yview_moveto(1.0)
            logging.info("Scroll region updated.")
        except Exception as e:
            logging.error(f"Error updating scroll region: {e}")
            print(f"DEBUG: Error updating scroll region: {e}")

    def clear_placeholder(self, event):
        if self.entry.get() == "Type your command...":
            self.entry.delete(0, tk.END)
            self.entry.config(fg="#00ffcc")

    def restore_placeholder(self, event):
        if not self.entry.get():
            self.entry.insert(0, "Type your command...")
            self.entry.config(fg="#888888")

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        if self.is_dark_mode:
            self.bg_colors = ["#0a0a0a", "#1c2526"]
            self.toggle_button.config(text="Toggle Light Mode")
        else:
            self.bg_colors = ["#e0e0e0", "#ffffff"]
            self.toggle_button.config(text="Toggle Dark Mode")
        self.root.config(bg=self.bg_colors[0])
        self.main_frame.config(bg=self.bg_colors[0])
        self.chat_frame.config(bg=self.bg_colors[1])
        self.chat_canvas.config(bg=self.bg_colors[1])
        self.chat_inner_frame.config(bg=self.bg_colors[1])
        self.header_label.config(bg=self.bg_colors[0])
        self.input_frame.config(bg=self.bg_colors[0])
        self.typing_label.config(bg=self.bg_colors[1])
        for widget in self.chat_inner_frame.winfo_children():
            widget.config(bg=self.bg_colors[1])
        self.adjust_message_widths(None)

    def fade_in_widget(self, widget, alpha=0.0):
        try:
            if alpha < 1.0:
                widget.config(fg=f"#{int(alpha * 255):02x}ffcc")
                self.root.after(50, lambda: self.fade_in_widget(widget, alpha + 0.05))
        except Exception as e:
            logging.error(f"Error in fade_in_widget: {e}")
            print(f"DEBUG: Error in fade_in_widget: {e}")

    def animate_button_click(self, event):
        try:
            winsound.Beep(1000, 100)
            self.submit_button.config(relief=tk.SUNKEN)
            self.root.after(100, lambda: self.submit_button.config(relief=tk.FLAT))
        except Exception as e:
            logging.error(f"Error in animate_button_click: {e}")
            print(f"DEBUG: Error in animate_button_click: {e}")

    def show_typing_indicator(self):
        try:
            self.typing_label.config(text="Jarvis is typing...")
            self.typing_label.pack(anchor="w", padx=10, pady=5, fill=tk.X)
            self.chat_canvas.yview_moveto(1.0)
            self.root.update_idletasks()
            logging.info("Typing indicator shown.")
        except Exception as e:
            logging.error(f"Error showing typing indicator: {e}")
            print(f"DEBUG: Error showing typing indicator: {e}")

    def hide_typing_indicator(self):
        try:
            self.typing_label.config(text="")
            self.typing_label.pack_forget()
            self.root.update_idletasks()
            logging.info("Typing indicator hidden.")
        except Exception as e:
            logging.error(f"Error hiding typing indicator: {e}")
            print(f"DEBUG: Error hiding typing indicator: {e}")

    def adjust_message_widths(self, event):
        try:
            canvas_width = self.chat_canvas.winfo_width() - 20
            max_width = max(200, int(canvas_width * 0.7))
            for msg_frame in self.chat_inner_frame.winfo_children():
                if msg_frame == self.typing_label:
                    continue
                try:
                    msg_label = msg_frame.winfo_children()[0]
                    msg_label.config(wraplength=max_width)
                    msg_frame.config(width=max_width)
                except IndexError:
                    logging.error("IndexError in adjust_message_widths: No label in msg_frame")
            self.root.update_idletasks()
        except Exception as e:
            logging.error(f"Error adjusting message width: {e}")
            print(f"DEBUG: Error adjusting message width: {e}")

    def append_to_chat(self, text, is_jarvis=False):
        try:
            msg_frame = tk.Frame(self.chat_inner_frame, bg=self.bg_colors[1])
            msg_frame.pack(fill=tk.X, padx=10, pady=5)
            msg_frame.columnconfigure(0, weight=1)
            msg_frame.columnconfigure(1, weight=0 if is_jarvis else 1)
            msg_frame.columnconfigure(2, weight=1 if is_jarvis else 0)
            bg_color = "#00ccaa" if is_jarvis else "#2e3b3e"
            fg_color = "#0a0a0a" if is_jarvis else "#00ffcc"
            anchor = "w" if is_jarvis else "e"
            msg_label = tk.Label(
                msg_frame,
                text=text,
                font=("Courier New", 12),
                bg=bg_color,
                fg=fg_color,
                justify="left" if is_jarvis else "right",
                padx=10,
                pady=5,
                relief=tk.RAISED,
                bd=2,
                anchor=anchor,
                wraplength=int(self.chat_canvas.winfo_width() * 0.7) or 200
            )
            msg_label.grid(row=0, column=1 if is_jarvis else 2, sticky=anchor, pady=2)
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            ts_label = tk.Label(
                msg_frame,
                text=timestamp,
                font=("Courier New", 8),
                fg="#888888",
                bg=self.bg_colors[1],
                anchor=anchor
            )
            ts_label.grid(row=1, column=1 if is_jarvis else 2, sticky=anchor)
            self.chat_canvas.yview_moveto(1.0)
            self.root.update_idletasks()
            logging.info(f"Appended to chat: {text}")
            print(f"DEBUG: Appended to chat: {text}")
            return msg_frame, msg_label  # Return for use in type_response
        except Exception as e:
            logging.error(f"Error appending to chat: {e}")
            print(f"DEBUG: Error appending to chat: {e}")
            return None, None

    def animate_message_slide(self, widget, x):
        try:
            if (x < 0 and widget.winfo_x() < 0) or (x > 0 and widget.winfo_x() > 0):
                widget.place_configure(x=widget.winfo_x() - x//10)
                self.root.after(20, lambda: self.animate_message_slide(widget, x))
            else:
                widget.place_configure(x=0)
                widget.pack(fill=tk.X, padx=10, pady=5)
                self.adjust_message_widths(None)
                self.root.update_idletasks()
                logging.info("Message slide animation completed.")
        except Exception as e:
            logging.error(f"Error in message slide animation: {e}")
            print(f"DEBUG: Error in message slide animation: {e}")

    def submit_command(self):
        try:
            user_input = self.entry.get().strip()
            if user_input and user_input != "Type your command...":
                self.append_to_chat("You: " + user_input)
                self.entry.delete(0, tk.END)
                if user_input.lower() == "exit":
                    self.root.quit()
                else:
                    self.show_typing_indicator()
                    self.process_and_respond(user_input)
        except Exception as e:
            logging.error(f"Error in submit_command: {e}")
            print(f"DEBUG: Error in submit_command: {e}")

    def process_and_respond(self, user_input):
        try:
            response = process_query(user_input)
            self.hide_typing_indicator()
            if not response:
                response = "Sorry, I didn't understand the command or the AI service is unavailable."
                logging.warning(f"Empty response for query: {user_input}")
            print(f"DEBUG: Response to display: {response}")
            self.type_response(response)
        except Exception as e:
            logging.error(f"Error in process_and_respond: {e}")
            print(f"DEBUG: Error in process_and_respond: {e}")
            self.hide_typing_indicator()
            self.append_to_chat("Jarvis: An error occurred while processing your request.", is_jarvis=True)

    def type_response(self, text):
        try:
            print(f"DEBUG: Displaying response: {text}")
            # Display the full response directly
            frame, label = self.append_to_chat("Jarvis: " + text, is_jarvis=True)
            if frame and label:
                self.root.update_idletasks()
                logging.info("Response displayed successfully.")
            else:
                logging.error("Failed to create message frame or label.")
                print("DEBUG: Failed to create message frame or label.")
        except Exception as e:
            logging.error(f"Error in type_response: {e}")
            print(f"DEBUG: Error in type_response: {e}")
            # Fallback: Try appending directly
            self.append_to_chat("Jarvis: " + text, is_jarvis=True)

# ---------------------- Additional Functions ----------------------
def speak_and_type(text, gui):
    logging.info(f"AI: {text}")
    print("AI:", text)
    try:
        engine.say(text[:300])
        engine.runAndWait()
    except Exception as e:
        print("❌ Voice error:", e)
        logging.error(f"Voice error: {e}")
    gui.root.after(0, gui.type_response, text)

def get_weather():
    try:
        city = "Kannur"
        api_key = "a87d91d0b889d1865fd01f916814a534"
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        data = requests.get(url, timeout=5).json()
        temp = data["main"]["temp"]
        desc = data["weather"][0]["description"]
        return f"The weather in {city} is {desc} with a temperature of {temp}°C."
    except Exception as e:
        logging.error(f"Weather fetch error: {e}")
        return "Sorry, I couldn't fetch the weather."

def process_query(query):
    query = query.lower()
    logging.info(f"User: {query}")
    responses = []
    commands = query.split(" and ")
    for cmd in commands:
        cmd = cmd.strip()
        logging.info(f"Processing command: {cmd}")
        if cmd.startswith("type "):
            try:
                to_type = cmd[5:].strip()
                pyautogui.write(to_type, interval=0.05)
                pyautogui.press("enter")
                responses.append(f"Typed {to_type} and pressed Enter.")
            except Exception as e:
                logging.error(f"Type command error: {e}")
                responses.append("Error typing the text.")
        elif "open youtube" in cmd:
            webbrowser.open("https://youtube.com")
            responses.append("Opening YouTube.")
        elif "who are" in cmd:
            responses.append("I am Jarvis, your personal assistant...")
        elif "open telegram" in cmd:
            webbrowser.open("https://web.telegram.org")
            responses.append("Opening Telegram.")
        elif "search youtube for" in cmd:
            q = cmd.replace("search youtube for", "").strip()
            webbrowser.open(f"https://www.youtube.com/results?search_query={q}")
            responses.append(f"Searching YouTube for {q}.")
        elif "open google" in cmd:
            webbrowser.open("https://google.com")
            responses.append("Opening Google.")
        elif "search google for" in cmd:
            q = cmd.replace("search google for", "").strip()
            webbrowser.open(f"https://www.google.com/search?q={q}")
            responses.append(f"Searching Google for {q}.")
        elif "open whatsapp" in cmd:
            webbrowser.open("https://web.whatsapp.com")
            responses.append("Opening WhatsApp.")
        elif "weather" in cmd:
            responses.append(get_weather())
        elif "battery" in cmd:
            battery = psutil.sensors_battery()
            if battery:
                responses.append(f"Battery is at {battery.percent}% and {'charging' if battery.power_plugged else 'not charging'}.")
            else:
                responses.append("Unable to retrieve battery information.")
        elif "voice mode" in cmd:
            root.destroy()
            subprocess.Popen(["python", "o.py"])
        elif "simple osint" in cmd:
            subprocess.Popen(["python", "s.py"])
            responses.append("Running Simple OSINT tool.")
        elif "osint power" in cmd:
            subprocess.Popen(["python", "Seint.py"])
            responses.append("Running OSINT Power tool.")
        elif "ip address" in cmd:
            try:
                ip = socket.gethostbyname(socket.gethostname())
                responses.append(f"Your IP address is {ip}.")
            except Exception as e:
                logging.error(f"IP address error: {e}")
                responses.append("Unable to get IP address.")
        elif "shutdown" in cmd:
            os.system("shutdown /s /t 5")
            responses.append("Shutting down.")
        elif "restart" in cmd:
            os.system("shutdown /r /t 5")
            responses.append("Restarting PC.")
        elif "screenshot" in cmd:
            try:
                with mss.mss() as sct:
                    filename = f"screenshot_{int(time.time())}.png"
                    sct.shot(output=filename)
                    responses.append(f"Screenshot saved as {filename}.")
            except Exception as e:
                logging.error(f"Screenshot error: {e}")
                responses.append("Screenshot failed.")
        elif "open notepad" in cmd:
            os.system("notepad")
            responses.append("Opening Notepad.")
        elif "open beast" in cmd or "launch" in cmd:
            beast_path = "C:\\Users\\Devajith\\Desktop\\Website\\school_website\\Latest\\__pycache__\\beast.py"
            if os.path.exists(beast_path):
                try:
                    subprocess.Popen(["python", beast_path])
                    responses.append("Launching Beast 3.0.")
                except Exception as e:
                    logging.error(f"Beast launch error: {e}")
                    responses.append("Failed to launch Beast 3.0.")
            else:
                logging.error(f"Beast.py not found at {beast_path}")
                responses.append("Beast 3.0 not found on this system.")
        elif "osint" in cmd or "run osint" in cmd:
            beast_path = "C:\\Users\\Devajith\\Desktop\\Website\\school_website\\Latest\\__pycache__\\beast.py"
            if os.path.exists(beast_path):
                try:
                    subprocess.Popen(["python", beast_path])
                    responses.append("Running OSINT tool.")
                except Exception as e:
                    logging.error(f"OSINT tool error: {e}")
                    responses.append("Failed to run OSINT tool.")
            else:
                logging.error(f"Beast.py not found at {beast_path}")
                responses.append("OSINT tool not found on this system.")
        elif "who is" in cmd:
            responses.append("He is the most intelligent human in the world!...")
        elif "time" in cmd:
            responses.append(datetime.datetime.now().strftime("The time is %I:%M %p."))
        elif "date" in cmd:
            responses.append(datetime.date.today().strftime("Today's date is %B %d, %Y."))
        elif cmd.lower() in ["press", "enter", "press enter", "okay please press enter"]:
            try:
                pyautogui.press("enter")
                responses.append("Pressed Enter.")
            except Exception as e:
                logging.error(f"Enter press error: {e}")
                responses.append("Failed to press Enter.")
        else:
            if co is None:
                responses.append("AI service unavailable: Failed to initialize Cohere client.")
                logging.error("Cohere client is not initialized.")
            else:
                try:
                    response = co.chat(model="command-r", message=cmd, temperature=0.6)
                    responses.append(response.text)
                except cohere.CohereAPIError as e:
                    logging.error(f"Cohere API error: {e}")
                    responses.append(f"AI response failed: {e.message}")
                except Exception as e:
                    logging.error(f"Unexpected error in Cohere API call: {e}")
                    responses.append("AI response failed: An unexpected error occurred.")

    response_text = " ".join(responses)
    if not response_text:
        response_text = "Sorry, I didn't understand the command."
        logging.warning("Empty response generated.")
    logging.info(f"Final response: {response_text}")
    return response_text

# ---------------------- Main ----------------------
if __name__ == "__main__":
    root = tk.Tk()
    gui = JarvisGUI(root)
    root.mainloop()