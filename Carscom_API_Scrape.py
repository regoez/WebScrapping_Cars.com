import csv
from itertools import islice
import requests
import re

# # # # # # # # # # # 
# HELPER FUNCTIONS  #
# # # # # # # # # # # 

# "https://api.cars.com/modellistingaggregate/2.0/rest/compare/?apikey=KHoONWaUgHyNC6pfY57Hul7ISRyhGFgY&criteria=pricing,fuelEconomy,convenience,specifications,overview&vehicle=audi-a5-2019&zip=92712"
def buildCarsUrl(row, year):
    apiKey = "KHoONWaUgHyNC6pfY57Hul7ISRyhGFgY"

    # format in apiKey, Make, Model
    urlBase = "https://api.cars.com/modellistingaggregate/2.0/rest/compare/?apikey=%s&criteria=pricing,fuelEconomy,convenience,specifications,overview&vehicle=%s-%s-%s&zip=92712"

    make = row[2].lower().replace(" ", "_").replace("-", "_")
    model = row[4].lower().replace(" ", "_").replace("-", "_")

    return urlBase % (apiKey, make, model, year)

def parseFuelType(engines):
    fuel = re.findall(r"\((.*?)\)", " ".join(engines))
    return ", ".join(fuel) if fuel else None

def parseCylinder(engines):
    cylinders = re.findall(r"\, (.*?) \(", "".join(engines))
    cylinderVals = []
    for cylinder in cylinders:
        array = cylinder.split("-")
        val = array[2] if len(array) > 2 else None
        cylinderVals.append(int(val))
    return min(cylinderVals) if cylinderVals else None

def parseHorsepower(horsepower):
    hp = " ".join(horsepower).split('@')
    if hp is not None:
        return hp[0]
    return " "

def parseTrasmission(transmissions):
    if "automatic" in transmissions:
        return "automatic"
    elif "manual" in transmissions:
        return "manual"
    else:
        return transmissions


# # # # # # # # 
# MAIN LOGIC  # 
# # # # # # # # 

# Open up a file named 2019_Sales_Makes_Series_Models.csv to read
with open('2019_Sales_Makes_Series_Models.csv') as csvfile:
    readCSV = csv.reader(csvfile, delimiter=',')

    cars = []
    firstline = True 
    for index, row in enumerate(readCSV):
        if firstline:
            # Skip first line since it's the header
            firstline = False
            continue

        # col 1 = Year (usually 2019), col 2 = Make, 3 = Series, 4 = Model
        currYear = row[1]
        make = row[2]
        model = row[4]
        print("Car #%d" % index)
        print("API URL: %s" % buildCarsUrl(row, currYear))

        otherYearsToTry = [2020, 2018, 2017, 2016, 2014, 2012]

        try:
            r = requests.get(buildCarsUrl(row, currYear), timeout = 5)
            data = r.json()
            status = data['status']

            # if API request results in error, try with other years for the model
            if status != "SUCCESS":
                for year in otherYearsToTry:
                    currYear = str(year)
                    r = requests.get(buildCarsUrl(row, currYear), timeout = 5)
                    data = r.json()
                    if data['status'] == "SUCCESS":
                        break
        except:
            print("Request Timed out for Car: %s %s" % (make, model))
            continue

        vehicle = data['vehicle']
        overview = vehicle['overview'] # msrp, mpgCombined, engines, transmissions, drivetrain, seats, 
        engines = overview['engines']
        specifications = vehicle['specifications'] # horsepower, length, wheelbase, width, height, curbWeight, passengerVolume
        fuelEconomy = vehicle['fuelEconomy'] # highway, city

        if specifications is None:
            specifications = {
                'horsepower': [],
                'length': "Missing",
                'wheelbase': "Missing",
                'width': "Missing",
                'height': "Missing",
                'curbWeight': [],
                'passengerVolume': "Missing"
            }

        if engines is None:
            engines = []

        fuel = parseFuelType(engines)
        cylinder = parseCylinder(engines)
        horsepower = parseHorsepower(specifications['horsepower'])

        drivetrain = overview['drivetrain']
        if drivetrain is None:
            drivetrain = "Missing"

        seats = overview['seats']
        if seats is None:
            seats = "Missing"

        # Create a dictionary with the scraped data for a car model. 
        currCar = {
            "Year": currYear,
            "Make": row[2],
            "Series": row[3],
            "Model": row[4],
            "MSRP": overview['msrp'], 
            "MPG": overview['mpgCombined'], 
            "Horsepower": horsepower, 
            "Cylinder": cylinder, 
            "Fuel": fuel,
            "Transmissions": parseTrasmission(" ".join(overview['transmissions'])), 
            "Drivetrain": drivetrain, 
            "Seats": seats, 
            "HighwayMPG": fuelEconomy['highway'], 
            "CityMPG": fuelEconomy['city'], 
            "Length": specifications.get('length'), 
            "Wheelbase": specifications.get('wheelbase'), 
            "Width": specifications.get('width'), 
            "Height": specifications.get('height'), 
            "curbWeight": " ".join(specifications.get('curbWeight')), 
            "passengerVolume": specifications.get('passengerVolume')
        }

        print("Appending car: ")
        print(currCar)
        print("\n")
        cars.append(currCar)

    print("List of Car Dictinaries: ")
    print(cars)

# Create and open a new file called Filled_Cars.csv, to populate the scraped data. 
with open('Filled_Cars.csv', 'w') as writeFile: 
    fieldNames = [
        "Year",
        "Make",
        "Series",
        "Model",
        "MSRP", 
        "MPG", 
        "Horsepower", 
        "Cylinder", 
        "Fuel",
        "Transmissions", 
        "Drivetrain", 
        "Seats", 
        "HighwayMPG", 
        "CityMPG", 
        "Length",
        "Wheelbase", 
        "Width", 
        "Height", 
        "curbWeight", 
        "passengerVolume"
    ]
    writer = csv.DictWriter(writeFile, fieldnames=fieldNames)
    writer.writeheader()

    print("ABOUT TO WRITE CARS")
    print(cars)

    writer.writerows(cars)

print("WRITE COMPLETE")    
