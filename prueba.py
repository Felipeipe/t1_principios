import json
with open("articulos.json", "r+") as file:
    data = json.load(file)

for key, value in data.items():
    print(type(value), value)
    print(type(key), key)

print(list(data.items())[1])