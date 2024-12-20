## About TimeSyncPro

**TimeSyncPro** is a comprehensive absence and leave management system designed to simplify holiday requests, 
absence tracking, and work schedule planning for organizations. With features like shift management, holiday approvals, 
and absence reporting, TimeSyncPro empowers companies to manage employee time efficiently while ensuring transparency and flexibility for all users.

---

## Used Technologies

TimeSyncPro is built using a robust stack of modern technologies:

- **Django**: A high-level Python web framework that promotes rapid development and clean, pragmatic design.
- **PostgreSQL**: A powerful, open-source relational database used for managing and storing application data securely and efficiently.
- **Redis**: An in-memory data structure store used as a caching layer to enhance application performance.
- **Celery**: A distributed task queue used for handling asynchronous tasks and job queues.
- **Celery Beat**: A scheduler for periodic tasks in Celery, ensuring automated and recurring workflows.


## Installation

## 1. **Clone the repository:**

      git clone https://github.com/Iliyan-H-Iliev/TimeSyncPro.git
      cd repository

## 2. **Create a Virtual Environment:**

      python -m venv .venv
      source .venv/bin/activate 

   
## 3. **Install dependencies:**

       pip install -r requirements.txt

## 4. **Configure the Environment Variables:**

  Create an .env file in the root directory and add the necessary environment variables.


## 5. **Apply database migrations:**

       python manage.py makemigrations
       python manage.py migrate

## 6. **Create default groups:**

       python manage.py create_groups

## 7. **Install Docker, Open a new terminal, and run the command:**

       docker run -d --name redis-stack-server -p 6379:6379 redis/redis-stack-server:latest

## 8. **Open a new terminal and run the command:**
  
       celery -A VolunteerAct worker --pool=solo --loglevel=info 

## 9. **Open a new terminal and run the command:**
          
         celery -A TimeSyncPro beat --loglevel=INFO
   
## 10. **Run the development server:**

        python manage.py runserver

## 11. **Access the application: Open your browser and navigate to:**

    http://127.0.0.1:8000/



# Site Feature Descriptions

## 1. **User Creation**
Start by creating a user account to gain access to the platform and begin managing your company efficiently.

## 2. **Company and Profile Setup**
Create your company and set up your profile, including important details about your organization.

## 3. **Setup Departments, Teams, and Shifts**
For an optimal experience, set up **Departments**, **Teams**, and **Shifts** first. This structure will allow 
for better organization and streamlined management.

## 4. **Register Employees and Assign Roles**
Register your employees on the platform and assign them appropriate roles within the company. Roles come with different 
permissions, ensuring access is tailored to their responsibilities.
  - **Roles include:**
    - HR Manager
    - Manager
    - Team Leader
    - Staff

## 5. **Employee Account Activation**
Every registered employee will receive an **email link** to activate their account and set their password, ensuring secure access to the system.

## 6. **Holiday Approver Assignment**
You can assign a **Holiday Approver** for each department or team. If no approver is selected, 
the **Company Administrator** (the person who registered the company) will be the default approver. 
This setting can be modified later through the company profile.

## 7. **Employee Dashboard: Shifts, Holidays, and Absences**
- Employees can view their **working days** and **days off** directly from their dashboard.
   - If shifts are configured, these details will reflect the assigned shifts.
   - If no shifts are set, the default schedule is **Monday to Friday, 9:00 AM - 5:00 PM**.
- Employees can also view their **approved holidays** and other absences, including:
   - Sick leave
   - Unpaid leave
   - Personal leave
   - Other absences

## 8. **Holiday Requests**
Employees can easily **request holidays** through the platform. Their assigned **Holiday Approver** 
will receive an email notification about the pending request for approval.
- Only requester can cancel the request before or after approval.

## 9. **Holiday Review Access**
The following roles have access to **review and approve or deny holiday requests**:
- HR Managers
- Company Administrators (can be multiple)
- Holiday Approvers

## 10. **Adding Absences**
Managers, HR personnel, and Company Administrators can **manually add absences** for employees, ensuring accurate attendance tracking.

## 11. **Reports Section**
The Reports section provides detailed insights into employee attendance. You can filter reports by:
- Date range
- Department
- Team

## 12. **Bradford Factor Report**
Track employee absence trends using the **Bradford Factor Report**. This report covers the past **12 months** 
and helps identify patterns in unplanned absences.

## 13. Additional Functionality

- **Automated Working Dates Generation:**  
  Every year on **January 1st (01.01)**, the system automatically generates working dates for each shift.  

  - **Employee Working Days Visibility:**  
    Employees can view their working days for:  
    - **The current year**  
    - **Two years in advance**  

    This feature ensures that employees and managers always have an up-to-date overview of their work schedule for better planning and management.
  

- **Automated Leave Days Allocation:**  
  At the beginning of each year, the system automatically sets leave days for the next year for all employees based on company policies or predefined rules.  

- **Flexibility in Leave Management:**  
  Managers and administrators can adjust the allocated leave days as needed to accommodate specific employee agreements or policy updates.

- **Employee Visibility:**  
  Employees can view their leave balance for the current year and the next year, ensuring they have adequate information for planning.
    
    