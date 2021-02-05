"""Generate CSVs of random data for ShareBnb

Only only need to run this if you wanted to
tweak the CSV formats or generate fewer/more rows.
"""

import csv
from random import choice, sample, uniform
from itertools import permutations
import requests
from faker import Faker
from helpers import get_random_datetime

USERS_CSV_HEADERS = [
    'username',
    'bio',
    'first_name',
    'last_name',
    'email',
    'password',
    'image_url',
    'location'
    ]
LISTINGS_CSV_HEADERS = [
    'title',
    'description',
    'photo',
    'price',
    'longitude',
    'latitude',
    'beds',
    'rooms',
    'bathrooms',
    'created_by'
    ]
MESSAGES_CSV_HEADERS = [
    'body',
    'sent_at',
    'to_user',
    'from_user',
    'listing_id'
    ]

NUM_USERS = 100
NUM_LISTINGS = 100
NUM_MESSAGES = 100

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
            password=(
                '$2b$12$Q1PUFjhN/AWRQ21LbGYvjeLpZZB6lfZ1BPwifHALGO6oIbyC3CmJe'
            ),
            bio=fake.sentence(),
            location=fake.city()
        ))

listing_owners = []
# generate a range of fake listings
with open('generator/listings.csv', 'w') as listings_csv:
    listings_writer = csv.DictWriter(
        listings_csv,
        fieldnames=LISTINGS_CSV_HEADERS
        )
    listings_writer.writeheader()

    for i in range(1, NUM_LISTINGS + 1):
        created_by = choice(all_usernames)
        listing_owners.append({"owner": created_by, "listing_id": i})

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
            created_by=created_by
        ))

# # generate a range of fake messages
# with open('generator/messages.csv', 'w') as messages_csv:
#     # get pairs of usernames, then use DictWriter to write in rows where
#     # from_username and to_username are sourced from the pair with randomly
#     # generated timestamp for sent_at
#     all_pairs = list(permutations(all_usernames, 2))
#     messages_writer = csv.DictWriter(
#         messages_csv,
#         fieldnames=MESSAGES_CSV_HEADERS,
#         )
#     messages_writer.writeheader()

#     for from_username, to_username in sample(all_pairs, NUM_MESSAGES):
#         messages_writer.writerow(dict(
#             body=fake.sentence(),
#             sent_at=get_random_datetime(),
#             to_user=to_username,
#             from_user=from_username,
#             # listing_id=choice(1...NUM_LISTINGS)
#         ))


# generate a range of fake messages
with open('generator/messages.csv', 'w') as messages_csv:
    # get a list of random users from all_usernames
    # randomly pick from this list of users and in a while loop,
    # if the user is IN the owner_list AND not self, then we create the pair
    random_senders = sample(all_usernames, NUM_MESSAGES)
    random_owners = sample(listing_owners, NUM_MESSAGES)

    eligible_pairs = []
    for idx in range(len(random_senders)):
        sender = random_senders[idx]
        owner_dict = random_owners[idx]  # { owner, listing_id }
        if sender != owner_dict["owner"]:
            eligible_pairs.append((sender, owner_dict))

    messages_writer = csv.DictWriter(
        messages_csv,
        fieldnames=MESSAGES_CSV_HEADERS,
        )
    messages_writer.writeheader()

    for from_username, to_user_dict in sample(eligible_pairs, 50):
        messages_writer.writerow(dict(
            body=fake.sentence(),
            sent_at=get_random_datetime(),
            to_user=to_user_dict["owner"],
            from_user=from_username,
            listing_id=to_user_dict["listing_id"]
        ))