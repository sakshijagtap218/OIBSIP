import tkinter as tk
from tkinter import messagebox, filedialog
import sqlite3
from datetime import datetime
import matplotlib.pyplot as plt
import csv


# ============================================================
# GLOBAL VARIABLES
# ============================================================

current_bmi = None
current_category = None


# ============================================================
# COLORS
# ============================================================

BG_COLOR = "#F4F7FB"
CARD_COLOR = "#FFFFFF"
TITLE_COLOR = "#1F2937"
TEXT_COLOR = "#374151"
PRIMARY_COLOR = "#2563EB"
SECONDARY_COLOR = "#64748B"
SUCCESS_COLOR = "#16A34A"
WARNING_COLOR = "#F59E0B"
DANGER_COLOR = "#DC2626"
EXPORT_COLOR = "#0D9488"


# ============================================================
# LIVE DATE & TIME
# ============================================================

def update_live_time():
    now = datetime.now().strftime("%d-%b-%Y  |  %H:%M:%S")
    clock_label.config(text=f"🕒  {now}")
    root.after(1000, update_live_time)


# ============================================================
# DATABASE SETUP
# ============================================================

def create_database():
    try:
        connection = sqlite3.connect("bmi_database.db")
        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bmi_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                weight REAL NOT NULL,
                height REAL NOT NULL,
                bmi REAL NOT NULL,
                category TEXT NOT NULL,
                date_time TEXT NOT NULL
            )
        """)

        connection.commit()
        connection.close()

    except sqlite3.Error as error:
        messagebox.showerror(
            "Database Error",
            f"Could not create database.\n{error}"
        )


# ============================================================
# CALCULATE BMI
# ============================================================

def calculate_bmi():
    global current_bmi, current_category

    try:
        name = name_entry.get().strip()
        weight_text = weight_entry.get().strip()
        height_text = height_entry.get().strip()

        if name == "":
            messagebox.showerror(
                "Invalid Input",
                "Please enter your name."
            )
            return

        if weight_text == "":
            messagebox.showerror(
                "Invalid Input",
                "Please enter your weight."
            )
            return

        if height_text == "":
            messagebox.showerror(
                "Invalid Input",
                "Please enter your height."
            )
            return

        weight = float(weight_text)
        height = float(height_text)

        if weight <= 0:
            messagebox.showerror(
                "Invalid Input",
                "Weight must be greater than 0."
            )
            return

        if height <= 0:
            messagebox.showerror(
                "Invalid Input",
                "Height must be greater than 0."
            )
            return

        # BMI Formula
        bmi = weight / (height ** 2)

        # BMI Category
        if bmi < 18.5:
            category = "Underweight"
            color = WARNING_COLOR

        elif bmi < 25:
            category = "Normal"
            color = SUCCESS_COLOR

        elif bmi < 30:
            category = "Overweight"
            color = WARNING_COLOR

        else:
            category = "Obese"
            color = DANGER_COLOR

        current_bmi = bmi
        current_category = category

        # Normal weight range
        minimum_normal_weight = 18.5 * (height ** 2)
        maximum_normal_weight = 24.9 * (height ** 2)

        # Display BMI
        result_label.config(
            text=f"{bmi:.2f}",
            fg=color
        )

        # Display Category
        category_label.config(
            text=category,
            fg=color
        )

        # Recommendation
        if category == "Normal":
            recommendation_text = (
                f"Great! Your BMI is in the normal range.\n\n"
                f"Your height: {height:.2f} m\n"
                f"Your weight: {weight:.1f} kg\n\n"
                f"Normal weight range for your height:\n"
                f"{minimum_normal_weight:.1f} kg - "
                f"{maximum_normal_weight:.1f} kg"
            )

        elif category == "Underweight":
            weight_needed = minimum_normal_weight - weight
            recommendation_text = (
                f"Your BMI is below the normal range.\n\n"
                f"Your height: {height:.2f} m\n"
                f"Your current weight: {weight:.1f} kg\n\n"
                f"Normal weight range for your height:\n"
                f"{minimum_normal_weight:.1f} kg - "
                f"{maximum_normal_weight:.1f} kg\n\n"
                f"You need approximately "
                f"{weight_needed:.1f} kg more "
                f"to reach the lower end of the normal range."
            )

        elif category == "Overweight":
            weight_to_lose = weight - maximum_normal_weight
            recommendation_text = (
                f"Your BMI is above the normal range.\n\n"
                f"Your height: {height:.2f} m\n"
                f"Your current weight: {weight:.1f} kg\n\n"
                f"Normal weight range for your height:\n"
                f"{minimum_normal_weight:.1f} kg - "
                f"{maximum_normal_weight:.1f} kg\n\n"
                f"The upper end of the normal range is "
                f"about {weight_to_lose:.1f} kg below your current weight."
            )

        else:
            weight_to_lose = weight - maximum_normal_weight
            recommendation_text = (
                f"Your BMI is in the obese range.\n\n"
                f"Your height: {height:.2f} m\n"
                f"Your current weight: {weight:.1f} kg\n\n"
                f"Normal weight range for your height:\n"
                f"{minimum_normal_weight:.1f} kg - "
                f"{maximum_normal_weight:.1f} kg\n\n"
                f"The upper end of the normal range is "
                f"about {weight_to_lose:.1f} kg below your current weight."
            )

        recommendation_label.config(
            text=recommendation_text,
            fg=TEXT_COLOR
        )

    except ValueError:
        messagebox.showerror(
            "Invalid Input",
            "Please enter valid numbers for weight and height."
        )


# ============================================================
# SAVE RECORD
# ============================================================

def save_record():
    global current_bmi, current_category

    try:
        if current_bmi is None:
            messagebox.showwarning(
                "Warning",
                "Please calculate your BMI first."
            )
            return

        name = name_entry.get().strip()
        weight = float(weight_entry.get())
        height = float(height_entry.get())

        if name == "":
            messagebox.showerror(
                "Invalid Input",
                "Please enter your name."
            )
            return

        date_time = datetime.now().strftime(
            "%d-%b-%Y %H:%M:%S"
        )

        connection = sqlite3.connect(
            "bmi_database.db"
        )

        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO bmi_records
            (name, weight, height, bmi, category, date_time)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            name,
            weight,
            height,
            current_bmi,
            current_category,
            date_time
        ))

        connection.commit()
        connection.close()

        messagebox.showinfo(
            "Success",
            "BMI record saved successfully!"
        )

    except sqlite3.Error as error:
        messagebox.showerror(
            "Database Error",
            f"Could not save record.\n{error}"
        )

    except ValueError:
        messagebox.showerror(
            "Invalid Input",
            "Please enter valid values."
        )


# ============================================================
# EXPORT ALL DATA TO CSV (UPDATED FIX)
# ============================================================

def export_to_csv():
    try:
        connection = sqlite3.connect("bmi_database.db")
        cursor = connection.cursor()

        cursor.execute("""
            SELECT id, name, weight, height,
                   bmi, category, date_time
            FROM bmi_records
            ORDER BY id DESC
        """)

        records = cursor.fetchall()
        connection.close()

        if not records:
            messagebox.showinfo(
                "No Data",
                "No BMI records found to export."
            )
            return

        file_path = filedialog.asksaveasfilename(
            title="Save BMI Records",
            defaultextension=".csv",
            initialfile="BMI_Records.csv",
            filetypes=[
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ]
        )

        if not file_path:
            return

        with open(
            file_path,
            mode="w",
            newline="",
            encoding="utf-8-sig"
        ) as file:

            writer = csv.writer(file)

            # Header
            writer.writerow([
                "ID",
                "Name",
                "Weight (kg)",
                "Height (m)",
                "BMI",
                "Category",
                "Date & Time"
            ])

            for record in records:
                rec_id = record[0]
                name = record[1]
                weight = record[2]
                height = record[3]
                bmi = record[4]
                category = record[5]
                date_time = record[6]

                # Single quote added to force Excel to render text and avoid ########
                date_time_text = f"'{date_time}"

                writer.writerow([
                    rec_id,
                    name,
                    weight,
                    height,
                    f"{bmi:.2f}",
                    category,
                    date_time_text
                ])

        messagebox.showinfo(
            "Export Successful",
            "All BMI records exported successfully!\n\n"
            "Date & Time is saved in readable text format."
        )

    except Exception as error:
        messagebox.showerror(
            "Export Error",
            f"Could not export data.\n{error}"
        )


# ============================================================
# DELETE SINGLE RECORD
# ============================================================

def delete_single_record(record_id, history_window, user_name):
    confirm = messagebox.askyesno(
        "Confirm Delete",
        "Are you sure you want to delete this record?"
    )

    if not confirm:
        return

    try:
        connection = sqlite3.connect("bmi_database.db")
        cursor = connection.cursor()

        cursor.execute(
            "DELETE FROM bmi_records WHERE id = ?",
            (record_id,)
        )

        connection.commit()
        connection.close()

        history_window.destroy()
        view_history()

    except sqlite3.Error as error:
        messagebox.showerror(
            "Database Error",
            f"Could not delete record.\n{error}"
        )


# ============================================================
# DELETE ALL RECORDS
# ============================================================

def delete_all_records(history_window):
    confirm = messagebox.askyesno(
        "Confirm Clear All",
        "Are you sure you want to delete ALL BMI history?"
    )

    if not confirm:
        return

    try:
        connection = sqlite3.connect("bmi_database.db")
        cursor = connection.cursor()

        cursor.execute("DELETE FROM bmi_records")

        connection.commit()
        connection.close()

        history_window.destroy()

        messagebox.showinfo(
            "History Cleared",
            "All BMI history has been deleted."
        )

        view_history()

    except sqlite3.Error as error:
        messagebox.showerror(
            "Database Error",
            f"Could not clear history.\n{error}"
        )


# ============================================================
# DELETE USER RECORDS
# ============================================================

def delete_user_records(user_name, history_window):
    confirm = messagebox.askyesno(
        "Confirm Clear",
        f"Delete ALL records for {user_name}?"
    )

    if not confirm:
        return

    try:
        connection = sqlite3.connect("bmi_database.db")
        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM bmi_records
            WHERE LOWER(name) = LOWER(?)
            """,
            (user_name,)
        )

        connection.commit()
        connection.close()

        history_window.destroy()

        messagebox.showinfo(
            "History Cleared",
            f"All records for {user_name} have been deleted."
        )

        view_history()

    except sqlite3.Error as error:
        messagebox.showerror(
            "Database Error",
            f"Could not clear user history.\n{error}"
        )


