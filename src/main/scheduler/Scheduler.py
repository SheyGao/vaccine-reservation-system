from model.Vaccine import Vaccine  
from model.Caregiver import Caregiver
from model.Patient import Patient
from util.Util import Util
from db.ConnectionManager import ConnectionManager
import pymssql
import datetime
import re 


'''
objects to keep track of the currently logged-in user
Note: it is always true that at most one of currentCaregiver and currentPatient is not null
        since only one user can be logged-in at a time
'''
current_patient = None

current_caregiver = None


def create_patient(tokens):
    # create_patient <username> <password>
    # check 1: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Failed to create user.")
        return

    username = tokens[1]
    password = tokens[2]
    # check 2: check if the username has been taken already
    if username_exists_patient(username):
        print("Username taken, try again!")
        return

    if not check_password(password):
        return

    salt = Util.generate_salt()
    hash = Util.generate_hash(password, salt)

    # create the patient
    patient = Patient(username, salt=salt, hash=hash)

    # save to patient information to our database
    try:
        patient.save_to_db()
    except pymssql.Error as e:
        print("Failed to create user.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Failed to create user.")
        print(e)
        return
    print("Created user ", username)


def username_exists_patient(username):
    cm = ConnectionManager()
    conn = cm.create_connection()

    select_username = "SELECT * FROM Patients WHERE Username = %s"
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute(select_username, username)
        #  returns false if the cursor is not before the first record or if there are no rows in the ResultSet.
        for row in cursor:
            return row['Username'] is not None
    except pymssql.Error as e:
        print("Error occurred when checking username")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error occurred when checking username")
        print("Error:", e)
    finally:
        cm.close_connection()
    return False


def create_caregiver(tokens):
    # create_caregiver <username> <password>
    # check 1: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Failed to create user.")
        return

    username = tokens[1]
    password = tokens[2]
    # check 2: check if the username has been taken already
    if username_exists_caregiver(username):
        print("Username taken, try again!")
        return

    if not check_password(password): 
        return 

    salt = Util.generate_salt()
    hash = Util.generate_hash(password, salt)

    # create the caregiver
    caregiver = Caregiver(username, salt=salt, hash=hash)

    # save to caregiver information to our database
    try:
        caregiver.save_to_db()
    except pymssql.Error as e:
        print("Failed to create user.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Failed to create user.")
        print(e)
        return
    print("Created user ", username)


def username_exists_caregiver(username):
    cm = ConnectionManager()
    conn = cm.create_connection()

    select_username = "SELECT * FROM Caregivers WHERE Username = %s"
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute(select_username, username)
        #  returns false if the cursor is not before the first record or if there are no rows in the ResultSet.
        for row in cursor:
            return row['Username'] is not None
    except pymssql.Error as e:
        print("Error occurred when checking username")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error occurred when checking username")
        print("Error:", e)
    finally:
        cm.close_connection()
    return False


def check_password(password):
    strong_password = True 
    
    if len(password) < 8:
        print("At least 8 characters for a strong password.")
        strong_password = False
    if (any(char.isalpha() for char in password) == False):
        print("At least 1 letter for a strong password.")
        strong_password = False
    if (any([char.isupper() for char in password]) == False):
        print("At least 1 uppercase letter for a strong password.")
        strong_password = False
    if re.search("[a-z]+", password) is None:
        print("At least 1 lowercase letter for a strong password.")
        strong_password = False
    if (any(char.isdigit() for char in password) == False):
        print("At least 1 number for a strong password.")
        strong_password = False
    if re.search(r"[!@#?]+", password) is None:
        print("Password must have at least 1 special character from (!, @, #, ?)")
        strong_password = False

    return strong_password 


def login_patient(tokens):
    # login_patient <username> <password>
    # check 1: if someone's already logged-in, they need to log out first
    global current_patient
    if current_patient is not None or current_caregiver is not None:
        print("User already logged in.")
        return 

    # check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Login failed.")
        return

    username = tokens[1]
    password = tokens[2]

    patient = None
    try:
        patient = Patient(username, password=password).get()
    except pymssql.Error as e:
        print("Login failed.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Login failed.")
        print("Error:", e)
        return

    # check if the login was successful
    if patient is None:
        print("Login failed.")
    else:
        print("Logged in as: " + username)
        current_patient = patient 

