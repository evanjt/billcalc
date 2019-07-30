#!/usr/bin/env python3

''' Written to log the in/out dates of tenants and split
    house
    bills appropriately according to their time at the
    house. The program does no management of bills, just stores
    their information for recalculation purposes in a JSON file

    Author:     Evan Thomas
    Contact:    evan {ą} evanjt ! com
'''

import os
import datetime
import uuid
import argparse
import sys
import json
from distutils import util
from shutil import copyfile

PROGRAM_JSON = os.path.join(os.getcwd(), 'billcalc.json')
BACKUP_JSON = os.path.join(os.getcwd(), 'billcalc.json_bak')
SUGGESTED_BILL_CATEGORIES = ['electricity', 'gas', 'water', 'internet']

# Set up some classes - Bills/Property/Tenants
class Bill:
    def __init__(self, category, amount, from_date, to_date, property_object, unique_id=None):
        self.category = category
        self.amount = amount
        self.from_date = from_date
        self.to_date = to_date
        self.per_day = self.amount / self.total_days()
        self.num_people_in_house = property_object.tenant_count
        if category.lower() not in property_object.bill_types.keys():
            raise Exception("ERROR: " + self.category.capitalize() + "'s provider name has not been set. Please reset house configuration.")
        self.supplier = property_object.bill_types[category.lower()]
        if unique_id == None:
            self.unique_id = uuid.uuid4() # Generate unique ID for referencing bill
        else:
            self.unique_id = unique_id

    # Custom equality rule to help prevent adding bill twice
    def __eq__(self, other):
        return self.amount == other.amount \
            and self.from_date == other.from_date \
            and self.to_date == other.to_date \
            and self.category == other.category

    def get_from_date(self):
        return self.from_date

    def get_to_date(self):
        return self.to_date

    def total_days(self):
        return (self.to_date - self.from_date).days

    # To assist with outputting to CSV. Follows CSV header found in check_files()s
    def raw_output(self):
        return self.category, self.amount,\
            self.from_date.year,\
            self.from_date.month,\
            self.from_date.day,\
            self.to_date.year,\
            self.to_date.month,\
            self.to_date.day,\
            self.supplier

    def to_json(self):
        raw_json = {"category": self.category,
                    "amount": self.amount,
                    "from_date": {
                        "year": self.from_date.year,
                        "month": self.from_date.month,
                        "day": self.from_date.day
                    },
                    "to_date": {
                        "year": self.to_date.year,
                        "month": self.to_date.month,
                        "day": self.to_date.day
                    },
                    "supplier": self.supplier
                    }
        return str(self.unique_id), raw_json

    def summary(self):
        print('{} -> {} ({} days) ${} {} ({})'.format(self.get_from_date(), self.get_to_date(), self.total_days(), self.amount, self.category, self.supplier))

class Property:
    def __init__(self, name, tenant_count, bill_types=None):
        self.name = name
        self.tenant_count = int(tenant_count)

        if bill_types == None:
            print("No bill types!")
            bill_types = {}
            #self.add_bill()
        else:
            self.bill_types = bill_types

    def add_bill(self):
        list_bills()
        bill_type = input("Enter bill type (gas, electricity, etc): ")
        current_provider = input("Who is the provider?: ")
        self.bill[bill_type.lower()] = current_provider.lower()

    def list_bills(self):
        print("Current bills for", self.name + ":")
        for key, value in self.bill.items():
            print(key.capitalize() + ' (' + value.capitalize() + ')')

    def to_json(self):
        raw_json = {"name": self.name,
                    "tenant_count": self.tenant_count,
                    "bill_types": self.bill_types
                    }
        return raw_json

    def summary(self):
        print('Name: {} \nTenant count: {}\n\nBill types:'.format(self.name.capitalize(), self.tenant_count))
        for bill_type, bill_provider in self.bill_types.items():
            print('Type: {:15} Provider: {}'.format(bill_type.capitalize(),
                                                    bill_provider.capitalize()))