# ============================================================
# VIEW HISTORY
# ============================================================

def view_history():
    user_name = name_entry.get().strip()

    try:
        connection = sqlite3.connect("bmi_database.db")
        cursor = connection.cursor()

        if user_name == "":
            cursor.execute("""
                SELECT id, name, weight, height,
                       bmi, category, date_time
                FROM bmi_records
                ORDER BY id DESC
            """)
            window_title = "BMI History - All Users"
        else:
            cursor.execute("""
                SELECT id, name, weight, height,
                       bmi, category, date_time
                FROM bmi_records
                WHERE LOWER(name) = LOWER(?)
                ORDER BY id DESC
            """, (user_name,))
            window_title = f"BMI History - {user_name}"

        records = cursor.fetchall()
        connection.close()

        history_window = tk.Toplevel(root)
        history_window.title(window_title)
        history_window.geometry("850x650")
        history_window.configure(bg=BG_COLOR)

        title_text = (
            "All Users History"
            if user_name == ""
            else f"BMI History for '{user_name}'"
        )

        title = tk.Label(
            history_window,
            text=title_text,
            font=("Arial", 20, "bold"),
            bg=BG_COLOR,
            fg=TITLE_COLOR
        )

        title.pack(pady=(15, 8))

        if user_name == "":
            clear_all_btn = tk.Button(
                history_window,
                text="Clear ALL History",
                font=("Arial", 10, "bold"),
                bg=DANGER_COLOR,
                fg="white",
                relief="flat",
                cursor="hand2",
                command=lambda: delete_all_records(history_window)
            )
            clear_all_btn.pack(pady=(0, 15), ipadx=10, ipady=4)
        else:
            clear_user_btn = tk.Button(
                history_window,
                text=f"Clear History for {user_name}",
                font=("Arial", 10, "bold"),
                bg=DANGER_COLOR,
                fg="white",
                relief="flat",
                cursor="hand2",
                command=lambda: delete_user_records(user_name, history_window)
            )
            clear_user_btn.pack(pady=(0, 15), ipadx=10, ipady=4)

        if not records:
            label = tk.Label(
                history_window,
                text="No BMI records found.",
                font=("Arial", 14),
                bg=BG_COLOR,
                fg=TEXT_COLOR
            )
            label.pack(pady=30)
            return

        hist_canvas = tk.Canvas(
            history_window,
            bg=BG_COLOR,
            highlightthickness=0
        )

        hist_scrollbar = tk.Scrollbar(
            history_window,
            orient="vertical",
            command=hist_canvas.yview
        )

        hist_frame = tk.Frame(
            hist_canvas,
            bg=BG_COLOR
        )

        hist_frame.bind(
            "<Configure>",
            lambda event: hist_canvas.configure(
                scrollregion=hist_canvas.bbox("all")
            )
        )

        hist_canvas_window = hist_canvas.create_window(
            (0, 0),
            window=hist_frame,
            anchor="nw"
        )

        def on_hist_configure(event):
            hist_canvas.itemconfig(
                hist_canvas_window,
                width=event.width
            )

        hist_canvas.bind("<Configure>", on_hist_configure)

        hist_canvas.configure(
            yscrollcommand=hist_scrollbar.set
        )

        hist_canvas.pack(
            side="left",
            fill="both",
            expand=True
        )

        hist_scrollbar.pack(
            side="right",
            fill="y"
        )

        for record in records:
            rec_id = record[0]
            name = record[1]
            weight = record[2]
            height = record[3]
            bmi = record[4]
            category = record[5]
            date_time = record[6]

            text = (
                f"Name: {name}\n"
                f"Weight: {weight} kg    "
                f"Height: {height} m\n"
                f"BMI: {bmi:.2f}\n"
                f"Category: {category}\n"
                f"Date & Time: {date_time}"
            )

            if category == "Normal":
                color = SUCCESS_COLOR
            elif category == "Obese":
                color = DANGER_COLOR
            else:
                color = WARNING_COLOR

            card = tk.Frame(
                hist_frame,
                bg=CARD_COLOR,
                relief="solid",
                borderwidth=1,
                padx=15,
                pady=10
            )

            card.pack(
                fill="x",
                padx=25,
                pady=6
            )

            record_label = tk.Label(
                card,
                text=text,
                font=("Arial", 11),
                fg=color,
                bg=CARD_COLOR,
                justify="left",
                anchor="w"
            )

            record_label.pack(
                side="left",
                fill="both",
                expand=True
            )

            delete_button = tk.Button(
                card,
                text="Delete",
                font=("Arial", 9, "bold"),
                bg=DANGER_COLOR,
                fg="white",
                relief="flat",
                cursor="hand2",
                command=lambda r_id=rec_id: delete_single_record(
                    r_id,
                    history_window,
                    user_name
                )
            )

            delete_button.pack(
                side="right",
                padx=(10, 0),
                ipadx=8,
                ipady=3
            )

    except sqlite3.Error as error:
        messagebox.showerror(
            "Database Error",
            f"Could not read history.\n{error}"
        )


