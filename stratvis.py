from lib.StratVisMain import (StratVisMain)
from multiprocessing import freeze_support
from os import system

if __name__ == '__main__':
	freeze_support()
	
	system("title StratVis")
	gui = StratVisMain()
