from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from pyqtgraph import PlotWidget, mkPen

from rlc.simulation import *
from math import log10


class Solver(QThread):

    solved = Signal(Simulation)
    progress = Signal(int)

    def __init__(self):
        super().__init__()
        self.simulation = None

    def run(self):
        if self.simulation is not None:
            self.simulation.solve()
            self.progress.emit(100)
            self.solved.emit(self.simulation)
        else:
            raise AttributeError("Simulation not set!")

    def startSimulation(self, params: list):
        circuit = Circuit(params[5], params[6], params[7], params[8], params[9], params[10])
        self.simulation = Simulation(circuit, params[0], params[1], params[3], params[4], params[2])
        self.simulation.iteration.connect(self.progress.emit)
        self.start()


class Graphs(QTabWidget):

    def __init__(self):
        super().__init__()
        self.setMinimumSize(1100, 600)

        titles = ["Charge", "Current", "Resistor Voltage", "Inductor Voltage", "Capacitor Voltage"]
        units  = ["C", "A", "V", "V", "V"]
        font   = {"color": "#FFFFFF", "font-size": "18pt"}
        labels = [titles[i] + " [" + units[i] + "]" for i in range(5)]

        self.graphs = {title: PlotWidget() for title in titles}
        for i in range(5):
            self.graphs[titles[i]].setLabel("bottom", "Time [s]", **font)
            self.graphs[titles[i]].setLabel("left", labels[i], **font)
            self.graphs[titles[i]].setBackground("#000000")
            self.addTab(self.graphs[titles[i]], titles[i])

    def plot(self, simulation: Simulation):
        pen = mkPen(color=(255, 255, 255), width=4, style=Qt.SolidLine)

        points_number_magnitude = log10(len(simulation.charge))
        if points_number_magnitude <= 3:
            time, results = simulation.getResults(1)
        else:
            delta = int(len(simulation.charge) // 1e4)
            time, results = simulation.getResults(delta)

        for i, key in enumerate(self.graphs.keys()):
            self.graphs[key].clear()
            self.graphs[key].plot(time, results[i], pen=pen)


class FormsHolder(QWidget):

    def __init__(self):
        super().__init__()
        self.forms_layout = QFormLayout()
        self.setLayout(self.forms_layout)

        titles = ["Start [s]", "End [s]", "Step [s]",
                  "Initial Charge [C]", "Initial Current [A]",
                  "Resistance [Ω]", "Inductance [H]", "Capacitance [F]",
                  "Source Voltage [V]", "Source Frequency [Hz]",
                  "Source Phase [s]"]

        self.labels = [QLabel(title) for title in titles]
        for label in self.labels:
            label.setAlignment(Qt.AlignCenter)
            label.setMinimumSize(170, 40)

        self.entries = [QLineEdit() for i in range(len(titles))]
        for entry in self.entries:
            entry.setAlignment(Qt.AlignCenter)
            entry.setMinimumSize(200, 40)

        for i in range(len(titles)):
            self.forms_layout.addRow(self.labels[i], self.entries[i])

    def getParameters(self):
        return [float(entry.text()) for entry in self.entries]


class Forms(QWidget):

    parameters_set = Signal(list)

    def __init__(self):
        super().__init__()
        self.forms_layout = QVBoxLayout()
        self.setLayout(self.forms_layout)

        self.title_label = QLabel("Simulation Parameters")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFixedHeight(60)

        self.forms = FormsHolder()

        self.progress_label = QLabel("0%")
        self.progress_label.setMinimumHeight(60)
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setStyleSheet("font-size: 24pt")

        self.sim_button = QPushButton("Simulate")
        self.sim_button.setFixedHeight(60)
        self.sim_button.clicked.connect(lambda: self.parameters_set.emit(self.forms.getParameters()))
        self.sim_button.setEnabled(False)

        self.signature_label = QLabel("infinite-dark")
        self.signature_label.setAlignment(Qt.AlignCenter)
        self.signature_label.setFixedHeight(40)

        self.forms_layout.addWidget(self.title_label)
        self.forms_layout.addWidget(self.forms)
        self.forms_layout.addWidget(self.progress_label)
        self.forms_layout.addWidget(self.sim_button)
        self.forms_layout.addWidget(self.signature_label)

    def updateProgress(self, value: int):
        self.progress_label.setText(str(value) + "%")


class PMN_Window(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Numerical Methods - RLC Circuit")

        with open("resources/stylesheet.css", "r") as styles:
            lines = styles.readlines()
        lines = [line.replace("\n", "") for line in lines]
        style = "".join(lines)
        self.setStyleSheet(style)

        self.frame = QWidget()
        self.frame_layout = QHBoxLayout()
        self.frame.setLayout(self.frame_layout)
        self.setCentralWidget(self.frame)

        self.solver = Solver()
        self.graphs = Graphs()
        self.forms = Forms()

        self.forms.parameters_set.connect(self.solver.startSimulation)
        self.solver.solved.connect(self.graphs.plot)
        self.solver.progress.connect(self.forms.updateProgress)

        self.frame_layout.addWidget(self.graphs, 10)
        self.frame_layout.addWidget(self.forms, 2)

    def keyReleaseEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Q:
            self.close()
        else:
            try:
                self.forms.forms.getParameters()
                self.forms.sim_button.setEnabled(True)
            except ValueError:
                self.forms.sim_button.setEnabled(False)

    def closeEvent(self, event: QCloseEvent):
        self.solver.simulation.kill()
        self.solver.wait()
        event.accept()