# ============================================================
# SHOW BMI GRAPH
# ============================================================

def show_graph():
    try:
        name = name_entry.get().strip()

        if name == "":
            messagebox.showerror(
                "Error",
                "Please enter a name to view the graph."
            )
            return

        connection = sqlite3.connect("bmi_database.db")
        cursor = connection.cursor()

        cursor.execute("""
            SELECT bmi, date_time
            FROM bmi_records
            WHERE LOWER(name) = LOWER(?)
            ORDER BY id ASC
        """, (name,))

        records = cursor.fetchall()
        connection.close()

        if not records:
            messagebox.showinfo(
                "No Data",
                f"No BMI records found for {name}."
            )
            return

        bmi_values = [record[0] for record in records]
        dates = [record[1] for record in records]

        plt.figure(figsize=(10, 5))

        plt.plot(
            dates,
            bmi_values,
            marker="o",
            linewidth=2
        )

        plt.title(
            f"BMI Trend for {name}",
            fontsize=16
        )

        plt.xlabel("Date & Time")
        plt.ylabel("BMI")

        plt.xticks(
            rotation=45,
            ha="right"
        )

        plt.axhline(
            y=18.5,
            linestyle="--",
            label="Underweight Limit"
        )

        plt.axhline(
            y=25,
            linestyle="--",
            label="Overweight Limit"
        )

        plt.axhline(
            y=30,
            linestyle="--",
            label="Obese Limit"
        )

        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.show()

    except Exception as error:
        messagebox.showerror(
            "Graph Error",
            f"Could not display graph.\n{error}"
        )


