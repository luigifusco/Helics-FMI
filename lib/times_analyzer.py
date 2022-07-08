import json

with open('ApartmentNoPV_times10.json') as file:
    t10 = json.load(file)
with open('ApartmentNoPV_times30.json') as file:
    t30 = json.load(file)
with open('ApartmentNoPV_times3600.json') as file:
    t3600 = json.load(file)
    

a10 = sum(s[0] for s in t10['steps']) / len(t10['steps'])
a30 = sum(s[0] for s in t30['steps']) / len(t30['steps'])
a3600 = sum(s[0] for s in t3600['steps']) / len(t3600['steps'])

print(a10)
print(a30)
print(a3600)