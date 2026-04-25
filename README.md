# Zeebull - Complete Hospitality Solution

Zeebull is a multi-platform hospitality management system designed for resorts, hotels, and multi-branch hospitality businesses. It provides a seamless experience for guests, employees, and management through integrated web and mobile applications.

## 🚀 Features

- **Guest Management**: Comprehensive booking, check-in, and check-out workflows.
- **Inventory & Services**: Real-time tracking of resort inventory, services, and guest requests.
- **Multi-App Ecosystem**:
  - **Admin Dashboard**: Web-based management portal.
  - **Mobile Apps**: Dedicated Flutter apps for Employees and Owners.
  - **User End**: Customer-facing web interface.
- **Landing Page**: Modern, responsive landing page for branding and lead generation.
- **Billing & GST**: Integrated GST-compliant billing system.

## 🛠 Tech Stack

- **Backend**: FastAPI (Python), SQLAlchemy, PostgreSQL, Gunicorn/Uvicorn.
- **Frontend (Web)**: React, Bootstrap.
- **Mobile**: Flutter (Dart).
- **Deployment**: Nginx, Docker, GCP, Render.

## 📂 Project Structure

- `ResortApp/`: Core backend source code.
- `Mobile/`: Flutter projects for Employee and Owner apps.
- `dasboard/`: Admin dashboard frontend.
- `userend/`: User-facing frontend.
- `landingpage/`: Public landing page.
- `gcp_deploy/`: Google Cloud Platform deployment scripts.

## ⚙️ Development Setup

### Backend
1. Navigate to `ResortApp/`.
2. Install dependencies: `pip install -r requirements.txt`.
3. Run local server: `python main.py` (Default port: 8011).

### Mobile
1. Navigate to `Mobile/employee/` or `Mobile/owner/`.
2. Run `flutter pub get`.
3. Run `flutter run`.

## 🌐 Deployment

The system is designed to be deployed on Ubuntu servers using Nginx and Systemd.
- Access URL: `http://35.224.72.199/`
- Backend API Docs: `http://35.224.72.199/api/docs`

---
*Created and maintained by TeqMates.*