# ============================================================
# CLEAR / RESET
# ============================================================

def clear_fields():
    global current_bmi, current_category

    name_entry.delete(0, tk.END)
    weight_entry.delete(0, tk.END)
    height_entry.delete(0, tk.END)

    result_label.config(
        text="--",
        fg=TITLE_COLOR
    )

    category_label.config(
        text="Enter your details",
        fg=SECONDARY_COLOR
    )

    recommendation_label.config(
        text="Your BMI recommendation will appear here.",
        fg=SECONDARY_COLOR
    )

    current_bmi = None
    current_category = None


# ============================================================
# MAIN WINDOW
# ============================================================

root = tk.Tk()
root.title("BMI Calculator")
root.geometry("600x800")
root.configure(bg=BG_COLOR)
root.resizable(True, True)


# ============================================================
# SCROLLABLE MAIN WINDOW
# ============================================================

canvas = tk.Canvas(
    root,
    bg=BG_COLOR,
    highlightthickness=0
)

scrollbar = tk.Scrollbar(
    root,
    orient="vertical",
    command=canvas.yview
)

scrollable_frame = tk.Frame(
    canvas,
    bg=BG_COLOR
)


def on_mousewheel(event):
    canvas.yview_scroll(
        int(-1 * (event.delta / 120)),
        "units"
    )


