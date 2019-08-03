import sys
import os
sys.path.append(os.path.abspath("../core"))
from stream import Stream

def run():
    Stream.scheduler.step()
