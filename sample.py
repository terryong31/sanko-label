import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
import mysql.connector
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as pdf_canvas
import os
from pathlib import Path
import webbrowser

def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="sanko",
        use_pure=True,  
    )

def create_users_table():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT PRIMARY KEY,
            username VARCHAR(255) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL
        )
    """)

    cursor.execute("""
        INSERT IGNORE INTO users (id, username, password)
        VALUES (1, 'admin', 'pass123')
    """)
    conn.commit()
    conn.close()

class LoginApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Login System")
        self.root.geometry("300x270")
        self.root.resizable(False, False)

        create_users_table()
        self.create_widgets()

    def create_widgets(self):
        main_frame = tk.Frame(self.root)
        main_frame.pack(padx=20, pady=20, fill='both', expand=True)

        tk.Label(main_frame, text="Login", font=("Arial", 16, "bold")).pack(pady=10)

        tk.Label(main_frame, text="Username:").pack()
        self.username_entry = tk.Entry(main_frame, width=25)
        self.username_entry.pack(pady=5)

        tk.Label(main_frame, text="Password:").pack()
        self.password_entry = tk.Entry(main_frame, width=25, show="*")
        self.password_entry.pack(pady=5)

        tk.Button(main_frame, text="Login", command=self.verify_login, width=15).pack(pady=20)

    def verify_login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showerror("Error", "All fields are required!")
            return

        try:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM users 
                WHERE username = %s AND password = %s
            """, (username, password))
            user = cursor.fetchone()
            conn.close()

            if user:
                messagebox.showinfo("Success", "Login successful!")
                self.root.destroy()
                root = tk.Tk()
                app = TransferNoteApp(root, username, user[0])
                root.mainloop()
            else:
                messagebox.showerror("Error", "Invalid credentials!")

        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error: {err}")