canvas.bind_all("<MouseWheel>", on_mousewheel)

scrollable_frame.bind(
    "<Configure>",
    lambda event: canvas.configure(
        scrollregion=canvas.bbox("all")
    )
)

canvas_window = canvas.create_window(
    0,
    0,
    window=scrollable_frame,
    anchor="n"
)


def on_canvas_configure(event):
    canvas.coords(
        canvas_window,
        event.width / 2,
        0
    )


canvas.bind("<Configure>", on_canvas_configure)

canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(
    side="left",
    fill="both",
    expand=True
)

scrollbar.pack(
    side="right",
    fill="y"
)


# ============================================================
# TITLE & CLOCK
# ============================================================

title_label = tk.Label(
    scrollable_frame,
    text="BMI Calculator",
    font=("Arial", 26, "bold"),
    bg=BG_COLOR,
    fg=TITLE_COLOR
)
title_label.pack(pady=(25, 5))

subtitle_label = tk.Label(
    scrollable_frame,
    text="Calculate and track your Body Mass Index",
    font=("Arial", 11),
    bg=BG_COLOR,
    fg=SECONDARY_COLOR
)
subtitle_label.pack(pady=(0, 5))

clock_label = tk.Label(
    scrollable_frame,
    text="🕒 --",
    font=("Arial", 10, "bold"),
    bg=BG_COLOR,
    fg=PRIMARY_COLOR
)
clock_label.pack(pady=(0, 15))


# ============================================================
# INPUT CARD
# ============================================================

input_frame = tk.Frame(
    scrollable_frame,
    bg=CARD_COLOR,
    padx=25,
    pady=20
)
input_frame.pack(pady=10)

name_label = tk.Label(
    input_frame, text="Name", font=("Arial", 11, "bold"), bg=CARD_COLOR, fg=TEXT_COLOR
)
name_label.pack(anchor="w")

name_entry = tk.Entry(
    input_frame, font=("Arial", 12), width=35, relief="solid", borderwidth=1
)
name_entry.pack(pady=(5, 15), ipady=5)

weight_label = tk.Label(
    input_frame, text="Weight (kg)", font=("Arial", 11, "bold"), bg=CARD_COLOR, fg=TEXT_COLOR
)
weight_label.pack(anchor="w")

weight_entry = tk.Entry(
    input_frame, font=("Arial", 12), width=35, relief="solid", borderwidth=1
)
weight_entry.pack(pady=(5, 15), ipady=5)

height_label = tk.Label(
    input_frame, text="Height (m)", font=("Arial", 11, "bold"), bg=CARD_COLOR, fg=TEXT_COLOR
)
height_label.pack(anchor="w")

height_entry = tk.Entry(
    input_frame, font=("Arial", 12), width=35, relief="solid", borderwidth=1
)
height_entry.pack(pady=(5, 10), ipady=5)


