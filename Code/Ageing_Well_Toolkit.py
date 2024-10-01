from bluepy.btle import Scanner, DefaultDelegate, UUID
import calendar
import time
from datetime import datetime, timedelta  
from threading import Thread
import csv
import serial
from time import sleep
import os
import RPi.GPIO as GPIO

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
xbee = 18
GPIO.setup(xbee, GPIO.OUT)

# ser = serial.Serial ("/dev/ttyS0", 9600)    #Open port with baud rate
# ser1 = serial.Serial ("/dev/ttyS0", 9600)    #Open port with baud rate


print(f"STARTING {os.path.basename(__file__)}")

absPath = os.path.dirname(os.path.abspath(__file__))
print(f"Current Directory: {absPath}")
directory = absPath
sensorFiles = [f"{directory}/bookmarks/", f"{directory}/clickers/", f"{directory}/pirs/", f"{directory}/pvs/"]

activityFiles = [f"{directory}/activityZero/", f"{directory}/activityOne/", f"{directory}/activityTwo/"]

iDIndex = 0
macIndex = 1
activityIndex = 2

timeOfPing = 3
accum = 4
sess = 5

cooking = 0
chores = 1
hobbies = 2

bookmarks = [[0, "00:a0:50:0e:18:19", -1, 0, 0, 0],
             [1, "00:a0:50:0e:1c:15", -1, 0, 0, 0],
             [2, "00:a0:50:07:22:1a", -1, 0, 0, 0],
             [3, "00:a0:50:07:0e:1f", hobbies, 0, 0, 0]
]



pvs = [[0, "00:a0:50:14:07:1f", hobbies, 0, 0, 0],
       [1, "00:a0:50:17:2c:2a", hobbies, 0, 0, 0],
       [2, "00:a0:50:07:1d:22", -1, 0, 0, 0],
       [3, "00:a0:50:17:2c:26", -1, 0, 0, 0],
       [4, "00:a0:50:17:27:18", -1, 0, 0, 0],
       [5, "00:a0:50:17:29:2b", -1, 0, 0, 0],
       [6, "00:a0:50:17:2b:29", -1, 0, 0, 0],
       [7, "00:a0:50:17:2b:2e", -1, 0, 0, 0]
]




pirSensors = [[6, "06:05:04:03:02:01",  cooking],
              [6, "06:05:04:03:02:01",  chores],
              [10, "10:05:04:03:02:01", -1], 
              [11, "11:05:04:03:02:01", -1], 
              [12, "12:05:04:03:02:01", -1]
]

clickers = [
    [0,  "e2:15:10:00:01:c3", chores], # 0
    [1,  "e2:15:10:00:01:d2", -1], # 1
    [2,  "e2:15:10:00:01:c0", -1], # 2
    [3,  "e2:15:10:00:01:cc", -1], # 3
    [4,  "e2:15:10:00:01:a2", -1], # 4
    [5,  "e2:15:10:00:01:c5", -1], # 5
    [6,  "e2:15:10:00:01:ce", -1], # 6
    [7,  "e2:15:10:00:01:d0", -1], # 7
    [8,  "e2:15:10:00:01:d1", -1], # 8
    [9,  "e2:15:10:00:01:cf", -1], # 9
    [10, "e2:15:10:00:01:ca", -1], # 10
    [11, "e2:15:10:00:01:c4", -1], # 11
    [12, "e2:15:10:00:01:cd", -1], # 12
    [13, "e2:15:10:00:01:cb", -1], # 13
    [14, "e2:15:10:00:01:b7", -1], # 14
    [15, "e2:15:10:00:01:c1", -1], # 15
    [16, "e2:15:10:00:01:c6", -1], # 16
    [17, "e2:15:10:00:01:c7", chores], # 17
    [18, "e2:15:10:00:01:bf", cooking], # 18
    [19, "e2:15:10:00:01:c2", -1], # 19
    [20, "e2:15:10:00:01:c8", chores], # 20 
    [21, "e2:15:10:00:01:c9", cooking], # 21
    [22, "e2:15:10:00:01:bc", cooking]   # 22
  
]

macs = []

typeBookmark = 0
typeClicker = 1
typePIR = 2
typePV = 3

for bookmark in bookmarks:
	macs.append([bookmark[macIndex],typeBookmark])

for clicker in clickers:
	macs.append([clicker[macIndex],typeClicker])
        
for pir in pirSensors:
	macs.append([pir[macIndex],typePIR])
        
for pv in pvs:
    macs.append([pv[macIndex], typePV])


bookmarkSaveDayToDay = True
pvSaveDayToDay = True


def resetBookmarkData():
    global bookmarkSaveDayToDay
    bookmarkSaveDayToDay = True

    for bookmark in bookmarks:
        bookmark[timeOfPing] = 0
        bookmark[accum] = 0
        bookmark[sess] = 0


