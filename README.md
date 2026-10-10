# 🌾 Farm Cart

### A Direct Farm-to-Consumer Marketplace

Farm Cart is a web-based agricultural marketplace built with **Flask and Python** that connects farmers directly with consumers. Farmers can list agricultural products, manage inventory, and track orders, while consumers can discover, search, filter, and purchase produce.

The platform also includes a regional agricultural insights feature with crop recommendations and profit visualization for **Bhopal, Madhya Pradesh**.

---

## 📌 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Technology Stack](#️-technology-stack)
- [How It Works](#-how-it-works)
- [REST API Endpoints](#-rest-api-endpoints)
- [Installation and Setup](#️-installation-and-setup)
- [Project Structure](#-project-structure)
- [Team Agile 11](#-team-agile-11)
- [Future Scope](#-future-scope)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🚀 Overview

Traditional agricultural supply chains can involve multiple intermediaries between farmers and consumers. Farm Cart aims to simplify this process by providing a shared digital marketplace where farmers can showcase their produce and buyers can explore available products.

### 🎯 Project Objectives

- Enable farmers to sell agricultural products directly to consumers.
- Provide product listing and inventory management.
- Simplify product discovery through search and filtering.
- Allow buyers and sellers to manage and track orders.
- Present regional crop recommendations and profit-related insights.
- Provide a centralized dashboard for marketplace features.

---

## ✨ Key Features

### 🔐 1. Authentication and User Profiles

- User registration and login.
- Farmer profiles and account access.
- Session management using Flask-Login.

### 🌱 2. Product Management

- Add, edit, and view agricultural product listings.
- Manage product prices and available stock.
- Display product information to potential buyers.

### 🛒 3. Marketplace and Product Discovery

- Browse available agricultural products.
- Search by product name or description.
- Filter products by farmer.
- Place orders through the marketplace interface.

### 📦 4. Order Management

- View orders placed as a buyer.
- Track orders received as a seller.
- Access order information through the dashboard.

### 📊 5. Agricultural Insights

- Crop recommendations for the Bhopal, Madhya Pradesh region.
- Profit visualization through graphs.
- Agricultural insights intended to support informed crop-related decisions.

### 🖥️ 6. Centralized Dashboard

A unified dashboard provides access to:

- Orders
- Product listings
- Agricultural insights
- Support

---

## 🛠️ Technology Stack

| Category           | Technologies              |
| ------------------ | ------------------------- |
| Backend            | Python, Flask             |
| ORM                | Flask-SQLAlchemy          |
| Authentication     | Flask-Login               |
| Frontend           | HTML, Jinja2 Templates    |
| Styling            | Tailwind CSS              |
| Data Visualization | Chart.js                  |
| Database           | SQLite                    |
| Security Utilities | Werkzeug password hashing |
| Logging            | Python logging            |

---

## 🔄 How It Works

### Farmer Workflow

1. Register or log in.
2. Open the dashboard.
3. Add and manage agricultural products.
4. View and manage received orders.
5. Explore regional agricultural insights.

### Consumer Workflow

1. Browse the marketplace.
2. Search and filter available products.
3. Explore product listings.
4. Log in and place an order.
5. Access orders through the dashboard.

---

## 🔌 REST API Endpoints

The project includes the following API endpoints:

| Endpoint                | Purpose                        |
| ----------------------- | ------------------------------ |
| `/api/farmers/register` | Farmer registration            |
| `/api/products`         | Product-related API operations |
| `/api/orders`           | Order-related API operations   |

For request methods, parameters, authentication requirements, and response formats, refer to the application implementation.

---

## ⚙️ Installation and Setup

### Prerequisites

- Python 3.8 or later
- `pip`
- Git

### 1. Clone the Repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd <YOUR_PROJECT_DIRECTORY>
```

Replace the placeholders with the actual repository URL and directory name.

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

**Windows:**

```bash
venv\\Scripts\\activate
```

**Linux / macOS:**

```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Start the Application

```bash
python app.py
```

### 5. Open the Application

Visit `http://localhost:5000` in your browser.

The SQLite database is configured to be created automatically on the first run.

---

## 📁 Project Structure

The structure below is illustrative. Actual filenames and directories may differ.

```text
Farm-Cart/
├── app.py
├── requirements.txt
├── templates/
├── static/
├── instance/
├── README.md
└── ...
```

- `app.py` — Application entry point.
- `requirements.txt` — Python dependencies.
- `templates/` — Server-rendered Jinja2 templates.
- `static/` — Static assets such as stylesheets and JavaScript.
- `instance/` — Possible location for local application data, depending on configuration.

---

## 👥 Team Agile 11

**Farm Cart is a collaborative team project developed by Team Agile 11.**

### Team Members

1. Lakshya Raj Malviya
2. Yash Goyal
3. Harshika Singh
4. Swayam Shukla
5. Sneha Sanodia
6. Mansi Jain
7. Hemant Yadav
8. Aparna Jha
9. Anshika Sharma
10. Alaknkrit Purohit
11. Raksha Pandey

---

## 🔮 Future Scope

Potential directions for future development include:

- Online payment integration.
- Delivery and shipment tracking.
- Advanced crop recommendation models.
- Expanded regional agricultural datasets.
- Weather-aware agricultural insights.
- Farmer verification and product quality indicators.
- Automated testing and production deployment.
- Enhanced reporting and marketplace analytics.

These are possible enhancements, not claims about existing functionality.

---

## 🤝 Contributing

Farm Cart is a collaborative project. Suggestions and constructive feedback can help improve the platform.

For proposed changes, consider creating a feature branch, testing the implementation, and submitting a pull request.

---

## 📄 License

A license has not been specified for this project. Add an appropriate `LICENSE` file before distributing the project under an open-source license.

---

<p align="center">
  <strong>🌾 Farm Cart — Connecting Farmers and Consumers Through Technology</strong>
  <br>
  <em>Built collaboratively by Team Agile 11.</em>
</p>
