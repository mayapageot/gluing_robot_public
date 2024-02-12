path = r"C:\Users\admin-local\Desktop\JC3_CandT_20240212_1708.CTD"
import chardet

# Read file in binary mode
with open(path, 'rb') as file:
    # Detect encoding
    encoding = chardet.detect(file.read())['encoding']

# Open file with detected encoding
with open(path, 'r', encoding=encoding) as file:
    for line in file:
        print(line.strip())