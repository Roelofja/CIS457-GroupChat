# CIS457 Group Chat Project
**Authors:** Jayden Roelofs, Chris Lamus

## Roles
Roles assigned to the members of the group:

> Jayden - In Charge of Server

> Chris - In Charge of Client

## Server Architecture

### `handleclient()`

```python
def handleClient(sock, addr, clients):
    print(f"[+] New connection from {addr}")
    try:
        while True:
            try:
                data = sock.recv(1024)
                if not data:
                    break  # clean disconnect
            except ConnectionResetError:
                print(f"[!] Client {addr} disconnected.")
                break

            # Broadcast message to all other clients
            for client in clients:
                if client != sock:
                    try:
                        client.sendall(data)
                    except:
                        pass  # ignore broken pipe or other issues
    finally:
        print(f"[-] Closing connection from {addr}")
        if sock in clients:
            clients.remove(sock)
        sock.close()
```
The `handleclient()` function takes in the socket connection, connection address, and list of connected client sockets. It starts by reading in up to 1024 bytes from the client socket and storing it in `data`. A for loop then loops through all of the currently connected sockets and sends the data to each one, excluding the socket of the sender. Once the while loop is broken out of, i.e. the associated client disconnects or is terminated, it's socket is closed and removed from the list of connections.

### `main()`

```python
def main():
    host = '0.0.0.0'
    port = 5000  # listen on port 5000

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    server_socket.settimeout(1.0)  # 1 second
    print(f"[+] Server listening on {host}:{port}")

    clients = []  # list to keep track of connected client sockets

    try:
        while True:
            try:
                conn, addr = server_socket.accept()
                clients.append(conn)
                t = Thread(target=handleClient, args=(conn, addr, clients))
                t.daemon = True
                t.start()
            except socket.timeout:
                continue  # allows us to break the loop with Ctrl+C
    except KeyboardInterrupt:
        print("[!] Server shutting down...")
    finally:
        for client in clients:
            client.close()
        server_socket.close()
```
Here, the `host` and `port` is defined. `host` is 0.0.0.0 to listen to all available network interfaces, and `port` is arbitrarily set to 5000. A server socket is created with `server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)` and then is binded to the `host` and `port`. A timeout for incomming connections is set in order for the later `.accept()` call to not block and allow CTRL+C to terminate the server if desired. The clients list is then created under `clients` to store the connected sockets. `conn, addr = server_socket.accept()` then waits for a new socket connection. On connection, the `conn` connection socket is added to the list of connected clients and a new `handleClient` thread is created and supplied the connection socket, connection address, and client list. When the server is terminated or closed, each client socket is closed with a for loop before finally closing the server socket.
## Client Architecture

The client is implemented using a `ChatClient` class.
### `__init__()`
```python 
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
```

This function initializes the GUI client, sets up the connection, and starts listening for messages. First the function, sets the window title using the client’s name. Then it initializes text widgets for chat display and input. Then it connects to the server using a socket (127.0.0.1:5000 by default). A receive thread is started with the `receive_messages` function and then the GUI refresh loop is started with `update_gui()`. Finally it registers the close protocol for safe exit.

### `ask_name()`
```python 
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
```
This function opens a toplevel window to prompt the user for their name.

It returns: String – The user's name or "Anonymous" if none provided.

### `insert_newline()`
```python
def insert_newline(self, event):
        self.input_box.insert(tk.INSERT, "\n")
        return "break"
```
Handles Shift + Return to insert a new line in the message input.

Returns: "break" to prevent default behavior.

### `send_message_event()`
```python
def send_message_event(self, event):
        self.send_message()
        return "break"
```
Handles Return key to send a message.

Returns: "break"

### `send_message()`
```python
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
```

Collects the message from the input box and sends it to the server. First it strip trailing newlines. Then it formats the message with the username. It then sends the message over the socket. It is also displayed in local chat area by tagging the message as yourself. The input box is then finally cleared.

### `receive_messages()`
```python
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
```
this funnciton runs in a background thread to receive messages from the server. IT first waits for data from the server. Then pushes it into a thread-safe queue (`self.data_queue`) for the GUI to process. Finally, if there is a disconnect or error, displays a message and calls `self.close()`.

### `update_gui()`
```python
def update_gui(self):
        try:
            while True:
                message = self.data_queue.get_nowait()
                self.append_chat(message)
        except queue.Empty:
            pass
        if self.running:
            self.master.after(100, self.update_gui)
```
Periodically checks the queue for new messages and appends them to the chat. This
runs every 100ms using `.after()`. It keeps the UI responsive while messages come in asynchronously.

### `append_chat()`
```python
def append_chat(self, message, tag=None):
        self.chat_area.configure(state='normal')
        self.chat_area.insert(tk.END, message + "\n", tag)
        self.chat_area.see(tk.END)
        self.chat_area.configure(state='disabled')
```
Adds a line of text to the chat window.

Arguments:

- message: The message to display.

- tag: Optional – applies a tag (e.g., "self" for styling your own messages).

### `close()`
```python
def close(self):
        self.running = False
        try:
            self.client_socket.close()
        except:
            pass
        self.master.destroy()
```
Cleanly closes the socket and destroys the Tkinter window.
This is called when the user closes the window or a disconnect occurs.

### `main()`
```python
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    app = ChatClient(root)
    root.deiconify()  # Show the main window after name is entered
    root.mainloop()
```
The main creates a new tkinter widget, hides it, gives it to the `ChatClient` class, then shows it again once the name has been entered. Finally the tkinter main loop is called.