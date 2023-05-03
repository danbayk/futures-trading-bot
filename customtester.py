import csv

basefile = '4hour.csv'
suppfile = '1min.csv'

with open(basefile, 'r') as basecsv:
    basedata = csv.reader(basecsv)
    with open(suppfile, 'r') as suppcsv:
        suppdata = csv.reader(suppcsv)
        for row1 in basedata:
            print(row1[1])
        for row2 in suppdata:
            print(row2[1])