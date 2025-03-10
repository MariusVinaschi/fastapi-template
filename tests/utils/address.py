from faker import Faker

fake = Faker()


def generate_address_data():
    return {
        "latitude": float(fake.latitude()),
        "longitude": float(fake.longitude()),
        "city": fake.city(),
        "postcode": fake.postcode(),
        "complement": fake.building_number(),
        "road": fake.street_name(),
        "house_number": fake.building_number(),
        "country": fake.country(),
        "country_code": fake.country_code(representation="alpha-2"),
    }