def resetPVData():
    global pvSaveDayToDay
    pvSaveDayToDay = True

    for pv in pvs:
        pv[timeOfPing] = 0
        pv[accum] = 0
        pv[sess] = 0

def getCurrentTime():
    current_GMT = time.gmtime()
    time_stamp = calendar.timegm(current_GMT)
    t = datetime.fromtimestamp(time_stamp)
    str_time = t.strftime("%H:%M:%S")

    return str_time

def getCurrentDate():
    current_GMT = time.gmtime()
    time_stamp = calendar.timegm(current_GMT)
    date = datetime.fromtimestamp(time_stamp)
    str_date = date.strftime("%d-%m-%Y")

    return str_date

def getYesterdaysDate():
    current_GMT = time.gmtime()
    time_stamp = calendar.timegm(current_GMT)
    date = datetime.fromtimestamp(time_stamp)
    date = date - timedelta(days=1)
    str_date = date.strftime("%d-%m-%Y")

    return str_date

class scanDelegate(DefaultDelegate):

    def __init__(self):
        DefaultDelegate.__init__(self)

    def handleDiscovery(self, dev, isNewDev, isNewData):
        # print(f"{dev.addr}")
        for mac in macs:
            if dev.addr == mac[0]:
                # print(f"{dev.addr}")

                if mac[1] == typeBookmark:
                    scanBookmarks(dev)
                elif mac[1] == typeClicker:
                    scanClickers(dev)
                elif mac[1] == typePIR:
                    scanPIRSensors(dev)
                elif mac[1] == typePV:
                    scanPVs(dev)


def saveData(filename, data):
    # print("SAVE DATA")

    shouldWrite = False

    #GET LAST ROW OF CSV and comapare  
    if os.path.isfile(filename):
        # print("FileExists")
        with open(filename) as f:
            print(os.path.abspath(filename))
            reader_obj = csv.reader(f)

            tempData = []

            for d in data:
                tempData.append(f"{d}")

            # print(f"Temp:{tempData}")

            lastRowData = []
            for row in reader_obj:
                lastRowData = row

            # print(f"---{lastRowData}")
            # print(tempData == lastRowData)

            if tempData != lastRowData:
                shouldWrite = True

            f.close()
    else:
        # print("File does not EXIST")
        shouldWrite = True


    if shouldWrite:
        # print("WRITE")
        with open(filename, 'a', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)

            writer.writerow(data)

            f.close()

def scanBookmarks(dev):
    global bookmarkSaveDayToDay

    for bookmark in bookmarks:
        if dev.addr == bookmark[macIndex]:
            current_GMT = time.gmtime()
            time_stamp = calendar.timegm(current_GMT)
            
            str_time = getCurrentTime()
            str_date = getCurrentDate()

            time_diff = 0

            if bookmark[timeOfPing] == 0:
                bookmark[timeOfPing] = time_stamp
            else:
                time_diff = time_stamp - bookmark[timeOfPing]
                # print(f"{i}: time_diff: {time_diff}")

            bookmark[timeOfPing] = time_stamp

            bookmark[accum] = bookmark[accum] + time_diff

            # 10 minutes
            sessionTimeout = 600
            # value = time_diff
            value = 1
            if time_diff > sessionTimeout:
                bookmark[sess] = bookmark[sess] + 1
                bookmark[accum] = 0
                # value = 0
                bookmarkSaveDayToDay = True
                # print("***********END OF SESSION***********")
            
            print(f"Bookmark ID: {bookmark[iDIndex]}, {str_date}, {str_time},Time Since Last PING: {time_diff}, Session: {bookmark[sess]}, Acumulator: {bookmark[accum]}")

            # Save all bookmark Data
            bookmarkData = [bookmark[iDIndex], str_date, str_time, time_diff, bookmark[sess], bookmark[accum]]

            filename = f"{sensorFiles[typeBookmark]}{str_date}.csv"
            saveData(filename, bookmarkData)

            # SAVE ACTIVITY DATA

            bookmarkData = [typeBookmark, bookmark[iDIndex], str_date, str_time, value]

            filename = f"{activityFiles[bookmark[activityIndex]]}{str_date}.csv"
            # print(f"FILE: {filename}")
            saveData(filename, bookmarkData)


            #save interaction by day
            # ONE SAVE PER SESSION  
            if bookmarkSaveDayToDay:
                # print("DAYTODAY")
                bookmarkData = [typeBookmark, bookmark[iDIndex], str_date, str_time]
                filename = f"{directory}/dayByDay/{str_date}.csv"
                saveData(filename, bookmarkData)
                bookmarkSaveDayToDay = False

