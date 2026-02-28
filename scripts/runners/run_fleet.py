"""Wrapper to run fleet reallocation and capture output."""
import sys
sys.stdout = open(r'c:\Users\asus\Desktop\decodex\fleet_output.txt', 'w', encoding='utf-8')
exec(open(r'c:\Users\asus\Desktop\decodex\stage1_fleet_reallocation.py', encoding='utf-8').read())
sys.stdout.close()
