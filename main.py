import sqlite3
import string
import random
import qrcode
from urllib.request import urlopen
from tkinter import *
import tkinter.messagebox
from tktimepicker import AnalogPicker, AnalogThemes, constants
from PIL import Image, ImageTk
import customtkinter as ctk
import csv

ctk.set_appearance_mode("dark")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("dark-blue")  # Themes: "blue" (standard), "green", "dark-blue"

def create_airport_table(conn, csv_file):
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS airports (
                    code TEXT PRIMARY KEY,
                    name TEXT,
                    city TEXT
                 )''')
    
    with open(csv_file, 'r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header row
        for row in reader:
            c.execute("INSERT OR REPLACE INTO airports VALUES (?, ?, ?)", row)

    conn.commit()

def generate_pnr():
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))

def generate_qrcode(text):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(text)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img.save("boarding_pass_qr.png")



def display_qrcode():

    qr_window = ctk.CTkToplevel(app)
    qr_window.iconphoto(False, PhotoImage(file='icon.png'))
    qr_window.title("QR Code")
    image_path = "boarding_pass_qr.png"
    image = image = Image.open(image_path)
    photo = ImageTk.PhotoImage(image)
    image_label = ctk.CTkLabel(app, image=photo)
    image_label.grid(row=0, column=0)



def connect_db():
    conn = sqlite3.connect('boarding_passes.db')
    return conn, conn.cursor()

def updateTime(time):
    time_lbl.configure(text="{}{}".format(*time)) # remove 3rd flower bracket in case of 24 hrs time
    
def get_time():

    top = ctk.CTkToplevel(app)
    top.iconphoto(False, PhotoImage(file='clock_icon.png'))
    top.title("Time Picker")

    time_picker = AnalogPicker(top, type=constants.HOURS24)
    time_picker.pack(expand=True, fill="both")

    theme = AnalogThemes(time_picker)
    theme.setDracula()
    ok_btn = ctk.CTkButton(top, text="Okay", command=lambda: updateTime(time_picker.time()))
    ok_btn.pack()

def check_in(conn, c, entries):
    name, phone_number, airline, flight_number, departure_airport, arrival_airport, departure_time = (e.get() for e in entries)

    pnr = generate_pnr()
    try:
        c.execute('''INSERT INTO boarding_passes (name, phone_number, airline, flight_number, departure_airport, arrival_airport, departure_time, pnr)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
              (name, phone_number, airline, flight_number, departure_airport, arrival_airport, departure_time, pnr))
        conn.commit()

        message = f"\nCheck-in successful! Your PNR is: {pnr}"
        tkinter.messagebox.showinfo("PNR generated successfuly", message)


    except sqlite3.IntegrityError:
        message = f"\nCheck-in failed! Phone number {phone_number} is already checked in."
        tkinter.messagebox.showerror("Check-in failed", message)
    
# Function to find airport details based on city
def find_airport(city, cursor):
    cursor.execute("SELECT code, name FROM airports WHERE city LIKE ?", ('%'+city+'%',))
    result = cursor.fetchone()
    return result if result else (None, None)  # Return None if city not found


def print_boarding_pass(conn, c, pnr_entry):
    pnr = pnr_entry.get()

    c.execute('''SELECT * FROM boarding_passes WHERE pnr = ?''', (pnr,))
    data = c.fetchone()

    if not data:
        print("Invalid PNR. Please try again.")
        return
    
    departure_city = data[4]  # Departure city
    arrival_city = data[5]  # Arrival city
    departure_iata, departure_name = find_airport(departure_city, c)
    arrival_iata, arrival_name = find_airport(arrival_city, c)

    if departure_iata and arrival_iata:
        # Add departure and arrival airport details to the boarding_passes table
        c.execute('''UPDATE boarding_passes SET departure_airport_name = ?, departure_airport_code = ?, arrival_airport_name = ?, arrival_airport_code = ? WHERE pnr = ?''',
                  (departure_name, departure_iata, arrival_name, arrival_iata, pnr))
        conn.commit()
        
    else:
        print("Could not find airport information for provided cities.")
    
    openNewWindow(data)


