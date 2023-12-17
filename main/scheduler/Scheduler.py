from msilib.schema import ControlEvent
from xml.sax.xmlreader import InputSource
from model.Vaccine import Vaccine
from model.Caregiver import Caregiver
from model.Patient import Patient
from util.Util import Util
from db.ConnectionManager import ConnectionManager
import pymssql
import re
import datetime


'''
objects to keep track of the currently logged-in user
Note: it is always true that at most one of currentCaregiver and currentPatient is not null
        since only one user can be logged-in at a time
'''
current_patient = None

current_caregiver = None


def create_patient(tokens):
    # create_patient <username><password>
    # following similar logic of creating caregiver 
    if len(tokens) != 3:
        print("Failed to create user.")
        return
    
    username = tokens[1]
    password = tokens[2]

    # checking if username already exists
    if username_exists_patient(username):
        print("Username taken, try again!")
        return

    strong_pathword = check_password(password)
    if strong_pathword == False: return
    
    salt = Util.generate_salt()
    hash = Util.generate_hash(password, salt)

    patient = Patient(username, salt=salt, hash=hash)

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
    
    strong_pathword = check_password(password)
    if strong_pathword == False: return

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


def username_exists_patient(username):
    cm = ConnectionManager()
    conn = cm.create_connection()

    select_username = "SELECT * FROM Patients WHERE Username = %s"
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute(select_username, username)
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


def login_patient(tokens):
    # login_patient <username> <password>
    # following same logic of logining patient
    global current_patient
    if current_patient is not None or current_caregiver is not None:
        print("User already logged in.")
        return

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
    if current_patient == current_caregiver:
        print("Please login first!")
        return
    if len(tokens) != 2:
        print("Please input the right arguments.")
        return

    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor(as_dict=True)

    try:
        # Parse date input and generate corresponding query statements
        date_tokens = tokens[1].split("-")
        month = int(date_tokens[0])
        day = int(date_tokens[1])
        year = int(date_tokens[2])
        d = datetime.datetime(year, month, day)

        get_available_dates = "SELECT Time, Username FROM Availabilities WHERE Time = %s ORDER BY Username"
        get_vaccines = "SELECT Name, Doses FROM Vaccines"

        # Query all results of availabilities and vaccines
        cursor.execute(get_available_dates, d)
        schedule_rows = cursor.fetchall()
        cursor.execute(get_vaccines)
        vaccine_rows = cursor.fetchall()

        if len(schedule_rows) == 0:  # If no appointments avaiable this day
            print("There are no appointments available on", tokens[1])
            return
        
        print("-----------------------")
        print("{: >10}\t{: >10}\t{: >10}\t{: >1}".format("Caregiver", "Vaccine", "Doses", "#"))
        # print out each caregiver followed by the dose number of each vaccine
        for row in schedule_rows:
            print("{}\t".format(row['Username']), end="")
            for i in range(0, len(vaccine_rows)):
                print("{: >10}\t{: >10}".format(vaccine_rows[i]["Name"],vaccine_rows[i]["Doses"]), end="")
            print("")

    # handling possible errors
    except pymssql.Error:
        print("Retrieving dates failed; try again")
        return
    except ValueError:
        print("Please enter a valid date")
        return
    except Exception:
        print("Error occurred when checking availability; try again")
        return
    finally:
        cm.close_connection()
        