class TransferNoteApp:
    def __init__(self, root, username, user_id):
        self.root = root
        self.username = username
        self.user_id = user_id
        self.root.title("Transfer Note")
        
        self.root.geometry("450x440")
        self.root.minsize(420, 420)
        
        self.create_tn_table()
        self.part_numbers = self.get_part_numbers()
        self.data = {}
        self.tn_no = None

        self.create_widgets()

    def create_tn_table(self):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS TN_table (
                TN_id INT AUTO_INCREMENT PRIMARY KEY,
                Prdcode VARCHAR(255),
                Quantity INT,
                LotNo VARCHAR(255),
                MachineNo VARCHAR(255),
                DatePrinted DATE
            )
        """)
        conn.commit()
        conn.close()
        return

    def get_part_numbers(self):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT Prdcode FROM information")
        parts = [row[0] for row in cursor.fetchall()]
        conn.close()
        return parts

    def get_info_by_part(self, part_number):
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        # Normalize part_number: strip whitespace and make case-insensitive
        part_number = part_number.strip()
        # Use LOWER() for case-insensitive comparison
        query = "SELECT * FROM information WHERE LOWER(Prdcode) = LOWER(%s)"
        cursor.execute(query, (part_number,))
        rows = cursor.fetchall()
        conn.close()
        return rows

    def get_latest_tn_number(self):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(TN_id) FROM TN_table")
        latest_tn = cursor.fetchone()[0]  
        conn.close()
        return latest_tn if latest_tn is not None else 0 

    def create_widgets(self):
        self.fields = {}

        main_frame = tk.Frame(self.root)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.columnconfigure(2, weight=1)
        main_frame.columnconfigure(3, weight=1)
        
        row = 0
        label = tk.Label(main_frame, text="Transfer Note", font=("Arial", 14, "bold"))
        label.grid(row=row, column=0, columnspan=4, sticky='ew')
        
        row += 1
        label2 = tk.Label(main_frame, text="Molding - FGP & Weighing Part", font=("Arial", 10))
        label2.grid(row=row, column=0, columnspan=4, sticky='ew')

        row += 1
        tk.Label(main_frame, text=f"User: {self.username} (ID: {self.user_id})", font=("Arial", 10, "italic")).grid(
            row=row, column=0, columnspan=4, sticky='ew', pady=8)

        row += 1
        tk.Label(main_frame, text="Date:", anchor='e').grid(
            row=row, column=0, sticky='e', padx=5, pady=2)
        self.fields['Date'] = tk.Label(main_frame, text=str(date.today()))
        self.fields['Date'].grid(row=row, column=1, sticky='w', padx=5, pady=2)

        tk.Label(main_frame, text="TN No:", anchor='e').grid(
            row=row, column=2, sticky='e', padx=5, pady=2)

        latest_tn = self.get_latest_tn_number()
        self.fields['TN No'] = tk.Label(main_frame, text=str(latest_tn + 1) if latest_tn is not None else "1")
        self.fields['TN No'].grid(row=row, column=3, sticky='w', padx=5, pady=2)

        row += 1
        tk.Label(main_frame, text="Part Number:", anchor='e').grid(
            row=row, column=0, sticky='e', padx=5, pady=2)
        self.part_dropdown = ttk.Combobox(main_frame, values=self.part_numbers, width=30)
        self.part_dropdown.grid(row=row, column=1, columnspan=2, sticky='w', padx=5, pady=2)
        self.part_dropdown.bind("<<ComboboxSelected>>", self.load_part_data)

        select_button = tk.Button(main_frame, text="Select Part", command=self.open_part_selection)
        select_button.grid(row=row, column=3, sticky='e', padx=5, pady=2)

        labels = [
            ("Customer", 'Custname'), ("Part Name", 'Prddesc'),
        ]

        for text, key in labels:
            row += 1
            tk.Label(main_frame, text=f"{text}:", anchor='e').grid(
                row=row, column=0, sticky='e', padx=5, pady=2)
            self.fields[key] = tk.Label(main_frame, text="", anchor='w')
            self.fields[key].grid(row=row, column=1, columnspan=3, sticky='w', padx=5, pady=2)

        row += 1
        tk.Label(main_frame, text="PUM (Std Pack Qty):", anchor='e').grid(
            row=row, column=0, sticky='e', padx=5, pady=2)
        self.pum_var = tk.StringVar()
        self.pum_dropdown = ttk.Combobox(main_frame, textvariable=self.pum_var, width=30)
        self.pum_dropdown.grid(row=row, column=1, columnspan=3, sticky='w', padx=5, pady=2)

        row += 1
        tk.Label(main_frame, text="No of Boxes:", anchor='e').grid(
            row=row, column=0, sticky='e', padx=5, pady=2)
        self.boxes_entry = tk.Entry(main_frame, width=32)
        self.boxes_entry.grid(row=row, column=1, columnspan=3, sticky='w', padx=5, pady=2)

        row += 1
        tk.Label(main_frame, text="Prod Lot No:", anchor='e').grid(
            row=row, column=0, sticky='e', padx=5, pady=2)
        self.prod_lot_entry = tk.Entry(main_frame, width=32)
        self.prod_lot_entry.grid(row=row, column=1, columnspan=3, sticky='w', padx=5, pady=2)

        row += 1
        tk.Label(main_frame, text="Remark:", anchor='e').grid(
            row=row, column=0, sticky='e', padx=5, pady=2)
        self.remark = tk.Entry(main_frame, width=32)
        self.remark.grid(row=row, column=1, columnspan=3, sticky='w', padx=5, pady=2)

        row += 1
        tk.Label(main_frame, text="Job Order No:", anchor='e').grid(
            row=row, column=0, sticky='e', padx=5, pady=2)
        self.job_order_entry = tk.Entry(main_frame, width=32)
        self.job_order_entry.grid(row=row, column=1, columnspan=3, sticky='w', padx=5, pady=2)

        row += 1
        tk.Label(main_frame, text="Machine No:", anchor='e').grid(
            row=row, column=0, sticky='e', padx=5, pady=2)
        self.machine_entry = tk.Entry(main_frame, width=32)
        self.machine_entry.grid(row=row, column=1, columnspan=3, sticky='w', padx=5, pady=2)

        button_frame = tk.Frame(self.root)
        button_frame.pack(side='bottom', fill='x', padx=10, pady=10)
        
        preview = tk.Button(button_frame, text="Preview", command=self.preview, width=15)
        preview.pack(side='left', padx=5)
        
        save_n_print = tk.Button(button_frame, text="Save & Print", command=self.save_and_print, width=15)
        save_n_print.pack(side='right', padx=5)

    def open_part_selection(self):
        PartSelectionWindow(self)

    def load_part_data(self, event):
        part_number = self.part_dropdown.get()
        if not part_number:
            messagebox.showerror("Error", "Please select a part number!")
            return

        rows = self.get_info_by_part(part_number)
        if not rows:
            messagebox.showerror("Not found", f"Part Number '{part_number}' not found in database")
            return

        self.data = rows[0]
        for key, widget in self.fields.items():
            if key in self.data:
                widget.config(text=str(self.data[key]))

        pum_values = sorted(set(row['PUM'] for row in rows if row['PUM'] is not None))
        self.pum_dropdown.config(values=pum_values)
        if len(pum_values) == 1:
            self.pum_var.set(pum_values[0])
        else:
            self.pum_var.set("")

    def generate_pdf(self, tn_no="(Will be assigned when printed)", quantity=None):
        conn = connect_db()
        cursor = conn.cursor()
        get_latest_tn_number = "SELECT MAX(TN_id) FROM TN_table"
        cursor.execute(get_latest_tn_number)
        latest_tn_number = cursor.fetchone()
        conn.close()
        docs_path = Path.home() / "Documents" / "TransferNotes"
        docs_path.mkdir(parents=True, exist_ok=True)
        pdf_filename = f"tn_no_{tn_no}.pdf" if tn_no != "(Will be assigned when printed)" else "preview.pdf"
        pdf_path = docs_path / pdf_filename

        c = pdf_canvas.Canvas(str(pdf_path), pagesize=A4)
        width, height = A4
        y = height - 40
        y_axis = 24.5

        my_width = 300
        c.setFont("Helvetica", 6)
        transfer_id = "F-J511-41"
        c.drawString(my_width, height - 22, transfer_id)

        transfer_note = "Transfer Note"
        c.drawString(my_width, height - 29, transfer_note)

        transfer_no = f"TN No: {tn_no}" if tn_no != "(Will be assigned when printed)" else f"TN No: Preview"
        c.drawString(my_width, height - 40, transfer_no)
        c.setFont("Helvetica", 11.5)

        my_x = 98.5
        customer_name = self.fields['Custname'].cget("text") if self.fields['Custname'].cget("text") else " "
        c.drawString(my_x, y, f"{customer_name}")
        y -= y_axis

        part_name = self.fields['Prddesc'].cget("text") if self.fields['Prddesc'].cget("text") else " "
        c.drawString(my_x, y, f"{part_name}")
        y -= y_axis

        part_number = self.part_dropdown.get() if self.part_dropdown.get() else ""  # Fetch Prdcode from self.data
        c.drawString(my_x, y, f"{part_number}")
        y -= y_axis
        
        quantity_text = f"{quantity}" if quantity else " "
        c.drawString(my_x, y, quantity_text)
        y -= y_axis

        prod_lot_no = self.prod_lot_entry.get() if self.prod_lot_entry.get() else " "
        c.drawString(my_x, y, f"{prod_lot_no}")
        y -= y_axis

        remark = self.remark.get() if self.remark.get() else " "
        c.drawString(my_x, y, f"{remark}")
        y -= y_axis

        job_order = self.job_order_entry.get() if self.job_order_entry.get() else " "
        c.drawString(my_x, y, f"JOB ORDER NO: {job_order}")
        y -= y_axis + 6

        username = self.username if self.username else " "
        c.drawString(my_x, y, f"{username}")
        y -= y_axis

        c.drawString(my_x, y, f"{str(date.today())}")
        y -= y_axis

        machine_no = self.machine_entry.get() if self.machine_entry.get() else ""
        c.drawString(my_x, y, f"{machine_no}")
        y -= y_axis

        no_of_cartons = self.boxes_entry.get() if self.boxes_entry.get() else ""
        c.drawString(my_width + 10, height - 70, f"{no_of_cartons}")

        pum = self.pum_var.get() if self.pum_var.get() else ""
        c.drawString(my_width + 6, height - 120 , f"{pum}")

        c.save()
        return pdf_path

    def preview(self):
        try:
            pum = int(self.pum_var.get())
            boxes = int(self.boxes_entry.get())
            quantity = pum * boxes
        except ValueError:
            messagebox.showerror("Input Error", "PUM and Boxes must be integers")
            return

        pdf_path = self.generate_pdf(quantity=quantity)
        webbrowser.open_new(str(pdf_path))

    def save_and_print(self):
        try:
            pum = int(self.pum_var.get())
            boxes = int(self.boxes_entry.get())
            quantity = pum * boxes
        except ValueError:
            messagebox.showerror("Input Error", "PUM and Boxes must be integers")
            return

        part_number = self.part_dropdown.get()
        lot_no = self.prod_lot_entry.get()
        machine_no = self.machine_entry.get()

        try:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO TN_table (PartNumber, Quantity, LotNo, MachineNo, DatePrinted) VALUES (%s, %s, %s, %s, %s)",
                        (part_number, quantity, lot_no, machine_no, date.today()))
            conn.commit()
            cursor.execute("SELECT LAST_INSERT_ID()")
            self.tn_no = cursor.fetchone()[0]
            conn.close()

            latest_tn = self.get_latest_tn_number()
            self.fields['TN No'].config(text=str(latest_tn + 1) if latest_tn is not None else "1")

            pdf_path = self.generate_pdf(tn_no=self.tn_no, quantity=quantity)

            try:
                os.startfile(str(pdf_path), "print")
                messagebox.showinfo("Success", f"Transfer Note {self.tn_no} has been saved and sent to printer.")
            except OSError as e:
                if e.winerror == 1155:
                    messagebox.showwarning(
                        "Print Warning",
                        f"Automatic printing failed (Error: {e}).\nThe PDF has been saved at {pdf_path}.\nPlease open it manually and print using your PDF viewer."
                    )
                    webbrowser.open_new(str(pdf_path))
                else:
                    messagebox.showerror(
                        "Print Error",
                        f"An unexpected error occurred while printing: {e}\nThe PDF has been saved at {pdf_path}."
                    )
                    webbrowser.open_new(str(pdf_path))
        except mysql.connector.Error as db_err:
            messagebox.showerror("Database Error", f"Failed to save data: {db_err}")

class PartSelectionWindow:
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent.root)
        self.window.title("Select Part Number")
        self.window.geometry("1000x600")
        self.window.transient(parent.root)
        self.window.grab_set()

        # Search frame
        search_frame = tk.Frame(self.window)
        search_frame.pack(fill='x', padx=10, pady=5)
        tk.Label(search_frame, text="Search:", font=("Arial", 10)).pack(side='left')
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var, font=("Arial", 10))
        self.search_entry.pack(side='left', fill='x', expand=True, padx=(5, 0))
        self.search_entry.bind('<KeyRelease>', self.update_table)

        # Main container for treeview and scrollbars
        main_frame = tk.Frame(self.window)
        main_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))

        # Get column names from database
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SHOW COLUMNS FROM information")
        self.columns = [row[0] for row in cursor.fetchall()]
        conn.close()

        # Create treeview with proper scrollbar setup
        self.tree = ttk.Treeview(main_frame, columns=self.columns, show='headings', height=20)
        
        # Configure column headings and widths
        for col in self.columns:
            self.tree.heading(col, text=col, anchor='w')
            # Set fixed width for columns to enable horizontal scrolling
            col_width = max(120, len(col) * 12 + 60)
            self.tree.column(col, width=col_width, minwidth=80, anchor='w', stretch=False)

        # Create scrollbars
        v_scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(main_frame, orient="horizontal", command=self.tree.xview)
        
        # Configure treeview to use scrollbars
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Grid layout for proper scrollbar positioning
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        self.tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')

        # Bind double-click event
        self.tree.bind("<Double-1>", self.on_double_click)
        
        # Button frame
        button_frame = tk.Frame(self.window)
        button_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        select_btn = tk.Button(button_frame, text="Select", command=self.select_part, 
                              font=("Arial", 10), width=15)
        select_btn.pack(side='right', padx=(5, 0))
        
        cancel_btn = tk.Button(button_frame, text="Cancel", command=self.window.destroy, 
                              font=("Arial", 10), width=15)
        cancel_btn.pack(side='right')

        # Load initial data
        self.load_parts()

    def load_parts(self):
        """Load all parts from database"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        try:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM information ORDER BY Prdcode")
            rows = cursor.fetchall()
            conn.close()
            
            # Insert data into treeview
            for row in rows:
                # Convert None values to empty strings for display
                display_row = [str(item) if item is not None else "" for item in row]
                self.tree.insert("", "end", values=display_row)
                
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error loading parts: {err}")

    def update_table(self, event):
        """Filter table based on search term"""
        search_term = self.search_var.get().strip()
        
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if not search_term:
            # If search is empty, load all parts
            self.load_parts()
            return
            
        try:
            conn = connect_db()
            cursor = conn.cursor()

            # Create search conditions for all columns
            conditions = []
            params = []
            
            for col in self.columns:
                conditions.append(f"LOWER(CAST(`{col}` AS CHAR)) LIKE %s")
                params.append(f'%{search_term.lower()}%')
            
            query = f"SELECT * FROM information WHERE {' OR '.join(conditions)} ORDER BY Prdcode"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            
            # Insert filtered data
            for row in rows:
                display_row = [str(item) if item is not None else "" for item in row]
                self.tree.insert("", "end", values=display_row)
                
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error searching parts: {err}")

    def on_double_click(self, event):
        """Handle double-click on treeview item"""
        self.select_part()

    def select_part(self):
        """Select the highlighted part and close window"""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("No Selection", "Please select a part from the list.")
            return
            
        # Get the selected item
        item = selected_items[0]
        values = self.tree.item(item, "values")
        
        # Find the part number (Prdcode) from the values
        try:
            prdcode_index = self.columns.index('Prdcode')
            part_number = values[prdcode_index]
        except (ValueError, IndexError):
            # Fallback: use first column if Prdcode not found
            part_number = values[0] if values else ""
        
        if not part_number:
            messagebox.showerror("Error", "Selected part has no part number.")
            return
            
        # Set the part number in parent window and load data
        self.parent.part_dropdown.set(part_number)
        self.parent.load_part_data(None)
        self.window.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = LoginApp(root)
    root.mainloop()