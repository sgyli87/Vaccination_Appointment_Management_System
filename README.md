## CSE 414 Database Management
This project is a simulation of registering for a COVID-19 vaccine appointment. The tech stack of this database application includes SQL in python with pymssql, ER diagrams, data normalization, and SQL queries / updates and Azure database.


## Guide
The application will prompt the following menu when started:

<pre>
  Welcome to the COVID-19 Vaccine Reservation Scheduling Application!
   *** Please enter one of the following commands ***
  > create_patient <username> <password>
  > create_caregiver <username> <password>
  > login_patient <username> <password>
  > login_caregiver <username> <password>
  > search_caregiver_schedule <date>
  > reserve <date> <vaccine>
  > upload_availability <date>
  > cancel <appointment_id>
  > show_all_available_dates
  > add_doses <vaccine> <number>
  > get_vaccine_information
  > show_appointments
  > logout
  > help (see this menu again)
  > quit
  </pre>

* create_patient and create_caregiver allows the user to create a patient to receive the vaccine or a caregiver to adminster it. Note that a caregiver does not require any medical license or degree as this is purely a simulation. Passwords are checked using Regex and then hashed using the SHA-256 algorithm if valid.
* login_patient and login_caregiver allows the user to login as an existing patient and caregiver.
* search_caregiver_schedule allows a caregiver or patient to search for caregivers available on the given date as well as the number of doses of each vaccine left.
* reserve allows a patient to reserve a valid date and vaccine (assuming there are doses left) for an appointment with a caregiver that day. The caregiver is chosen in ascending alphabetical order.
* upload_availability allows caregivers to upload a date when they are available for patients to make an appointment with them.
* cancel allows both patients and caregivers to cancel a valid date they have an appointment on.
* show_all_available_dates shows all available dates for every caregiver.
* add_doses allows caregivers to add doses to existing vaccines or to create a new vaccine (real or fiction).
* get_vaccine_information displays all existing vaccines in the database with their number of doses remaining.
* show_appointments shows appointments for the logged in patient or caregiver
* logout is self-explanatory
* help displays the main menu again. Note that the menu will not print again after commands are entered so that information is not lost by the menu being printed a lot of times.
* quit terminates the program.
