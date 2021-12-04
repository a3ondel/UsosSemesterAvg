from re import sub
import re
import mechanize
from bs4 import BeautifulSoup
import http.cookiejar as cookiejar## http.cookiejar in python3
import sys


if len(sys.argv) <= 2:
    print("Wypierdalaj!")
    exit()

semsesters = 6
if len(sys.argv) >= 4:
    semsesters = int(sys.argv[3])

displayGradesAndWeights = False
if len(sys.argv) >= 5:
    displayGradesAndWeights = True

    
print("Logging in")
authUrl ="https://usoscas.polsl.pl/cas/login?service=https%3A%2F%2Fusosweb.polsl.pl%2Fkontroler.php%3F_action%3Dlogowaniecas%2Findex&locale=pl"

br = mechanize.Browser()
cj = cookiejar.CookieJar()
br.set_cookiejar(cj)
br.open(authUrl)

br.select_form(nr=0)
br.form['username'] = sys.argv[1]
br.form['password'] = sys.argv[2]
br.submit()

print("Logged in successfuly")

gradesUrl = "https://usosweb.polsl.pl/kontroler.php?_action=dla_stud/studia/oceny/index"
br.open(gradesUrl)

gradesHtmlRaw = br.response().read()
gradesHtml = BeautifulSoup(gradesHtmlRaw, 'html.parser')
tablesM = gradesHtml.select("#layout-c22a")[0].select("table.grey")

gradesTable = tablesM[0]

if len(tablesM) > 1:
    gradesTable = tablesM[1]

grades = []

for i in range(1,semsesters + 1):
    gradesForSem = gradesTable.select("#tab"+ str(i))[0].select("tr")
    grades.append([])
    for grade in gradesForSem:
        pryt = grade.select("td")[2].select("span")[0].text
        pryt = pryt.replace(",",".")

        
        x = re.findall("[2-5][\.]*5{0,1}0*",pryt)
        y = re.findall("ZAL",pryt)

        grade = 2.0

        if len(x) > 0:
            grade = float(x[0])
            
        if len(y) > 0:
            grade = 5.0
        
        if (x == None and y == None ) or (len(y) <= 0 and len(x) <= 0):
            continue
        
        grades[i-1].append(grade)

grades.reverse()

for i in range(0,len(grades)):
    if len(grades[i]) <= 1:
        grades[i] = [0,0,0,0,0,0,0,0,0,0,0,0,0,0]

print("grades loaded")

stagesLinksUrl = "https://usosweb.polsl.pl/kontroler.php?_action=dla_stud/studia/zaliczenia/index"

br.open(stagesLinksUrl)

stagesLinksHtmlRaw = br.response().read()
stagesLinksHtml = BeautifulSoup(stagesLinksHtmlRaw, 'html.parser')

links = []

tables = stagesLinksHtml.select("#layout-c22a")[0].select("table.grey")

linksTable = tables[-1].select("tr")[1:semsesters + 1]
# print(tables[-1].text)

for tr in linksTable:
    links.append(tr.select("a")[0]["href"])
    # print(tr.text + "\n-------------------------------------------------\n")

print("stages links loaded")

i = 0

weights = []
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

for i in range(0,semsesters):
   sum = 0.0
   for gr in range(0,len(weights[i])):
       sum += grades[i][gr] * weights[i][gr]

   avg.append(sum / 30.0)


overallAvg = 0.0
empty = False
print("\n")

if displayGradesAndWeights:
    print("grades:\n")
    print(grades)
    print("\nweights:\n")
    print(weights)

for i in range(0,len(avg)):
    if avg[i] == 0.0:
        empty = True
    overallAvg += avg[i]
    print("semester " + str(i + 1) + " "+ str(round(avg[i],4)))

if empty:
    overallAvg /= (semsesters -1)
else:
    overallAvg /= semsesters



print("\noverall avg: " + str(round(overallAvg,4)))


