from rlc.gui import *
import sys

if __name__ == "__main__":
    Application = QApplication(sys.argv)
    Window = PMN_Window()
    Window.showMaximized()
    sys.exit(Application.exec_())
