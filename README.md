# Farm Cart — Direct Farm-to-Consumer Marketplace

**Team Agile 11**

## About the Project

Farm Cart is a web-based agricultural marketplace designed to connect farmers directly with consumers. It aims to help farmers sell their produce and make fresh agricultural products easier for consumers to find.

The project focuses on reducing intermediaries, improving order management, and exploring practical solutions for agricultural delivery.

## Project Objectives

- Connect farmers directly with consumers.
- Make agricultural products easier to browse and discover.
- Simplify product and order management.
- Reduce delivery costs through grouped orders.
- Improve inventory management and database reliability.

## Proposed Features

- **Farmer Listings:** Farmers can list their agricultural products, prices, and availability.
- **Product Discovery:** Consumers can browse and search for available produce.
- **User Authentication:** Separate access for farmers and consumers.
- **Order Management:** Manage customer orders and their status.

## Proposed Improvements

### 1. Batch Delivery Model

Delivering small quantities of produce over long distances can be expensive. Farm Cart proposes grouping orders from nearby customers and delivering them to common pickup points on scheduled days.

For example, a farmer could deliver multiple orders to one neighborhood on Saturday morning. This can reduce transportation costs and help manage the delivery of perishable products.

### 2. PostgreSQL Migration

The current project plan mentions SQLite as the database. As the application grows, PostgreSQL is proposed to handle concurrent database operations more reliably.

Using PostgreSQL with SQLAlchemy, along with proper database transactions and inventory checks, can help prevent overselling when multiple customers place orders simultaneously.

## Technology Stack

- **Backend:** Python, Flask
- **API:** REST endpoints
- **Current Planned Database:** SQLite
- **Proposed Database:** PostgreSQL with SQLAlchemy
- **Frontend:** HTML, Jinja2 Templates, Tailwind CSS
- **Data Visualization:** Chart.js
- **Version Control:** Git and GitHub

## Future Scope

- Scheduled deliveries and neighborhood pickup points.
- Inventory tracking and order status updates.
- Improved concurrent order processing.
- Regional agricultural insights and crop recommendations.
- Weather-aware agricultural information.

## Team Members

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

## Project Goal

To develop a reliable farm-to-consumer marketplace that makes agricultural products easier to access while addressing practical challenges such as delivery costs, product freshness, and inventory management.

**Project Status:** Features and database improvements should be updated as they are implemented and tested.