def reserve(tokens):
    # check input validality and 
    if current_patient == current_caregiver:
        print("Please login first")
        return
    if current_patient is None:
        print("Please login as a patient to reserve")
        return
    if len(tokens) != 3:
        print("Failed to execute; wrong arguments")
        return
    
    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor(as_dict=True)
    try:
        # Parse the date and attempt to retrieve date, caregiver, and vaccine name from the database
        date_tokens = tokens[1].split("-")
        month = int(date_tokens[0])
        day = int(date_tokens[1])
        year = int(date_tokens[2])
        d = datetime.datetime(year, month, day)
        find_available_dates = "SELECT TOP 1 Time, Username FROM Availabilities WHERE Time = %s ORDER BY Username"
        cursor.execute(find_available_dates, d)
        dates = cursor.fetchall()
        if len(dates) == 0:
            print("There are no caregivers available for this date")
            return
        assigned_caregiver = dates[0]["Username"]
        assigned_date = dates[0]["Time"]
        vaccine_name = tokens[2]
        vaccine = Vaccine(vaccine_name, available_doses=None).get()

        # Check vaccine is valid and update supply number
        if vaccine is None:
            print("Our caregivers do not have this vaccine. Try again inputting a valid vaccine from this list:")
            cursor.execute("SELECT Name FROM Vaccines")
            for row in cursor:
                print(row["Name"])
            return
        if vaccine.available_doses == 0:
            print("There are not enough doses left. Try another vaccine brand.")
            return
        vaccine.decrease_available_doses(1)

        # Add appointment to database. set appointment ID is as the highest id number + 1
        add_appointment = "INSERT INTO Appointments VALUES (%d, %s, %s, %s, %s)"
        temp_cursor = conn.cursor()
        temp_cursor.execute("SELECT MAX(a_id) FROM Appointments")
        highest_row = temp_cursor.fetchone()[0]
        if highest_row is None:
            cursor.execute(add_appointment, (1
                                             , assigned_date, current_patient.username, assigned_caregiver,
                                             vaccine_name))
        else:
            cursor.execute(add_appointment, (highest_row + 1
                                             , assigned_date, current_patient.username, assigned_caregiver,
                                             vaccine_name))

        # drop that caregiver's availability from the availability database
        drop_availability = "DELETE FROM Availabilities WHERE Time = %s AND Username = %s"
        cursor.execute(drop_availability, (d, assigned_caregiver))

        conn.commit()

        # print information about the appointment
        print("Success! Below is information on your appointment:")
        print("-----------------------")
        get_appointment = "SELECT a_id, date, c_name, v_name FROM appointments WHERE p_name = %s AND c_name = %s AND date = %s"
        cursor.execute(get_appointment, (current_patient.username, assigned_caregiver, assigned_date))
        print("{: >10}\t{: >10}\t{: >10}\t{: >10}".format("Appointment ID", "Date", "Caregiver", "Vaccine"))
        for row in cursor:
            print("{: >10}\t{: >10}\t{: >10}\t{: >10}".format(row["a_id"], str(row["date"]), row["c_name"],
                                                              row["v_name"]))

    except pymssql.Error as e:
        print("Error trying to create appointment; try again")
        print("DBError:", e)
        return
    except ValueError as e:
        print("Invalid date format; try again")
        print("Error:", e)
        return
    except Exception as e:
        print("Error occurred when creating an appointment; try again")
        print("Error:", e)
        return
    finally:
        cm.close_connection()

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
        print("Please enter a valid date!")
        return
    except Exception as e:
        print("Error occurred when uploading availability")
        print("Error:", e)
        return
    print("Availability uploaded!")