def login_caregiver(tokens):
    # login_caregiver <username> <password>
    # check 1: if someone's already logged-in, they need to log out first
    global current_caregiver
    if current_caregiver is not None or current_patient is not None:
        print("User already logged in.")
        return

    # check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Login failed.")
        return

    username = tokens[1]
    password = tokens[2]

    caregiver = None
    try:
        caregiver = Caregiver(username, password=password).get()
    except pymssql.Error as e:
        print("Login failed.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Login failed.")
        print("Error:", e)
        return

    # check if the login was successful
    if caregiver is None:
        print("Login failed.")
    else:
        print("Logged in as: " + username)
        current_caregiver = caregiver


def search_caregiver_schedule(tokens):  
    # search_caregiver_schedule <date>
    # check 1: Check if there's any user logged in
    global current_caregiver
    global current_patient
    
    if current_caregiver is None and current_patient is None: 
        print("Please login first!")
        return
    
    # check 2: the length for tokens need to be exactly 2 to include all information (with the operation name)
    if len(tokens) != 2:
        print("Please try again!") 
        return

    cm = ConnectionManager() 
    conn = cm.create_connection()
    cursor = conn.cursor(as_dict=True)

    date = tokens[1]  

    search_vaccine = "SELECT Name, Doses FROM Vaccines"
    search_caregiver = "SELECT Username FROM Availabilities WHERE Time = %s ORDER BY Username" 
 
    try:
        cursor.execute(search_vaccine)
        vaccine = cursor.fetchall()
        cursor.execute(search_caregiver, date)
        caregiver = cursor.fetchall()

        print("{:<12}".format("Caregiver"), end="")
        for i in range(0, len(vaccine)):
            print("{:<12}".format(vaccine[i]["Name"]), end="") 
        print("\n", end="") 

        for row in caregiver:
            print("{:<12}".format(row['Username']), end="") 
            for i in range(0, len(vaccine)):
                print("{:<12}".format(vaccine[i]["Doses"]), end="")
            print("")
            
    except pymssql.Error as e:
        print("Error occurred when getting details from Caregivers or Vaccines") 
        print("Db-Error:", e)
        quit()
    except ValueError as e:
        print("Invalid statement; try again")
        print("Error:", e)
        return
    except Exception as e:
        print("Error occurred when getting details from Caregivers or Vaccines")  
        print("Error:", e)
    finally:
        cm.close_connection()
        

def reserve(tokens):     
    # reserve <date> <vaccine>
    global current_patient 
    # check 1: Check if there's any user logged in 
    if current_caregiver is None and current_patient is None: 
        print("Please login first!")
        return
    # check 2: check if the current logged-in user is a patient
    if current_patient is None:
        print("Please login as a patient!") 
        return
    # check 3: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3: 
        print("Please try again!")  
        return

    cm = ConnectionManager() 
    conn = cm.create_connection()
    cursor = conn.cursor(as_dict=True)  
    
    # check 4: check if there's available caregivers    
    date = tokens[1]
    date_tokens = date.split("-")
    month = int(date_tokens[0])
    day = int(date_tokens[1])
    year = int(date_tokens[2])
    vaccine_name = tokens[2] 

    search_caregiver = "SELECT Username FROM Availabilities WHERE Time = %s ORDER BY Username"  
    get_vaccine = "SELECT Doses FROM Vaccines WHERE Name = %s" 
    
    try:
        d = datetime.datetime(year, month, day) 
        cursor.execute(search_caregiver, d)
        row = cursor.fetchone()
        if row is None:
            print("No Caregiver is available!")  
            return
        else:
            chosen_caregiver = str(row['Username'])
       
        
    # check 5: check if there's enough doses      
        cursor.execute(get_vaccine, vaccine_name) 
       
        for row in cursor:
            available_doses = row["Doses"] 
            
        if available_doses == 0:
            print("Not enough available doses!")  
            return
        
        vaccine = Vaccine(vaccine_name, available_doses).get()     
        vaccine.decrease_available_doses(1)  

        appointment_reserved =  "INSERT INTO Appointment VALUES (%d, %s, %s, %s)" 

        cursor.execute(appointment_reserved, (d, chosen_caregiver, current_patient.username, vaccine_name))

        drop_availability = "DELETE FROM Availabilities WHERE Time = %d AND Username = %s"       
        cursor.execute(drop_availability, (d, chosen_caregiver))    
        conn.commit()

        appointment_details = "SELECT Id, Cusername FROM Appointment WHERE Pusername = %s AND Time = %d and Vname = %s" 
        cursor.execute(appointment_details, (current_patient.username, d, vaccine_name))
        for row in cursor:
            print("Appointment ID: " + str(row["Id"]) + ", Caregiver username: " + str(row["Cusername"]))    
            
    except pymssql.Error as e:
        print("Error occurred when making reservation")
        print("Db-Error:", e)
        quit()
    except ValueError as e:
        print("Invalid statement; try again")
        print("Error:", e)
        return
    except Exception as e:
        print("Error occurred when making reservation") 
        print("Error:", e)
    finally:
        cm.close_connection()  
    return False


