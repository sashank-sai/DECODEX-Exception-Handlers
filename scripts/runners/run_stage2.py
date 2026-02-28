"""Wrapper to run Stage 2 analysis and capture output."""
import sys
sys.stdout = open(r'c:\Users\asus\Desktop\decodex\stage2_output.txt', 'w', encoding='utf-8')
exec(open(r'c:\Users\asus\Desktop\decodex\stage2_shock_analysis.py', encoding='utf-8').read())
sys.stdout.close()
