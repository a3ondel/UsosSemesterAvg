from re import sub
import re
from typing import Tuple
import mechanize
from bs4 import BeautifulSoup
import http.cookiejar as cookiejar## http.cookiejar in python3
import argparse

def get_args() -> Tuple[str,str,int,str,str]:
    parser = argparse.ArgumentParser()
    parser.add_argument('--username','-u', type = str, help = 'login to polsl, without @...')
    parser.add_argument('--password','-p', type = str, help = 'password to polsl')
    parser.add_argument('--semesters','-s', type = int, help = 'number of semesters you want to display',required=False,default=7)
    parser.add_argument('--display_degrees','-d', type = bool, help = 'type True if you want to see all of your grades',required=False,default=False)
    args = parser.parse_args()
    return args.username, args.password, args.semesters, args.display_degrees
    
username, password, semester_count, display_degrees = get_args()
    
print("Logging in")
authUrl ="https://usoscas.polsl.pl/cas/login?service=https%3A%2F%2Fusosweb.polsl.pl%2Fkontroler.php%3F_action%3Dlogowaniecas%2Findex&locale=pl"

br = mechanize.Browser()
cj = cookiejar.CookieJar()
br.set_cookiejar(cj)
br.open(authUrl)

br.select_form(nr=0)
br.form['username'] = username
br.form['password'] = password
br.submit()

print("Logged in successfuly")
#------------------------------------------------------------------------

gradesUrl = "https://usosweb.polsl.pl/kontroler.php?_action=dla_stud/studia/oceny/index"
br.open(gradesUrl)

gradesHtmlRaw = br.response().read()
gradesHtml = BeautifulSoup(gradesHtmlRaw, 'html.parser')
tablesM = gradesHtml.select("#layout-c22a")[0].select("table.grey")

gradesTable = tablesM[0]

if len(tablesM) > 1:
    gradesTable = tablesM[1]

grades = []
counter = 0

tbodies = gradesTable.select("tbody")

for tbody in tbodies:
    if tbody.attrs.__contains__("id"):
        counter += 1

start = counter - semester_count + 1
end = counter + 1

for i in range(start,end):
    gradesForSem = gradesTable.select("#tab"+ str(i))[0].select("tr")
    grades.append([])
    for grade in gradesForSem:
        gradeRaw = grade.select("td")[2].select("span")[0].text
        gradeRaw = gradeRaw.replace(",",".")

        
        num = re.findall("[2-5][\.]*5{0,1}0*",gradeRaw)
        symbol = re.findall("ZAL",gradeRaw)

        grade = 2.0

        if len(num) > 0:
            grade = float(num[0])
            
        if len(symbol) > 0:
            grade = 5.0
        
        if (num == None and symbol == None ) or (len(symbol) <= 0 and len(num) <= 0):
            continue
        
        grades[i-start].append(grade)

grades.reverse()

for i in range(0,len(grades)):
    if len(grades[i]) <= 1:
        grades[i] = [0,0,0,0,0,0,0,0,0,0,0,0,0,0]

print("grades loaded")
#------------------------------------------------------------------------

stagesLinksUrl = "https://usosweb.polsl.pl/kontroler.php?_action=dla_stud/studia/zaliczenia/index"

br.open(stagesLinksUrl)

stagesLinksHtmlRaw = br.response().read()
stagesLinksHtml = BeautifulSoup(stagesLinksHtmlRaw, 'html.parser')

links = []

tables = stagesLinksHtml.select("#layout-c22a")[0].select("table.grey")
linksTable = tables[-1].select("tr")[1:semester_count + 1]

for tr in linksTable:
    links.append(tr.select("a")[0]["href"])
    
print("stages links loaded")

#------------------------------------------------------------------------

weights = []
i = 0
for link in links:
    i += 1
    br.open(link)
    weightsHtmlRaw = br.response().read()
    weightsHtml = BeautifulSoup(weightsHtmlRaw, 'html.parser')
    tablesW = weightsHtml.select("#layout-c22a")[0].select("table.grey")
    tableW = tablesW[0]

    if len(tablesW) > 1:
        tableW = tablesW[1]

    subjectsRaw = tableW.select("tr")[2:]
    weights.append([])

    for subject in subjectsRaw:
                
        sub = subject.select(".ptzal")
        ects = 0
        if  len(sub) < 1 or subject.attrs.__contains__("class") and subject.attrs["class"][0].__contains__("sumowanie"):
            if len(subject.select(".ptzero")) <= 0:
                break
        else:
            ects = int(sub[0].text)

        weights[i-1].append(ects)
        
    print("semester " + str(i) + " weights loaded")
    
avg = []

for i in range(0,semester_count):
   sum = 0.0
   for gr in range(0,len(weights[i])):
       sum += grades[i][gr] * weights[i][gr]

   avg.append(sum / 30.0)


overallAvg = 0.0
empty = 0
print("\n")

if display_degrees:
    print("grades:\n")
    print(grades)
    print("\nweights:\n")
    print(weights)

for i in range(0,len(avg)):
    if avg[i] == 0.0:
        empty += 1
    overallAvg += avg[i]
    print("semester " + str(i + 1) + " "+ str(round(avg[i],4)))

if empty > 0:
    overallAvg /= (semester_count - empty)
else:
    overallAvg /= semester_count



print("\noverall avg: " + str(round(overallAvg,4)))