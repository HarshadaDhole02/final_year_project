import os

files = ['train.py', 'predict.py', 'clean_dataset.py', 'app.py', 'utils.py']
for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    content = content.replace('\\"', '"').replace('\\\\n', '\\n')
    with open(f, 'w', encoding='utf-8') as file:
        file.write(content)
print("Fixed!")