def openNewWindow(data: tuple):

    # Toplevel object which will 
    # be treated as a new window
    newWindow = ctk.CTkToplevel(app)
   
    # sets the title of the
    # Toplevel widget
    newWindow.title("Pass")
 
    # sets the geometry of toplevel
    newWindow.geometry("294x290")
    
    # A ctk.CTkLabel widget to show in toplevel
    ctk.CTkLabel(newWindow, text="Name: ").grid(row=0, column=0)
    ctk.CTkLabel(newWindow, text="PNR: ").grid(row=1, column=0)
    ctk.CTkLabel(newWindow, text="Airline: ").grid(row=2, column=0)
    ctk.CTkLabel(newWindow, text="Flight number: ").grid(row=3, column=0)
    ctk.CTkLabel(newWindow, text="").grid(row=4, column=0)
    ctk.CTkLabel(newWindow, text="Boarding Time: ").grid(row=5, column=0)
    ctk.CTkLabel(newWindow, text="Departure Airport: ").grid(row=6, column=0)
    ctk.CTkLabel(newWindow, text="Arrival Airport: ").grid(row=7, column=0)
    ctk.CTkLabel(newWindow, text="").grid(row=8, column=0)

    # Construct boarding pass information string including airport details
    text = f'''Passenger Mr./Ms. {data[0]} with PNR number {data[7]} travelling via {data[2]} flight number {data[3]} departing from {data[8]} to {data[10]} at {data[6]} hrs.
    \nPlease note that boarding begins at {data[6]-100} hrs and closes 20 minutes before departure.\nHave a safe journey!'''

    ctk.CTkButton(newWindow, text="Generate QR", command=lambda: generate_qrcode(text)).grid(row=9, column=0, padx=5)
    ctk.CTkButton(newWindow, text="  Show QR  ", command=lambda: Image.open('boarding_pass_qr.png').show()).grid(row=9, column=1)
 



    '''
    #Creating gap
    ctk.CTkLabel(newWindow, text="\t").grid(row=0, column=1)
    ctk.CTkLabel(newWindow, text="\t").grid(row=1, column=1)
    ctk.CTkLabel(newWindow, text="\t").grid(row=2, column=1)
    ctk.CTkLabel(newWindow, text="\t").grid(row=3, column=1)
    ctk.CTkLabel(newWindow, text="\t").grid(row=4, column=1)
    ctk.CTkLabel(newWindow, text="\t").grid(row=5, column=1)
    ctk.CTkLabel(newWindow, text="\t").grid(row=6, column=1)
    ctk.CTkLabel(newWindow, text="\t").grid(row=7, column=1)
    '''
     # A ctk.CTkLabel widget to show in toplevel
    ctk.CTkLabel(newWindow, text=f"{data[0]}").grid(row=0, column=1)
    ctk.CTkLabel(newWindow, text=f"{data[7]}").grid(row=1, column=1)
    ctk.CTkLabel(newWindow, text=f"{data[2]}").grid(row=2, column=1)
    ctk.CTkLabel(newWindow, text=f"{data[3]}").grid(row=3, column=1)
    ctk.CTkLabel(newWindow, text="").grid(row=4, column=1)
    ctk.CTkLabel(newWindow, text=f"{data[6]-100} hrs").grid(row=5, column=1)
    ctk.CTkLabel(newWindow, text=f"{data[9]}").grid(row=6, column=1)
    ctk.CTkLabel(newWindow, text=f"{data[11]}").grid(row=7, column=1)



def create_table(conn, c):
    # Define table schema with data types
    c.execute('''CREATE TABLE IF NOT EXISTS boarding_passes (
              name TEXT,
              phone_number TEXT PRIMARY KEY,
              airline TEXT,
              flight_number TEXT,
              departure_airport TEXT,
              arrival_airport TEXT,
              departure_time NUMBER,
              pnr TEXT,
              departure_airport_name TEXT,
              departure_airport_code TEXT,
              arrival_airport_name TEXT,
              arrival_airport_code TEXT
)''')

    conn.commit()

if __name__ == "__main__":
    conn, c = connect_db()
    create_table(conn, c)  # Create table if it doesn't exist
    create_airport_table(conn, 'airport_codes.csv')
    app = ctk.CTk()
    app.title("Boarding Pass Generator")
    app.geometry("290x345")

    ctk.CTkLabel(app, text="Enter your name: ").grid(row=0)
    ctk.CTkLabel(app, text="Enter phone number: ").grid(row=1)
    ctk.CTkLabel(app, text="Enter airline: ").grid(row=2)
    ctk.CTkLabel(app, text="Enter flight number: ").grid(row=3)
    ctk.CTkLabel(app, text="Enter departure city:   ").grid(row=4)
    ctk.CTkLabel(app, text="Enter arrival city: ").grid(row=5)
    ctk.CTkLabel(app, text="  Choose departure time:  ").grid(row=6)
   

    entries = [ctk.CTkEntry(app) for _ in range(7)]
    for i, entry in enumerate(entries):
        entry.grid(row=i, column=1, pady=1, padx=2)
    
    
    time = ()
    time_lbl = ctk.CTkLabel(app, text="")
    time_btn = ctk.CTkButton(app, text=" Get Time ", command=get_time)
    time_lbl.grid(row=7, column=1)
    time_btn.grid(row=7, column=0)
    

    ctk.CTkButton(app, text='  Click to Check In  ', command=lambda: check_in(conn, c, entries)).grid(row=8, column=1, sticky=W, pady=4, padx=2)

    ctk.CTkLabel(app, text="Enter your PNR: ").grid(row=9)
    pnr_entry = ctk.CTkEntry(app)
    pnr_entry.grid(row=9, column=1)
    ctk.CTkButton(app, text='Print Boarding Pass', command=lambda: print_boarding_pass(conn, c, pnr_entry)).grid(row=10, column=1, sticky=W, pady=12, padx=2)


    app.mainloop()
