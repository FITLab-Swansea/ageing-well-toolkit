import os
import csv

bookmark = 0
clicker = 1
pir = 2
pv = 3

cooking = 0
chores = 1
hobbies = 2



sensors = [
	[clicker, 18, "Plate Cupboard", cooking],
	[clicker, 22, "Utensil Draw", cooking],
	[clicker, 21, "Pan Cupboard", cooking],
	[pir, 6, "Kitchen", cooking],
	[clicker, 0, "Washing Machine", chores],
	[clicker, 17, "Cleaning Cupboard", chores],
	[clicker, 20, "Iron Cupboard", chores],
	[pir, 6, "Kitchen", chores],
	[clicker, 15, "Bin Cupboard", chores],
	[pv, 5, "Toybox", hobbies],
	[bookmark, 3, "Reading", hobbies],
	[pv, 0, "Hobbybox", hobbies],
	[pv, 1, "TV", hobbies]
]



def processData(filename):
	
	type = 0
	ID = 1
	
	location = 2
	date = 2
	time = 3
	context = 3
	
	
	if os.path.isfile(filename):
		with open(filename) as f:
			reader_obj = csv.reader(f)
		
			temp = []
			
			for row in reader_obj:
				temp2 = ""
				for sensor in sensors:
					
					if int(row[type]) == sensor[type] and int(row[ID]) == sensor[ID]:
						str = f"{row[date]}, {row[time]}, {sensor[location]}"
						if temp2 != str:
							temp2 = str
							tempData = [row[date], row[time], sensor[location]]
							print(temp2)
							temp.append(tempData)
			
			f.close()
			
#			print(temp)
				

processData("18-08-2023.csv")