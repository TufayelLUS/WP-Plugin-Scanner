import re
import requests
import customtkinter as ctk
from tkinter import messagebox
from threading import Thread, Semaphore


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("WordPress Plugin Detector")
        self.geometry("500x550")
        self.resizable(False, False)

        # Mode Selection
        self.mode_label = ctk.CTkLabel(self, text="Select Mode:")
        self.mode_label.pack(pady=5)

        self.mode_var = ctk.StringVar(value="Single")
        self.mode_dropdown = ctk.CTkComboBox(
            self, values=["Single", "Bulk"], command=self.update_mode, variable=self.mode_var, state="readonly"
        )
        self.mode_dropdown.pack(pady=5)

        # Single Mode UI
        self.url_label = ctk.CTkLabel(self, text="Enter Website URL:")
        self.url_entry = ctk.CTkEntry(self, width=450)
        self.scan_button = ctk.CTkButton(self, text="Scan Website", command=self.scan_website_threaded)
        self.result_textbox = ctk.CTkTextbox(self, width=450, height=200, state="disabled")

        # Bulk Mode UI
        self.bulk_label = ctk.CTkLabel(self, text="Enter Websites (one per line):")
        self.bulk_entry = ctk.CTkTextbox(self, width=450, height=100)
        self.thread_label = ctk.CTkLabel(self, text="Threads:")
        self.thread_var = ctk.StringVar(value="5")
        self.thread_count = ctk.CTkEntry(self, width=50, textvariable=self.thread_var, validate="key", validatecommand=(self.register(self.validate_number_input), "%P"))
        self.bulk_scan_button = ctk.CTkButton(self, text="Scan Bulk Websites", command=self.scan_bulk_threaded)
        self.bulk_result_textbox = ctk.CTkTextbox(self, width=450, height=200, state="disabled")

        # Set Default UI (Single Mode)
        self.update_mode()

    def validate_number_input(self, input_value):
        try:
            # Check if the input is a number and >= 1
            if input_value.strip() == "" or int(input_value) >= 1:
                return True
            else:
                return False
        except ValueError:
            return False

    def update_mode(self, *_):
        """Update UI based on mode selection."""
        mode = self.mode_var.get()

        # Hide all widgets first
        for widget in [self.url_label, self.url_entry, self.scan_button, self.result_textbox,
                       self.bulk_label, self.bulk_entry, self.thread_label, self.thread_count,
                       self.bulk_scan_button, self.bulk_result_textbox]:
            widget.pack_forget()

        if mode == "Single":
            self.url_label.pack(pady=5)
            self.url_entry.pack(pady=5)
            self.scan_button.pack(pady=5)
            self.result_textbox.pack(pady=5)
        else:
            self.bulk_label.pack(pady=5)
            self.bulk_entry.pack(pady=5)
            self.thread_label.pack(pady=5)
            self.thread_count.pack(pady=5)
            self.bulk_scan_button.pack(pady=5)
            self.bulk_result_textbox.pack(pady=5)

    def scan_website(self):
        """Single mode website scan."""
        self.scan_button.configure(state="disabled")
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Input Error", "Please enter a website URL.")
            self.scan_button.configure(state="normal")
            return

        self.result_textbox.configure(state="normal")
        self.result_textbox.delete("1.0", "end")

        plugins_found = self.detect_wp_plugins(url)

        if plugins_found is None:
            messagebox.showerror("Error", "Failed to access the website.")
        elif not plugins_found:
            messagebox.showinfo("No Plugins Found", "No detectable plugins were found.")
        else:
            self.result_textbox.insert("end", "Detected Plugins:\n\n")
            for plugin in plugins_found:
                self.result_textbox.insert("end", f"- {plugin}\n")

        self.result_textbox.configure(state="disabled")
        self.scan_button.configure(state="normal")

    def scan_website_threaded(self):
        """Run single mode scan in a separate thread."""
        thread = Thread(target=self.scan_website)
        thread.daemon = True
        thread.start()

    def scan_bulk_threaded(self):
        """Run bulk mode scan with threading."""
        thread = Thread(target=self.scan_bulk)
        thread.daemon = True
        thread.start()

    def scan_bulk(self):
        """Bulk mode website scan with threading."""
        urls = self.bulk_entry.get("1.0", "end").strip().split("\n")
        urls = [url.strip() for url in urls if url.strip()]
        
        if not urls:
            messagebox.showwarning("Input Error", "Please enter at least one website URL.")
            return

        try:
            num_threads = int(self.thread_count.get().strip())
            if num_threads < 1:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Input Error", "Please enter a valid number of threads.")
            return

        self.bulk_scan_button.configure(state="disabled")
        self.bulk_result_textbox.configure(state="normal")
        self.bulk_result_textbox.delete("1.0", "end")

        semaphore = Semaphore(num_threads)

        def process_url(url):
            """Process a single URL in bulk mode."""
            with semaphore:
                plugins_found = self.detect_wp_plugins(url)
                result = f"{url}:\n"
                if plugins_found is None:
                    result += "  - Failed to access the website.\n\n"
                elif not plugins_found:
                    result += "  - No detectable plugins found.\n\n"
                else:
                    result += "  - Detected Plugins:\n"
                    for plugin in plugins_found:
                        result += f"    - {plugin}\n"
                    result += "\n"

                self.bulk_result_textbox.insert("end", result)

        threads = []
        for url in urls:
            thread = Thread(target=process_url, args=(url,))
            thread.daemon = True
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        self.bulk_result_textbox.configure(state="disabled")
        self.bulk_scan_button.configure(state="normal")

    def detect_wp_plugins(self, url):
        """Detect WordPress plugins from a given URL."""
        if not url.lower().startswith(("http://", "https://")):
            url = "http://" + url
        try:
            response = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
            if response.status_code != 200:
                return None

            plugins = set(re.findall(r"/wp-content/plugins/([^/]+)/", response.text))
            return list(plugins) if plugins else []

        except:
            return None


if __name__ == "__main__":
    app = App()
    app.mainloop()
