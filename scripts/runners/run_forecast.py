"""Wrapper to run forecast and capture output."""
import sys
sys.stdout = open(r'c:\Users\asus\Desktop\decodex\forecast_output.txt', 'w', encoding='utf-8')
exec(open(r'c:\Users\asus\Desktop\decodex\stage1_forecast.py', encoding='utf-8').read())
sys.stdout.close()
