"""Generate CSVs of random data for ShareBnb

Only only need to run this if you wanted to
tweak the CSV formats or generate fewer/more rows.
"""

import csv
from random import choice, randint, sample, uniform
from itertools import permutations
import requests
from faker import Faker


USERS_CSV_HEADERS = ['email', 'username', 'image_url', 'password',
                     'first_name', 'last_name', 'bio', 'location']
LISTINGS_CSV_HEADERS = ['title', 'description', 'photo', 'price',
                        'latitude', 'longitude', 'beds', 'rooms',
                        'bathrooms', 'created_by']                        
MESSAGES_CSV_HEADERS = ['body', 'to_user', 'from_user']
# FOLLOWS_CSV_HEADERS = ['user_being_followed_id', 'user_following_id']

NUM_USERS = 100
NUM_LISTINGS = 50
NUM_MESSAGES = 500

fake = Faker()

# Generate random profile image URLs to use for users

image_urls = [
    f"https://randomuser.me/api/portraits/{kind}/{i}.jpg"
    for kind, count in [("lego", 10), ("men", 100), ("women", 100)]
    for i in range(count)
]

# Generate random header image URLs to use for users

location_image_urls = [
    requests.get(f"http://www.splashbase.co/api/v1/images/{i}").json()['url']
    for i in range(1, 46)
]

# a random number of beds, rooms, and bathrooms to use for listings
total_in_home = [1, 2, 3, 4, 5, 6]

# generate a range of fake users
# password hash is for "password"
# also keeping tracking of all usernames added to randomly pick them for
# created_by field in listings

all_usernames = []
with open('generator/users.csv', 'w') as users_csv:
    users_writer = csv.DictWriter(users_csv, fieldnames=USERS_CSV_HEADERS)
    users_writer.writeheader()
    
    for i in range(NUM_USERS):
        new_username = fake.user_name()
        all_usernames.append(new_username)

        users_writer.writerow(dict(
            email=fake.email(),
            username=new_username,
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            image_url=choice(image_urls),
            password='$2b$12$Q1PUFjhN/AWRQ21LbGYvjeLpZZB6lfZ1BPwifHALGO6oIbyC3CmJe',
            bio=fake.sentence(),
            location=fake.city()
        ))

# generate a range of fake listings
with open('generator/listings.csv', 'w') as listings_csv:
    listings_writer = csv.DictWriter(listings_csv, fieldnames=LISTINGS_CSV_HEADERS)
    listings_writer.writeheader()

    for i in range(NUM_LISTINGS):
        location_tuple = fake.location_on_land()
        listings_writer.writerow(dict(
            title=fake.sentence(),
            description=fake.paragraph(),
            photo=choice(location_image_urls),
            price=round(uniform(150, 2000), 2),
            latitude=location_tuple[0],
            longitude=location_tuple[1],
            beds=choice(total_in_home),
            rooms=choice(total_in_home),
            bathrooms=choice(total_in_home),
            created_by=choice(all_usernames)
        ))

"""  
May need to generate messages later with a to and from_user
Strategy: Get pairs of usernames, then use DictWriter to write in rows where from_username
and to_username are sourced from the pair 
""" 

# with open('generator/messages.csv', 'w') as messages_csv:
#     all_pairs = list(permutations(all_usernames, 2))
#     messages_writer = csv.DictWriter(messages_csv, fieldnames=MESSAGES_CSV_HEADERS)
#     messages_writer.writeheader()

#     for from_username, to_username in sample(all_pairs, NUM_MESSAGES):
#         messages_writer.writerow(dict(
#             body=fake.sentence(),
#             from_user=from_username,
#             to_user=to_username
#         ))