# ============================================================
# CALCULATE BUTTON
# ============================================================

calculate_button = tk.Button(
    scrollable_frame,
    text="Calculate BMI",
    font=("Arial", 12, "bold"),
    bg=PRIMARY_COLOR,
    fg="white",
    activebackground=PRIMARY_COLOR,
    activeforeground="white",
    relief="flat",
    cursor="hand2",
    command=calculate_bmi
)
calculate_button.pack(pady=15, ipadx=30, ipady=8)


# ============================================================
# RESULT CARD
# ============================================================

result_frame = tk.Frame(
    scrollable_frame,
    bg=CARD_COLOR,
    padx=60,
    pady=15
)
result_frame.pack(pady=10)

result_title = tk.Label(
    result_frame, text="Your BMI", font=("Arial", 11), bg=CARD_COLOR, fg=SECONDARY_COLOR
)
result_title.pack()

result_label = tk.Label(
    result_frame, text="--", font=("Arial", 28, "bold"), bg=CARD_COLOR, fg=TITLE_COLOR
)
result_label.pack(pady=5)

category_label = tk.Label(
    result_frame, text="Enter your details", font=("Arial", 13, "bold"), bg=CARD_COLOR, fg=SECONDARY_COLOR
)
category_label.pack()


# ============================================================
# RECOMMENDATION CARD
# ============================================================

recommendation_frame = tk.Frame(
    scrollable_frame,
    bg=CARD_COLOR,
    padx=20,
    pady=15
)
recommendation_frame.pack(pady=10)

recommendation_title = tk.Label(
    recommendation_frame, text="Weight Recommendation", font=("Arial", 13, "bold"), bg=CARD_COLOR, fg=TITLE_COLOR
)
recommendation_title.pack(pady=(0, 8))

recommendation_label = tk.Label(
    recommendation_frame,
    text="Your BMI recommendation will appear here.",
    font=("Arial", 10),
    bg=CARD_COLOR,
    fg=SECONDARY_COLOR,
    justify="center",
    wraplength=400
)
recommendation_label.pack()


# ============================================================
# BUTTON FRAME
# ============================================================

button_frame = tk.Frame(scrollable_frame, bg=BG_COLOR)
button_frame.pack(pady=10)

save_button = tk.Button(
    button_frame, text="Save Record", font=("Arial", 10, "bold"), bg=SUCCESS_COLOR, fg="white", relief="flat", cursor="hand2", command=save_record
)
save_button.grid(row=0, column=0, padx=4, ipadx=8, ipady=6)

history_button = tk.Button(
    button_frame, text="View History", font=("Arial", 10, "bold"), bg=SECONDARY_COLOR, fg="white", relief="flat", cursor="hand2", command=view_history
)
history_button.grid(row=0, column=1, padx=4, ipadx=8, ipady=6)

graph_button = tk.Button(
    button_frame, text="Show Graph", font=("Arial", 10, "bold"), bg=PRIMARY_COLOR, fg="white", relief="flat", cursor="hand2", command=show_graph
)
graph_button.grid(row=0, column=2, padx=4, ipadx=8, ipady=6)

export_button = tk.Button(
    button_frame, text="Export CSV", font=("Arial", 10, "bold"), bg=EXPORT_COLOR, fg="white", relief="flat", cursor="hand2", command=export_to_csv
)
export_button.grid(row=0, column=3, padx=4, ipadx=8, ipady=6)


# ============================================================
# CLEAR / RESET BUTTON & GUIDE
# ============================================================

clear_button = tk.Button(
    scrollable_frame, text="Clear / Reset", font=("Arial", 10, "bold"), bg=DANGER_COLOR, fg="white", relief="flat", cursor="hand2", command=clear_fields
)
clear_button.pack(pady=5, ipadx=25, ipady=5)

guide_label = tk.Label(
    scrollable_frame,
    text="BMI Guide: Underweight < 18.5 | Normal 18.5–24.9 | Overweight 25–29.9 | Obese ≥ 30",
    font=("Arial", 8),
    bg=BG_COLOR,
    fg=SECONDARY_COLOR,
    wraplength=450
)
guide_label.pack(pady=(10, 25))


# ============================================================
# INITIALIZE APPLICATION
# ============================================================

create_database()
update_live_time()

root.mainloop()