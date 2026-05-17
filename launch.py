import subprocess, os, sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
subprocess.Popen([sys.executable, "main_pyside6.py"])
