from PySide2.QtCore import QObject, Signal
import numpy as np


class Circuit:

    def __init__(self, R: float, L: float, C: float, sem=0.0, f=0.0, p=0.0):
        self.R = R
        self.L = L
        self.C = C

        self.sem = sem
        self.freq = f
        self.phase = p

    def diffeq(self, t, p, q):
        return self.sem * np.sin(2*np.pi*self.freq * t + self.phase) - self.R/self.L * p - q / self.L / self.C


class Simulation(QObject):

    iteration = Signal(int)

    def __init__(self, circuit: Circuit, t0: float, t1: float, q0: float, p0: float, dt: float):
        super().__init__()
        if t1 < t0:
            raise ValueError("t0 must be lower than t1")
        if dt > t1 - t0:
            raise ValueError("time step must be shorter than time interval")
        if dt <= 0:
            raise ValueError("time step must be a positive number")

        self.dt = dt
        self.circuit = circuit

        self.time = np.arange(t0, t1, self.dt, dtype=float)
        self.steps = len(self.time)

        self.charge = np.zeros(shape=(self.steps,), dtype=float)
        self.charge[0] = q0

        self.current = np.zeros(shape=(self.steps,), dtype=float)
        self.current[0] = p0

        self.resistor_voltage = np.zeros(shape=(self.steps,), dtype=float)
        self.inductor_voltage = np.zeros(shape=(self.steps,), dtype=float)
        self.capacitor_voltage = np.zeros(shape=(self.steps,), dtype=float)

        self.running = False

    def solve(self):
        self.running = True
        progress = 0
        for i in range(1, self.steps):
            if self.running:
                t = self.time[i - 1]
                p = self.current[i - 1]
                q = self.charge[i - 1]

                dp1 = self.dt * self.circuit.diffeq(t, p, q)
                dq1 = self.dt * p

                dp2 = self.dt * self.circuit.diffeq(t + self.dt / 2, p + dp1 / 2, q + dq1 / 2)
                dq2 = self.dt * (p + dp1 / 2)

                dp3 = self.dt * self.circuit.diffeq(t + self.dt / 2, p + dp2 / 2, q + dq2 / 2)
                dq3 = self.dt * (p + dp2 / 2)

                dp4 = self.dt * self.circuit.diffeq(t + self.dt, p + dp3, q + dq3)
                dq4 = self.dt * (p + dp3)

                self.current[i] = p + (dp1 + 2 * dp2 + 2 * dp3 + dp4) / 6
                self.charge[i] = q + (dq1 + 2 * dq2 + 2 * dq3 + dq4) / 6

                current_progress = int(round(100*i/self.steps))
                if current_progress != progress:
                    self.iteration.emit(current_progress)
                    progress = current_progress

        if self.running:
            self.resistor_voltage = self.current * self.circuit.R
            self.inductor_voltage = - self.circuit.L * self.circuit.diffeq(self.time, self.current, self.charge)
            self.capacitor_voltage = self.charge / self.circuit.C

    def getResults(self, offset: int):
        if offset == 1:
            return self.time, [self.charge, self.current, self.resistor_voltage, self.inductor_voltage, self.capacitor_voltage]
        elif offset < 0:
            raise ValueError("Negative step!")
        else:
            time              = [self.time[i]              for i in range(0, len(self.time),              offset)]
            charge            = [self.charge[i]            for i in range(0, len(self.charge),            offset)]
            current           = [self.current[i]           for i in range(0, len(self.current),           offset)]
            resistor_voltage  = [self.resistor_voltage[i]  for i in range(0, len(self.resistor_voltage),  offset)]
            inductor_voltage  = [self.inductor_voltage[i]  for i in range(0, len(self.inductor_voltage),  offset)]
            capacitor_voltage = [self.capacitor_voltage[i] for i in range(0, len(self.capacitor_voltage), offset)]
            return time, [charge, current, resistor_voltage, inductor_voltage, capacitor_voltage]

    def kill(self):
        self.running = False