def cancel(tokens):
    if current_patient == current_caregiver:
        print("Please login first!")
        return
    if len(tokens) != 2:
        print("Failed to execute commands; wrong arguments given")
        return
    try:
        cm = ConnectionManager()
        conn = cm.create_connection()
        cursor = conn.cursor(as_dict=True)
        cancel_id = tokens[1]

        # we need to check first if the users' provided appointment id is actually their own appointments
        get_appointment = "SELECT a_id, date, p_name, c_name, v_name FROM Appointments WHERE a_id = %d"
        cursor.execute(get_appointment, cancel_id)
        appointment = cursor.fetchone()
        valid_appointment = False
        if current_patient is not None:
            if appointment['p_name'] == current_patient.username:
                valid_appointment = True
            else:
                print("You don't have appointment with a_id:", cancel_id)
        elif current_caregiver is not None:
            if appointment['c_name'] == current_caregiver.username:
                valid_appointment = True
            else:
                print("You don't have appointment with a_id:", cancel_id)

        # If the provided appointment id is valid, then delete that appointment
        if valid_appointment:
            delete_appointment = "DELETE FROM Appointments WHERE a_id = %d"
            vaccine = Vaccine(appointment["v_name"], None).get()
            vaccine.increase_available_doses(1)  # add back the vaccine used
            cursor.execute(delete_appointment, cancel_id)
            conn.commit()
            print("Appointment successfully cancelled.")
            if current_patient is not None:  # if the appointment is cancelled by patient, add the availability back to the corresponding caregiver
                appointment_date = appointment['date']
                caregiver = appointment['c_name']
                cursor.execute("INSERT INTO Availabilities VALUES (%d, %d)", (appointment_date, caregiver))
                conn.commit()
        else:
            print("Could not find appointment with id:", cancel_id)
    except pymssql.Error as e:
        print("Failed to retrieve appointment information")
        print("DBError:", e)
    except Exception as e:
        print("Could not find appointment with id:", cancel_id)
    finally:
        cm.close_connection()


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
    if current_patient == current_caregiver:
        print("Please login first!")
        return
    if len(tokens) != 1:
        print("Failed to show appointments, wrong number of arguments")
        return
    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor(as_dict=True)
    try:
        if current_patient is not None:
            # Attempt to get appointments for the current logged in patient and then print them
            get_patient_appointments = "SELECT a_id, v_name, date, c_name FROM Appointments WHERE " \
                                       "p_name = %s ORDER BY a_id"
            cursor.execute(get_patient_appointments, current_patient.username)
            appointments = cursor.fetchall()
            if len(appointments) == 0:
                print("There are no appointments scheduled")
                return
            print("-" * (len(appointments) * 20))
            print("{: >10}\t{: >10}\t{: >10}\t{: >10}\t".format("Appointment ID", "Vaccine", "Date", "Caregiver"),
                  end="")
            print("")

            for i in range(0, len(appointments)):
                print("{: >10}\t{: >10}\t{: >10}\t{: >10}\t"
                      .format(appointments[i]["a_id"], appointments[i]["v_name"], str(appointments[i]["date"]),
                              appointments[i]["c_name"]))

        elif current_caregiver is not None:
            # Attempt to get the appointments for the current logged in caregiver.
            get_caregiver_appointments = "SELECT a_id, v_name, date, p_name FROM Appointments WHERE " \
                                         "c_name = %s ORDER BY a_id"
            cursor.execute(get_caregiver_appointments, current_caregiver.username)
            appointments = cursor.fetchall()
            if len(appointments) == 0:
                print("There are no appointments scheduled")
                return
            print("-" * (len(appointments) * 20))
            print("{: >10}\t{: >10}\t{: >10}\t{: >10}\t".format("Appointment ID", "Vaccine", "Date", "Patient"), end="")
            print("")
            for i in range(0, len(appointments)):
                print("{: >10}\t{: >10}\t{: >10}\t{: >10}\t"
                      .format(appointments[i]["a_id"], appointments[i]["v_name"], str(appointments[i]["date"]),
                              appointments[i]["p_name"]))

    except pymssql.Error as e:
        print("Error in retrieving appointments")
        print("DBError:", e)
    except Exception as e:
        print("Error in showing appointments")
        print("Error:", e)
    finally:
        cm.close_connection()


def logout(tokens):
    global current_patient
    global current_caregiver
    try:
        # log out either a patient or a caregiver
        if current_patient != current_caregiver:
            current_patient = None
            current_caregiver = None
            print("Successfully logged out!")
            start()
        else:
            print("Please login first!")
    except Exception as e:
        print("Failed to logout!")
        print("Error:", e)
    return

def check_password(password):  # password strength checking based on regex
    valid_password = True
    if len(password) < 8:
        print("Password must be at least 8 characters")
        valid_password = False
    if re.search(r'[a-z]', password) is None:
        print("Password must have at least 1 letter")
        valid_password = False
    if re.search(r'[A-Z]', password) is None:
        print("Password must have at least 1 capital letter")
        valid_password = False
    if re.search(r"[\d]+", password) is None:
        print("Password must have at least 1 number")
        valid_password = False
    if re.search(r"[!@#?]+", password) is None:
        print("Password must have at least 1 special character from (!, @, #, ?)")
        valid_password = False
    return valid_password


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

        #response = response.lower()
        tokens = response.split(" ")
        tokens[0] = tokens[0].lower()
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
        elif operation == "cancel":
            cancel(tokens)
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
