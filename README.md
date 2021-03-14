# ShareBnB 

A web application for people to share and rent out their private and public spaces with others. Users create listings that include photos, location, price, # of beds, # of rooms, etc. and are able to search for created listings by price, location, # of beds, and # of bathrooms, etc. Users book listings and message other users regarding a listgin, directly on the platform.  

Check out the deployed app <a href="">here</a>.

Note: the following documentation focuses on the backend. For frontend related documentation and commentary, please go <a href="">here</a> 

## Motivation

As we move towards a world where people share more and more things, it’s time we build an application where users can share indoor and outdoor spaces like backyards or pools!

## Screenshots
TBU with application screenshots

**Database**

<img src="/static/images/database-er-diagram.png" width="750" height="250">

- Key relationships:

## Build status
- Proof of concept achieved
- WIP on minimum viable product

## Current features
- General app functions:
    - Authenticated users are able to create a listing with photos, price, and other details of the listing
    - Authenticated users are able to search listings by max_price, latitude, longitude, # of beds and # of bathrooms
    - Photos when uploaded are stored in Amazon S3, not in a database
- Backend:
    - AWS S3 cloud storage created and connected
    - database for users, listings, and messages
    - seed database using faker for development
    - SQL queries for specific user, all listings, specific listing, and messages between users and by listings
    - CRUD endpoints for users, listings, and messages
- Frontend: 
    - Homepage / signup / login / listings / logout
    - Forms functioning including uploading images with preview
    - Basic presentational components for listings

## Upcoming features
- Backend:
    - auth for admin
    - auth for same user as logged in, restrict access if false
    - queries for messages by listing
    - websockets for more real-time like messaging
- Frontend:
    - User profile with listings created and booked 
    - Messaging page linked to listings with booking capabilities
    - Interface with a map that updates with listings when moved
    - Pagination for showing listings

## Tech stack
- AWS S3 cloud storage
- PostgreSQL for database
- SQLAlchemy for database ORM
- Flask/Python for backend
- Create-React-App/React for frontend

## Installing
**Backend dependencies** include:
- awscli
- bcrypt
- boto3
- botocore
- cors
- faker
- flask-debugtoolbar
- flask-jwt-extended
- flask-sqlalchemy
- flask-WTForms
- psycopg2-binary

Install dependencies using requirements.txt from /sharebnb-backend 


**Frontend dependencies** include:
- axios for requests
- bootstrap for styling
- jest *(ships with CRA)*
- jsonwebtoken for security
- react-router-dom for routing

Install dependencies using package.json from /sharebnb-frontend/src 

TBU with a step by step of how to get a development env running
TBU include example of being able to get data out of the system or little demo

## Testing
TBU with explanation on how to run the automated tests for the system 

## Deploying
TBU with notes about how to deploy this on a live system

## Authors
- Winnie Chou
- Alan Tseng (pair programming partner)
