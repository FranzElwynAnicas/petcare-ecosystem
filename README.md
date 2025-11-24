# PetCare Ecosystem 🐾  
A comprehensive pet care platform integrating adoption services, veterinary management, and shelter operations using Django and Flask.  
This project is created for our course **System Integration**.

---

## 👥 Members
- **Franz Elwyn F. Anicas**  
- **Bella Pereyra Whitehead**  
- **Kamil Ogoy**

---

## 🎯 System Overview
This project demonstrates a real-world microservices architecture with three interconnected systems:

### 🏠 Adoption System (Django)
- Pet browsing and search functionality  
- Online adoption applications  
- User profiles and appointment management  
- Real-time vet appointment scheduling  

### 🏥 Veterinary System (Django)
- Appointment scheduling and management  
- Medical records and health tracking  
- Vaccine and treatment records  
- Vet staff dashboard  

### 🐕 Shelter System (Flask)
- Animal inventory management  
- Adoption request processing  
- Shelter operations dashboard  
- REST API for external integrations  

---

## 🚀 Quick Start

### **Prerequisites**
- Python 3.8+  
- pip (Python package manager)  

### **Installation & Setup**

#### **1. Adoption System (Django)**
cd adoption_django
python -m venv venv

Windows: venv\Scripts\activate
macOS/Linux: source venv/bin/activate

pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8000
Access: http://localhost:8000

---

#### **2. Veterinary System (Django)**
cd veterinary
python -m venv venv

Windows: venv\Scripts\activate
macOS/Linux: source venv/bin/activate

pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 6001
Access: http://localhost:6001

---

#### **3. Shelter System (Flask)**
cd shelter_flask
python -m venv venv

Windows: venv\Scripts\activate
macOS/Linux: source venv/bin/activate

pip install -r requirements.txt
python app.py
Access: http://localhost:5001

---

## 🔄 Running All Systems
- Open three separate terminal windows  
- Start each system in order: **Shelter (5001) → Veterinary (6001) → Adoption (8000)**  
- Each system must run in its own activated virtual environment  

---

## 🏗 Architecture
Adoption (Django) ↔ Veterinary (Django)
↓ ↓
Shelter (Flask) External Systems

---

## 📁 Project Structure
petcare-ecosystem/
├── adoption_django/ # Django adoption portal
├── veterinary/ # Django veterinary system
├── shelter_flask/ # Flask shelter management


---

## 🔧 Key Features
- Pet browsing & adoption applications  
- Veterinary appointment scheduling  
- Shelter inventory management  
- Real-time cross-system data sync  
- REST API integration  

---

## 🔗 Live Systems
- Adoption: **http://localhost:8000**  
- Veterinary: **http://localhost:6001**  
- Shelter: **http://localhost:5001**  

---

## 🛠 Tech Stack
**Django**, **Flask**, **REST APIs**, **Bootstrap**

**Tags:** python, django, flask, pet-care, adoption-system, veterinary, shelter-management, microservices

---