def upload_availability(tokens):
    #  upload_availability <date>
    #  check 1: check if the current logged-in user is a caregiver
    global current_caregiver
    if current_caregiver is None:
        print("Please login as a caregiver first!")
        return

    # check 2: the length for tokens need to be exactly 2 to include all information (with the operation name)
    if len(tokens) != 2: 
        print("Please try again!")
        return

    date = tokens[1] 
    # assume input is hyphenated in the format mm-dd-yyyy
    date_tokens = date.split("-")
    month = int(date_tokens[0])
    day = int(date_tokens[1])
    year = int(date_tokens[2])
    try:
        d = datetime.datetime(year, month, day)
        current_caregiver.upload_availability(d)
    except pymssql.Error as e:
        print("Upload Availability Failed")
        print("Db-Error:", e)
        quit()
    except ValueError:
        print("Please enter a valid statement")
        print("Error:", e)
        return
    except Exception as e:
        print("Error occurred when uploading availability")
        print("Error:", e)
        return
    print("Availability uploaded!")


def cancel(tokens):
    """
    TODO: Extra Credit
    """
    pass


def add_doses(tokens):
    #  add_doses <vaccine> <number>
    #  check 1: check if the current logged-in user is a caregiver
    global current_caregiver
    if current_caregiver is None:
        print("Please login as a caregiver first!")
        return

    #  check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Please try again!")
        return

    vaccine_name = tokens[1]
    doses = int(tokens[2])
    vaccine = None
    try:
        vaccine = Vaccine(vaccine_name, doses).get()
    except pymssql.Error as e:
        print("Error occurred when adding doses")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error occurred when adding doses")
        print("Error:", e)
        return

    # if the vaccine is not found in the database, add a new (vaccine, doses) entry.
    # else, update the existing entry by adding the new doses
    if vaccine is None:
        vaccine = Vaccine(vaccine_name, doses)
        try:
            vaccine.save_to_db()
        except pymssql.Error as e:
            print("Error occurred when adding doses")
            print("Db-Error:", e)
            quit()
        except Exception as e:
            print("Error occurred when adding doses")
            print("Error:", e)
            return
    else:
        # if the vaccine is not null, meaning that the vaccine already exists in our table
        try:
            vaccine.increase_available_doses(doses)
        except pymssql.Error as e:
            print("Error occurred when adding doses")
            print("Db-Error:", e)
            quit()
        except Exception as e:
            print("Error occurred when adding doses")
            print("Error:", e)
            return
    print("Doses updated!")


