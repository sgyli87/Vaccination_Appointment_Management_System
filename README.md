## CSE 414 Database Management
This project is a simulation of registering for a COVID-19 vaccine appointment. The tech stack of this database application includes SQL in python with pymssql, ER diagrams, data normalization, and SQL queries / updates and Azure database.


## Guide
The application will prompt the following menu when started:

'''
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
'''