class Tenant:
    def __init__(self, name, entered_house, still_at_address, left_house=None, unique_id=None):
        self.name = name
        self.entered_house = entered_house
        self.still_at_address = bool(still_at_address) # Force boolean
        if unique_id == None:
            self.unique_id = uuid.uuid4() # Generate unique ID for referencing tenant
        else:
            self.unique_id = unique_id
        if left_house == None:
            self.left_house = datetime.date.today()
        else:
            self.left_house = left_house

    def get_from_date(self):
        return self.entered_house

    # Call this function to return today's date if someone is still living there
    def get_to_date(self):
        if self.still_at_address:
            return datetime.date.today()
        else:
            return self.left_house

    # Calculate how much a tenant owes by taking a bill object
    def owes(self, input_bill):
        if self.get_from_date() <= input_bill.get_from_date():
            tenant_pays_from = input_bill.get_from_date()
        elif self.get_from_date() > input_bill.get_from_date():
            tenant_pays_from = self.get_from_date()

        if self.get_to_date() >= input_bill.get_to_date():
            tenant_pays_to = input_bill.get_to_date()
        elif self.get_from_date() < input_bill.get_from_date():
            tenant_pays_to = self.get_to_date()
        elif input_bill.get_to_date() > datetime.date.today():
            sys.exit("Bill end date is later than today's date")

        days_owing = (tenant_pays_to - tenant_pays_from).days
        if days_owing > 0:
            return self.name, days_owing, round(((days_owing / input_bill.total_days()) * (input_bill.amount / input_bill.num_people_in_house)),2)
        else:
            return None

    # This function helps output the data to a CSV
    def raw_output(self):
        return self.name, self.entered_house.year,\
            self.entered_house.month,\
            self.entered_house.day,\
            self.still_at_address,\
            self.left_house.year,\
            self.left_house.month,\
            self.left_house.day

    def to_json(self):
        raw_json = {"name": self.name,
                    "entered_house": {
                        "year": self.entered_house.year,
                        "month": self.entered_house.month,
                        "day": self.entered_house.day
                    },
                    "left_house": {
                        "year": self.left_house.year,
                        "month": self.left_house.month,
                        "day": self.left_house.day
                    },
                    "still_at_address": self.still_at_address
                    }
        return str(self.unique_id), raw_json

    # Summary of the individual tenant
    def summary(self):
        print('{:10} \t {} -> {} ({} days)'.format(self.name, self.get_from_date(), self.get_to_date(), str((self.get_to_date() - self.get_from_date()).days)))

# A helper function to return the object by giving a UUID4
def search_id(in_id, object_list):
    for x in object_list:
        if x.unique_id == in_id:
            return x

def add_new_tenant():
    name = input("Name of tenant: ")
    print("\nEnter date of when tenant started living at the house")
    print("NOTE: If tenants are changing, the end date and the start date must be the same")
    year_in = input("Year entered house: ")
    month_in = input("Month entered house: ")
    day_in = input("Day entered house: ")

    print("\nEnter date of when tenant left the house")
    print("**Leave blank and press enter if they have not left yet")
    year_out = input("Year left house: ")
    if len(year_out) == 0:
        still_at_address = True
    else:
        month_out = input("Month left house: ")
        day_out = input("Day left house: ")
        still_at_address = False

    if still_at_address == True:
        return Tenant(name, datetime.date(int(year_in), int(month_in), int(day_in)), True)
    else:
        return Tenant(name, datetime.date(int(year_in), int(month_in), int(day_in)), False, datetime.date(int(year_out), int(month_out), int(day_out)))

def ask_to_add_tenant(TENANT_FILENAME, tenant_list):
    list_tenants(tenant_list)
    add_tenant = True
    has_added_tenant = False
    while add_tenant:
        answer = input("Do you wish to add another tenant? yes/no: ")
        if answer == "yes":
            add_tenant = True
            tenant_list.append(add_new_tenant())
            has_added_tenant = True # Has added one, reprint list
        else:
            add_tenant = False
            save_tenants(TENANT_FILENAME, tenant_list)
            if has_added_tenant:
                print("\nUpdated tenant list:")
                list_tenants(tenant_list)
    return tenant_list

def list_tenants(tenant_list):
    for idx, tenant in enumerate(tenant_list):
        print('[{:2}]'.format(idx), end=' ')
        tenant.summary()

