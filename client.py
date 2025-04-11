import tkinter as tk
import threading
import socket
import queue

class ChatClient:
    def __init__(self, master):
        self.master = master
        self.running = True

        self.name = self.ask_name()
        self.master.title(f"Client {self.name}")
        self.data_queue = queue.Queue()

        # Text area for chat history (read-only)
        self.chat_area = tk.Text(master, state='disabled', height=20, width=50, wrap='word')
        self.chat_area.pack(padx=10, pady=5)
        self.chat_area.tag_config("self", foreground="blue")

        # Entry box for input
        self.input_box = tk.Text(master, height=3, width=50)
        self.input_box.pack(padx=10, pady=5)
        self.input_box.bind("<Return>", self.send_message_event)
        self.input_box.bind("<Shift-Return>", self.insert_newline)

        # Connect to server
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client_socket.connect(("127.0.0.1", 5000))
        except Exception as e:
            self.append_chat(f"[Error] Unable to connect: {e}")
            return

        # Start receiving thread
        self.receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
        self.receive_thread.start()

        # Start GUI update loop
        self.update_gui()
        self.master.protocol("WM_DELETE_WINDOW", self.close)

    def ask_name(self):
        name_prompt = tk.Toplevel(self.master)
        name_prompt.title("Enter Name")

        tk.Label(name_prompt, text="Enter your name:").pack(padx=10, pady=5)
        name_var = tk.StringVar()

        entry = tk.Entry(name_prompt, textvariable=name_var)
        entry.pack(padx=10, pady=5)
        entry.focus()

        def submit_name():
            name_prompt.destroy()

        entry.bind("<Return>", lambda event: submit_name())
        tk.Button(name_prompt, text="OK", command=submit_name).pack(pady=5)

        self.master.wait_window(name_prompt)
        return name_var.get() or "Anonymous"

    def insert_newline(self, event):
        self.input_box.insert(tk.INSERT, "\n")
        return "break"

    def send_message_event(self, event):
        self.send_message()
        return "break"

    def send_message(self):
        message = self.input_box.get("1.0", tk.END).strip()
        if message:
            full_message = f"{self.name}: {message}"
            try:
                self.client_socket.sendall(full_message.encode())
                self.append_chat(full_message, tag="self")
                self.input_box.delete("1.0", tk.END)
            except Exception as e:
                self.append_chat(f"[Error sending message] {e}")

    def receive_messages(self):
        try:
            while self.running:
                data = self.client_socket.recv(1024)
                if not data:
                    break
                self.data_queue.put(data.decode())
        except Exception as e:
            self.data_queue.put(f"[Error] {e}")
        finally:
            self.data_queue.put("[Disconnected from server]")
            self.close()


    def update_gui(self):
        try:
            while True:
                message = self.data_queue.get_nowait()
                self.append_chat(message)
        except queue.Empty:
            pass
        if self.running:
            self.master.after(100, self.update_gui)

    def append_chat(self, message, tag=None):
        self.chat_area.configure(state='normal')
        self.chat_area.insert(tk.END, message + "\n", tag)
        self.chat_area.see(tk.END)
        self.chat_area.configure(state='disabled')


    def close(self):
        self.running = False
        try:
            self.client_socket.close()
        except:
            pass
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    app = ChatClient(root)
    root.deiconify()  # Show the main window after name is entered
    root.mainloop()
