"""Quick wrapper to run the pipeline and capture output to a file."""
import sys
import os

os.chdir(r'c:\Users\asus\Desktop\decodex')

# Redirect stdout to file
original_stdout = sys.stdout
with open('stage1_output.txt', 'w', encoding='utf-8') as f:
    sys.stdout = f
    exec(open('stage1_pipeline.py', encoding='utf-8').read(), {'__file__': r'c:\Users\asus\Desktop\decodex\stage1_pipeline.py'})
    sys.stdout = original_stdout

print("Done! Results written to stage1_output.txt")
