from deta import Deta

DETA_KEY = "c0m2o6xwrkg_nsZoik8xjnPoEtfdGMbBxM8vEJfDdCbL"

# initialize with a project key
deta = Deta(DETA_KEY)

# This is how to create / connect to a database
db = deta.Base("licensePlateNumber")

def insert_lpn(licence_plate_number, current_time):
    # returns the report on a successful creation, otherwise raises an error
    return db.put({"key": licence_plate_number, "time": current_time})

def fetch_all_lpn():
    # returns a dict of all periods
    res = db.fetch()
    return res.items

def get_lpn(license_plate_number):
    # if not found, the function will return none
    return db.get(license_plate_number)

def del_lpn(license_plate_number):
    return db.delete(license_plate_number)