def scanPVs(dev):
    global pvSaveDayToDay

    for pv in pvs:
        if dev.addr == pv[macIndex]:
            current_GMT = time.gmtime()
            time_stamp = calendar.timegm(current_GMT)
            
            str_time = getCurrentTime()
            str_date = getCurrentDate()

            time_diff = 0

            if pv[timeOfPing] == 0:
                pv[timeOfPing] = time_stamp
            else:
                time_diff = time_stamp - pv[timeOfPing]
                # print(f"{i}: time_diff: {time_diff}")

            pv[timeOfPing] = time_stamp

            pv[accum] = pv[accum] + time_diff

            # 10 minutes
            sessionTimeout = 600
            # value = time_diff
            value = 1
            if time_diff > sessionTimeout:
                pv[sess] = pv[sess] + 1
                pv[accum] = 0
                # value = 0
                pvSaveDayToDay = True
                # print("***********END OF SESSION***********")
            
            print(f"pv ID: {pv[iDIndex]}, {str_date}, {str_time},Time Since Last PING: {time_diff}, Session: {pv[sess]}, Acumulator: {pv[accum]}")

            # Save all bookmark Data
            pvData = [pv[iDIndex], str_date, str_time, time_diff, pv[sess], pv[accum]]

            filename = f"{sensorFiles[typePV]}{str_date}.csv"
            saveData(filename, pvData)

            # SAVE ACTIVITY DATA

            pvData = [typePV, pv[iDIndex], str_date, str_time, value]

            filename = f"{activityFiles[pv[activityIndex]]}{str_date}.csv"
            # print(f"FILE: {filename}")
            saveData(filename, pvData)


            #save interaction by day
            # ONE SAVE PER SESSION  
            if pvSaveDayToDay:
                # print("DAYTODAY")
                pvData = [typePV, pv[iDIndex], str_date, str_time]
                filename = f"{directory}/dayByDay/{str_date}.csv"
                saveData(filename, pvData)
                pvSaveDayToDay = False           

def scanClickers(dev):
    for clicker in clickers:
        if dev.addr == clicker[macIndex]:
            str_time = getCurrentTime()
            str_date = getCurrentDate()

            print(f"Clicker ID: {clicker[iDIndex]}, {str_date}, {str_time}, Activity: {clicker[activityIndex]}")

            # #CLICKER DATA
            
            clickerData = [clicker[iDIndex], str_date, str_time, clicker[activityIndex]]

            filename = f"{sensorFiles[typeClicker]}{str_date}.csv"
            saveData(filename, clickerData)

            # save interaction by activity/space
            # Value of interaction
            value = 1
            clickerData = [typeClicker, clicker[iDIndex], str_date, str_time, value]

            filename = f"{activityFiles[clicker[activityIndex]]}{str_date}.csv"
            saveData(filename, clickerData)

            #save interaction by day  
            clickerData = [typeClicker, clicker[iDIndex], str_date, str_time]
            filename = f"{directory}/dayByDay/{str_date}.csv"
            saveData(filename, clickerData)

def scanPIRSensors(dev):
    for pir in pirSensors:
        if dev.addr == pir[macIndex]:
            str_time = getCurrentTime()
            str_date = getCurrentDate()

            print(f"PIR ID: {pir[iDIndex]}, {str_date}, {str_time}, Activity: {pir[activityIndex]}")

            # #CLICKER DATA
            
            pirData = [pir[iDIndex], str_date, str_time, pir[activityIndex]]

            filename = f"{sensorFiles[typePIR]}{str_date}.csv"
            saveData(filename, pirData)

            # save interaction by activity/space
            # Value of interaction
            value = 1
            pirData = [typePIR, pir[iDIndex], str_date, str_time, value]

            filename = f"{activityFiles[pir[activityIndex]]}{str_date}.csv"
            saveData(filename, pirData)

            #save interaction by day  
            pirData = [typePIR, pir[iDIndex], str_date, str_time]

            filename = f"{directory}/dayByDay/{str_date}.csv"
            saveData(filename, pirData)

def getActivityCount(day, act):

    filename = f"{activityFiles[act]}{day}.csv"

    #count 
    count = 0
    if os.path.isfile(filename):
        with open(filename) as f:
            reader_obj = csv.reader(f)

            temp = ""
            for row in reader_obj:
                temp = row[4]
                # print(f"Temp: {temp}")
                count = count + int(temp)

            # print(f"Count: {count}")

            f.close()
    
    return count