def show_appointments(tokens):
    # show_appointments
    # check 1: Check if there's any user logged in
    
    global current_caregiver
    global current_patient
    
    if current_caregiver is None and current_patient is None: 
        print("Please login first!")
        return
    
    # check 2: the length for tokens need to be exactly 1 to include all information (with the operation name)
    if len(tokens) != 1: 
        print("Please try again!") 
        return

    cm = ConnectionManager() 
    conn = cm.create_connection() 
    cursor = conn.cursor(as_dict=True)  
    
    try:
        if current_caregiver is not None:
            
            caregiver_info = "SELECT Id, Vname, Time, Pusername FROM Appointment WHERE Cusername = %s ORDER BY Id"
            cursor.execute(caregiver_info, current_caregiver.username)
            cinfo = cursor.fetchall()
            if len(cinfo) == 0:
                print("No appointment scheduled.")
                return
            
            for i in range(0, len(cinfo)): 
                print(str(cinfo[i]["Id"]) + " " + str(cinfo[i]["Vname"]) + " " + str(cinfo[i]["Time"]) + " " + 
                            str(cinfo[i]["Pusername"]))
                 
        elif current_patient is not None:
            patient_info = "SELECT Id, Vname, Time, Cusername FROM Appointment WHERE Pusername = %s ORDER BY Id"
            cursor.execute(patient_info, current_patient.username)
            pinfo = cursor.fetchall()
            if len(pinfo) == 0:
                print("No appointment scheduled.")
                return
            
            for i in range(0, len(pinfo)): 
                print(str(pinfo[i]["Id"]) + " " + str(pinfo[i]["Vname"]) + " " + str(pinfo[i]["Time"]) + " " + 
                            str(pinfo[i]["Cusername"])) 
                 
    except pymssql.Error as e:
        print("Error occurred when showing appointments")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error occurred when showing appointments")
        print("Error:", e)
    finally:
        cm.close_connection() 
    return False 
    

def logout(tokens): 
    # Logout
    global current_caregiver
    global current_patient 
    
    # check 1: the length for tokens need to be exactly 1 to include all information (with the operation name)
    if len(tokens) != 1:
        print("Please try again!") 
        return

    # check 2: Check if there's any user logged in
    try:
        if current_caregiver == current_patient:
            print("Please login first.")
            return 
        current_caregiver = None
        current_patient = None
        print("Successfully logged out!")
    except Exception as e:
        print("Error occurred when logging out")
        print("Error:", e)
    return
    

def start():
    stop = False
    print()
    print(" *** Please enter one of the following commands *** ")
    print("> create_patient <username> <password>")  # //TODO: implement create_patient (Part 1)
    print("> create_caregiver <username> <password>")
    print("> login_patient <username> <password>")  # // TODO: implement login_patient (Part 1)
    print("> login_caregiver <username> <password>")
    print("> search_caregiver_schedule <date>")  # // TODO: implement search_caregiver_schedule (Part 2)
    print("> reserve <date> <vaccine>")  # // TODO: implement reserve (Part 2)
    print("> upload_availability <date>")
    print("> cancel <appointment_id>")  # // TODO: implement cancel (extra credit)
    print("> add_doses <vaccine> <number>")
    print("> show_appointments")  # // TODO: implement show_appointments (Part 2)
    print("> logout")  # // TODO: implement logout (Part 2)
    print("> Quit")
    print()
    while not stop:
        response = ""
        print("> ", end='')

        try:
            response = str(input())
        except ValueError:
            print("Please try again!")
            break

        # response = response.lower()
        tokens = response.split(" ")
        if len(tokens) == 0:
            ValueError("Please try again!")
            continue
        operation = tokens[0]
        if operation == "create_patient":
            create_patient(tokens)
        elif operation == "create_caregiver":
            create_caregiver(tokens)
        elif operation == "login_patient":
            login_patient(tokens)
        elif operation == "login_caregiver":
            login_caregiver(tokens)
        elif operation == "search_caregiver_schedule":
            search_caregiver_schedule(tokens)
        elif operation == "reserve":
            reserve(tokens)
        elif operation == "upload_availability":
            upload_availability(tokens)
        elif operation == cancel:
            cancel(tokens)
        elif operation == "add_doses":
            add_doses(tokens)
        elif operation == "show_appointments":
            show_appointments(tokens)
        elif operation == "logout":
            logout(tokens)
        elif operation == "quit":
            print("Bye!")
            stop = True
        else:
            print("Invalid operation name!")


if __name__ == "__main__":
    '''
    // pre-define the three types of authorized vaccines
    // note: it's a poor practice to hard-code these values, but we will do this ]
    // for the simplicity of this assignment
    // and then construct a map of vaccineName -> vaccineObject
    '''

    # start command line
    print()
    print("Welcome to the COVID-19 Vaccine Reservation Scheduling Application!")

    start()
