#!/usr/bin/env python
# coding: utf-8
import csv
import os
import datetime
import uuid

TENANT_FILENAME = os.path.join(os.getcwd(), 'tenants.csv')

class Bill:
    def __init__(self, provider, amount, from_date, to_date, num_people_in_house):
        self.provider = provider
        self.amount = amount
        self.from_date = from_date
        self.to_date = to_date
        self.per_day = self.amount / self.total_days()
        self.num_people_in_house = num_people_in_house

    def get_from_date(self):
        return self.from_date

    def get_to_date(self):
        return self.to_date

    def total_days(self):
        return (self.to_date - self.from_date).days

class Property:
    def __init__(self, name, tenant_count, bill_types=None): # Bill types as a list of tuples
        self.name = name
        self.tenant_count = tenant_count
        self.bill = {}

        if bill_types == None:
            self.add_bill()
        else:
            for bill_type in bill_types:
                self.bill[bill_type[0]] = bill_type[1] # Set type and current provider

    def add_bill(self):
        list_bills()
        bill_type = input("Enter bill type (gas, electricity, etc): ")
        current_provider = input("Who is the provider?: ")
        self.bill[bill_type.lower()] = current_provider.lower()

    def list_bills(self):
        print("Current bills for", self.name + ":")
        for key, value in self.bill.items():
            print(key.capitalize() + ' (' + value.capitalize() + ')')

class Person:
    def __init__(self, name, entered_house, still_at_address, left_house=None):
        self.name = name
        self.entered_house = entered_house
        self.still_at_address = still_at_address
        self.id = uuid.uuid4() # Generate unique ID for referencing tenant
        if left_house == None:
            self.left_house = datetime.date.today()
        else:
            self.left_house = left_house

    def get_from_date(self):
        return self.entered_house

    # Call this function to return today's date if someone is still living there
    def get_to_date(self):
        if self.still_at_address == True:
            return datetime.date.today()
        else:
            return self.left_house

    def owes(self, input_bill):
        if self.get_from_date() <= input_bill.get_from_date():
            tenant_pays_from = input_bill.get_from_date()
        elif self.get_from_date() > input_bill.get_from_date():
            tenant_pays_from = self.get_from_date()

        if self.get_to_date() >= input_bill.get_to_date():
            tenant_pays_to = input_bill.get_to_date()
        elif self.get_from_date() < input_bill.get_from_date():
            tenant_pays_to = self.get_to_date()

        days_owing = (tenant_pays_to - tenant_pays_from).days
        if days_owing > 0:
            return self.name, days_owing, round(((days_owing / input_bill.total_days()) * (input_bill.amount / input_bill.num_people_in_house)),2)
        else:
            return None

    def raw_output(self):
        return self.name, self.entered_house.year,                 self.entered_house.month,                 self.entered_house.day,                 self.still_at_address,                 self.left_house.year,                 self.left_house.month,                 self.left_house.day

    def summary(self):
        print('{:10} \t {} -> {} ({} days)'.format(self.name, self.get_from_date(), self.get_to_date(), str((self.get_to_date() - self.get_from_date()).days)))

# Keep a file with the list of tenants
def save_tenants(filename, tenant_list):
    with open(filename, 'w', newline='') as csvfile:
        csv_header = ['name', 'year_in', 'month_in', 'day_in', 'still_at_address', 'year_out', 'month_out', 'day_out']
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow(csv_header)
        for tenant in tenant_list:
            writer.writerow(tenant.raw_output())
    print("Saved tenant list to", filename)

# Reads the file of saved tenant information
def read_tenants(filename):
    tenant_list = []
    with open(filename, newline='') as csvfile:
        reader = csv.reader(csvfile)
        next(reader, None) # Skip header
        for row in reader:
            tenant_list.append(Person(row[0], # Name
                                      datetime.date(int(row[1]), int(row[2]), int(row[3])), # In house
                                      row[4], # Still at address boolean
                                      datetime.date(int(row[5]), int(row[6]), int(row[7])))) # Out house
            #print(csvfile.line_num)
    print("Imported", len(tenant_list), "tenants")
    return tenant_list

def read_property(filename):
    property

def add_new_tenant():
    name = input("Name of person: ")
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
        return Person(name, datetime.date(int(year_in), int(month_in), int(day_in)), True)
    else:
        return Person(name, datetime.date(int(year_in), int(month_in), int(day_in)), False, datetime.date(int(year_out), int(month_out), int(day_out)))

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
    for tenant in tenant_list:
        tenant.summary()

def load_tenants(filename):
    if os.path.exists(filename):
        tenant_list = read_tenants(filename)
        tenant_list = ask_to_add_tenant(filename, tenant_list)
    else:
        print("Please add a tenant")
        add_tenant = True
        tenant_list = []
        tenant_list.append(add_tenant())
        tenant_list = ask_to_add_tenant(filename, tenant_list)
    return tenant_list


def load_property_conf(filename):
    if os.path.exists(filename):
        propert_conf = read()

def add_bill(property_object):
    name = input("Bill type: ")
    amount = input("Total amount to pay: ")
    start_date = input("Enter start date (yyyy mm dd): ")
    end_date = input("Enter end date (yyyy mm dd): ")
    start_year, start_month, start_day = start_date.split(" ")
    end_year, end_month, end_day = end_date.split(" ")

    return Bill(name, float(amount), datetime.date(int(start_year), int(start_month), int(start_day)), datetime.date(int(end_year), int(end_month), int(end_day)), int(property_object.tenant_count))

def who_owes_what(bill, tenants):
    total_check = 0
    for tenant in tenants:
        tenant_data = tenant.owes(bill)
        if tenant_data is not None:
            print("{:10}${:>6.2f} ({} days)".format(tenant_data[0], tenant_data[2], tenant_data[1]))
            total_check += tenant_data[2]
    difference = total_check - bill.amount
    print()
    print("{} bill, {} total sum [{:+} difference]".format(bill.amount, total_check, difference))


def main():
    print("Welcome to the bill calculator!")
    tenant_list = load_tenants(TENANT_FILENAME)
    print()
    # Set property details, bills are a dummy at the moment, most important is 4 (number of tenants)
    postoffice = Property('post office', 4, [('gas', 'origin'), ('water', 'yarra valley water')])
    postoffice.list_bills()
    new_bill = add_bill(postoffice)
    print()
    who_owes_what(new_bill, tenant_list) # List how much is owing

if __name__ == "__main__":
    main()