def add_bill(property_conf, bill_detail_list, bill_list):
    amount = float(bill_detail_list[0])
    start_date_list = bill_detail_list[1].split(".")
    end_date_list = bill_detail_list[2].split(".")
    start_date = datetime.date(int(start_date_list[0]),
                               int(start_date_list[1]),
                               int(start_date_list[2]))
    end_date = datetime.date(int(end_date_list[0]),
                             int(end_date_list[1]),
                             int(end_date_list[2]))
    bill_type = bill_detail_list[3]

    bill = Bill(bill_type, float(amount), start_date, end_date, property_conf)

    for other_bill in bill_list:
        if other_bill == bill:
            print("Bill already exists")
            return bill_list

    # If bill hasn't been added before, add to list and return
    bill_list.append(bill)
    return bill_list

# Check each tenant if they apply to a bill, and if so, print out name, days and amount
def who_owes_what(bill, tenants):
    total_check = 0
    list_of_payees = []
    for tenant in tenants:
        tenant_data = tenant.owes(bill)
        if tenant_data is not None:
            print("{:10}${:>6.2f} ({} days)".format(tenant_data[0], tenant_data[2], tenant_data[1]))
            total_check += tenant_data[2]
            list_of_payees.append(tenant_data)
    difference = total_check - bill.amount
    print()
    print("{} bill, {} total sum [{:+} difference]".format(bill.amount, total_check, difference))
    return list_of_payees

def list_categories(allowed_categories):
    for category in allowed_categories:
        print(category, end='')
        if category != allowed_categories[-1]:
            print('/', end='')

def start_from_nothing():
    tenant_list = []
    property_conf = {}
    print("Add details... Only a placeholder for the moment")

    return tenant_list, property_conf

# Save all data to a JSON file stored locally
def save_json(tenant_list, property_conf, bill_list, filename):
    property_data = property_conf.to_json()

    bill_data = []
    for bill in bill_list:
        unique_id, bill_json = bill.to_json()
        bill_data.append({unique_id: bill_json})

    tenant_data = []
    for tenant in tenant_list:
        tenant_id, tenant_json = tenant.to_json()
        tenant_data.append({tenant_id: tenant_json})

    out_json = {"property": property_data,
                "tenants": tenant_data,
                "bills": bill_data}

    with open(filename, "w") as json_file:
        json.dump(out_json, json_file, indent=4)

# Loads the JSON into a list of tenants, a list of bills, and property information
def load_json(filename, new_property_conf=None):
    # Read JSON
    if os.path.exists(filename):
        print("Loading stored data... ", end='')
    else:
        print(filename, "not found")
        start_from_nothing()
    with open(filename, "r") as json_file:
        json_data = json.load(json_file)

    # Allow for new property information to override JSON if argument provided
    if new_property_conf is not None:
        property_conf = new_property_conf
    else:
        # Add property information
        try:
            property_data = json_data['property']
            bill_types = {}
            for key, value in property_data['bill_types'].items():
                bill_types[key] = value
            property_conf = Property(property_data['name'],
                                    property_data['tenant_count'],
                                    bill_types)
        except Exception:
            pass
            print("\n\nCurrent property information:")
            property_object.summary()
            property_conf = set_property_values(property_conf)

    # Add all tenants
    tenant_data = json_data['tenants']
    tenant_list = []
    for tenant in tenant_data:
        for keys, values in tenant.items():
            # Seperates values from JSON into variables -- cleaner
            unique_id = keys
            name = values['name']
            iny = int(values['entered_house']['year'])
            inm = int(values['entered_house']['month'])
            ind = int(values['entered_house']['day'])
            outy = int(values['left_house']['year'])
            outm = int(values['left_house']['month'])
            outd = int(values['left_house']['day'])
            still_at_address = values['still_at_address']
            in_house = datetime.date(iny, inm, ind)
            out_house = datetime.date(outy, outm, outd)
            # Add tenant from JSON data
            tenant_list.append(Tenant(name, in_house, still_at_address, out_house, unique_id))

    # Load bills
    bill_list = []
    bill_data = json_data['bills']
    for bill in bill_data:
            for keys, values in bill.items():
                unique_id = keys
                cat = str(values['category'])
                amount = float(values['amount'])
                fromy = int(values['from_date']['year'])
                fromm = int(values['from_date']['month'])
                fromd = int(values['from_date']['day'])
                toy = int(values['to_date']['year'])
                tom = int(values['to_date']['month'])
                tod = int(values['to_date']['day'])
                supplier = str(values['supplier'])
                from_date = datetime.date(fromy, fromm, fromd)
                to_date = datetime.date(toy, tom, tod)
                bill_list.append(Bill(cat, amount, from_date, to_date, property_conf, unique_id))

    print("Found", len(bill_list), "bills and", len(tenant_list), "tenants at", property_conf.name)
    print()

    return tenant_list, property_conf, bill_list

