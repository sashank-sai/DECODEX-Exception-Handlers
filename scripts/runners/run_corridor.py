"""Wrapper to run corridor analysis and capture output."""
import sys
sys.stdout = open(r'c:\Users\asus\Desktop\decodex\corridor_output.txt', 'w', encoding='utf-8')
exec(open(r'c:\Users\asus\Desktop\decodex\stage1_corridor_analysis.py', encoding='utf-8').read())
sys.stdout.close()
