from lib.View import (View)
from lib.Model import (Model)

from PySide2 import (QtWidgets)
import sys

class StratVisMain(object):
	
	def __init__(self):
		
		app = QtWidgets.QApplication(sys.argv)
		model = Model()
		view = View(model)
		view.show()
		app.exec_()
