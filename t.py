import json

d = {"key1": "value1", "key2": "value2"}
d2 = {"key2": "toto", "key4": "value4"}


print(json.dumps(d))
print(json.dumps(d2))
d3 = {**d, **d2}
print(json.dumps(d3))