def calcMinMaxAvg(act):
    min = getActivityCount(getYesterdaysDate() ,act)
    max = getActivityCount(getYesterdaysDate() ,act)
    avg = 0
    count = getActivityCount(getYesterdaysDate() ,act)
    days = 1

    tempMin = 0
    tempMax = 0
    tempDays = 0
    tempCount = 0

    filename = f"{directory}/minMaxAvg-{act}.csv"

    if os.path.isfile(filename):
        with open(filename) as f:
            reader_obj = csv.reader(f)

            
            for row in reader_obj:
                tempMin = int(row[0])
                tempMax = int(row[1])
                tempCount =  int(row[3])
                tempDays = int(row[4])

            f.close()
    else:
        tempMax = 10

    count = count + tempCount
    days = tempDays + 1

    avg = int(count/days)

    # print(days)
    if tempMax > max:
        max = tempMax

    if tempMin < min:
        min = tempMin

    data = [min, max, avg, count, days]
    saveData(filename, data)

    print(data)



def getAvg(act):
    avg = 0

    filename = f"{directory}/minMaxAvg-{act}.csv"

    if os.path.isfile(filename):
        with open(filename) as f:
            reader_obj = csv.reader(f)

            
            for row in reader_obj:
                avg = int(row[2])

            f.close()
    return avg

def averageMax():
    max = [10, 10, 10]

    for i in range(3):
        filename = f"{directory}/minMaxAvg-{i}.csv"

        if os.path.isfile(filename):
            with open(filename) as f:
                reader_obj = csv.reader(f)

                
                for row in reader_obj:
                    max[i] = int(row[1])

                f.close()

    return (max[0] + max[1] + max[2]) / 3
        

def getMax(act):
    max = 10 ## RANDOM

    filename = f"{directory}/minMaxAvg-{act}.csv"

    if os.path.isfile(filename):
        with open(filename) as f:
            reader_obj = csv.reader(f)

            
            for row in reader_obj:
                max = int(row[1])

            f.close()

    max = averageMax()
    return max

def mapIt(x, in_min, in_max, out_min, out_max):
  return int((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

def getDataToSend():
    # print("DATA TO SEND")
    letters = [['A', 'a'],['B','b'],['C','c']]
    string = ""


    for i in range(3):
        countA = getActivityCount(getCurrentDate(), i)
        avgA = getAvg(i)
        if avgA == 0:
            avgA = countA

        max = getMax(i)

        # print(f"1: countA: {countA}, avgA: {avgA}, max: {max}")
# 
        if countA >= max:
            max = countA
        if avgA >= max:
            max = avgA

        max = int(max)

        # print(f"2: countA: {countA}, avgA: {avgA}, max: {max}")

        lights_A = int((100/max) * countA)
        lights_A = mapIt(lights_A, 0, 100, 1, 8)

        lights_a = int((100/max) * avgA)
        lights_a = mapIt(lights_a, 0, 100, 1, 8)

        string = string + f"{letters[i][0]}{lights_a} {letters[i][1]}{lights_A} " # LOWER CASE OUTER UPP CASE INNER

    # print(f"TOSEND: {string}")

    return string

def recieveFromPods():
    ser = serial.Serial ("/dev/ttyS0", 9600)    #Open port with baud rate

    while True:
        received_data = ser.read()             
        sleep(0.03)
        data_left = ser.inWaiting()             
        received_data += ser.read(data_left)
        t = chr(received_data[0])
        print (t)

        str_date = getCurrentDate()
        str_time = getCurrentTime()
        
        data = [t, str_date, str_time]

        filename =  f"{directory}/pods/{str_date}.csv"
        saveData(filename, data)

def writeToPods():
    ser = serial.Serial ("/dev/ttyS0", 9600)    #Open port with baud rate

    while True:
        string = getDataToSend()
        sleep(1)
        print(f"CurrentTime: {getCurrentDate()} {getCurrentTime()}")

        arr = bytes(string, 'utf-8')
        
        # print(arr)
        ser.write(arr)
        sleep(3)

def resetAfterMidnight():
    shouldReset = True 
    while True:
        
        if getCurrentTime() == "00:01:00":
            print("NEWDAY")

            if shouldReset:
                print("RESET")
                resetBookmarkData()
                resetPVData()

                calcMinMaxAvg(0)
                calcMinMaxAvg(1)
                calcMinMaxAvg(2)
                shouldReset = False
        else:
            shouldReset = True

        sleep(0.9)

def main():
    GPIO.output(xbee, GPIO.LOW)
    sleep(0.1)
    GPIO.output(xbee, GPIO.HIGH)
    sleep(0.1)

    scanner = Scanner().withDelegate(scanDelegate())
    
    thread2 = Thread(target=writeToPods)
    thread2.start()

    thread = Thread(target=recieveFromPods)
    thread.start()

    thread3 = Thread(target=resetAfterMidnight)
    thread3.start()

    try:
        while True:
            devices = scanner.scan(0.1)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
    
