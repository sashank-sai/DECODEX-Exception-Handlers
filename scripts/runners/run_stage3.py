import sys
sys.stdout = open(r'c:\Users\asus\Desktop\decodex\output\stage3\stage3_output.txt', 'w', encoding='utf-8')
exec(open(r'c:\Users\asus\Desktop\decodex\scripts\stage3\stage3_accountability.py', encoding='utf-8').read())
sys.stdout.close()
