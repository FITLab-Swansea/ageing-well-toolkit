import os

print(os.path.dirname(__file__))
 
rootDir = f"{os.path.dirname(__file__)}/"


def removeCSV(dir):
    for f in os.listdir(dir):
        s = dir + f

        if (os.path.isdir(s)):
            print(f"directory: {f}")
            removeCSV(s)
        
        if f.endswith('.csv'):
            print(f"csv: {f}")
            os.remove(os.path.join(dir, f))

removeCSV(rootDir)