def set_property_values():
    name = input("Enter property name: ")
    tenant_count = input("Enter number of tenants: ")
    keep_asking = True
    bill_types = {}
    while keep_asking:
        print("Enter bill category", "(options are " + "/".join(SUGGESTED_BILL_CATEGORIES) + ")")
        print("Press Enter to escape")
        bill_type = input(": ")
        if len(bill_type) == 0:
            keep_asking = False
            break
        print("Enter bill provider")
        bill_provider = input(": ")
        bill_types[bill_type.lower()] = bill_provider.lower()
    new_property = Property(name, tenant_count, bill_types)
    return new_property

def list_bills(bill_list):
    for idx, bill in enumerate(bill_list):
        print('[{:3}]'.format(idx), end=' ')
        bill.summary()

def main():
    # Argparse content
    parser = argparse.ArgumentParser()
    arg_bills = parser.add_argument_group("Bills")
    arg_bills.add_argument("-b", nargs=4, metavar=('AMOUNT', 'DATEFROM', 'DATEUNTIL', 'CATEGORY'),
                        help="Add bill. Dates should be yyyy.mm.dd. Category electricity, gas, etc")
    arg_bills.add_argument("-lb", "--list-bills", help="Lists all bills", action="store_true")
    arg_bills.add_argument("-rc", "--recalculate", help="Recalculate bill for tenants. Use with -lb", action="store_true")
    arg_bills.add_argument("-db", "--delete-bill", help="Delete bill", action="store_true")

    arg_tenants = parser.add_argument_group("Tenants")
    arg_tenants.add_argument("-lt", "--list-tenants", help="Lists current tenants", action="store_true")
    arg_tenants.add_argument("-dt", "--delete-tenant", help="Delete tenant", action="store_true")

    arg_property = parser.add_argument_group("Property settings")
    arg_property.add_argument("-p", "--property-set", help="Set property values", action="store_true")
    arg_property.add_argument("-lp", "--list-property", help="List current property values", action="store_true")

    args = parser.parse_args()

    # If the user is setting new property values, send them to load_json, which will send them
    # straight back, rather than using the values stored in the JSON
    if args.property_set:
        new_property_conf = set_property_values()
        tenant_list, property_conf, bill_list = load_json(PROGRAM_JSON, new_property_conf)
    else:
        # Load stored data
        tenant_list, property_conf, bill_list = load_json(PROGRAM_JSON)

    # Create backup of user data
    copyfile(PROGRAM_JSON, BACKUP_JSON)

    try:
        if args.list_bills:
            list_bills(bill_list)

        if args.recalculate:
            list_bills(bill_list)
            print()
            bill_number = input("Recalculate for which bill #: ")
            who_owes_what(bill_list[int(bill_number)], tenant_list)

        if args.delete_bill:
            list_bills(bill_list)
            print()
            print("WARNING!! This cannot be undone")
            bill_number = input("Delete which bill #: ")
            bill_list.pop(int(bill_number))
            print()
            list_bills(bill_list)

        if args.delete_tenant:
            list_tenants(tenant_list)
            print()
            print("WARNING!! This cannot be undone")
            tenant_number = input("Delete which tenant #: ")
            tenant_list.pop(int(tenant_number))
            print()
            list_tenants(tenant_list)

        if args.list_tenants:
            list_tenants(tenant_list)
            save_json(tenant_list, property_conf, bill_list, PROGRAM_JSON)

        if args.b is not None:
            new_bill = add_bill(property_conf, args.b, bill_list)
            print()
            who_owes_what(new_bill[-1], tenant_list) # List how much is owing

        if args.list_property:
            property_conf.summary()

        # Print help if no arguments passed
        if len(sys.argv[1:]) == 0:
            parser.print_help()

        # If error saving, copy back the backup and exit, otherwise remove backup
        save_json(tenant_list, property_conf, bill_list, PROGRAM_JSON)
    except:
        copyfile(BACKUP_JSON, PROGRAM_JSON)
        sys.exit("Error saving file. Changes not saved")

    # Remove backup file
    os.remove(BACKUP_JSON)

if __name__ == "__main__":
    main()
