#!/usr/bin/env python3
import time
import threading
import numpy as np
import matplotlib.pyplot as plt
import PySimpleGUI as sg
from scipy.signal import find_peaks
from scipy.optimize import curve_fit
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from periphery import GPIO

# --- Custom Modules ---
from M5Tension import setup_tension_cells, get_latest_forces, close_tension_cells
from M5IMU import read_gyro_z, ser 

# ---------------------------- GPIO SETUP ----------------------------
GPIO_CHIP = "/dev/gpiochip0"
STEP_PIN, DIR_PIN = 18, 23
EM1_PIN, EM2_PIN, EM3_PIN = 5, 6, 13
STEP = GPIO(GPIO_CHIP, STEP_PIN, "out")
DIR  = GPIO(GPIO_CHIP, DIR_PIN,  "out")
EM1 = GPIO(GPIO_CHIP, EM1_PIN, "out")
EM2 = GPIO(GPIO_CHIP, EM2_PIN, "out")
EM3 = GPIO(GPIO_CHIP, EM3_PIN, "out")
# Safe defaults
STEP.write(False); DIR.write(False)
EM1.write(False); EM2.write(False); EM3.write(False)

# ---------------------------- CONSTANTS -----------------------------
sampling_rate      = 100
IMU_RECORD_TIME    = 30
TENSION_GAIN       = 3.3508e4 # Obtained from calibration
TENSION_OFFSET     = -1.5682e-5 # Obtained from calibration
MOTOR_TRIGGER_TIME = 1.0
STEADY_DELAY       = 2.0
R                  = 0.4572 # Radius of the plate (m)
L                  = 1.5 # Length of suspension cables (m)

# ----------------------- Motor/EM Function --------------------------
def trigger_motor():
    EM1.write(True); EM2.write(True); EM3.write(True)
    time.sleep(1)
    DIR.write(True)
    for _ in range(120): STEP.write(False); time.sleep(0.0015); STEP.write(True); time.sleep(0.0015)
    DIR.write(False)
    for _ in range(300): STEP.write(False); time.sleep(0.0015); STEP.write(True); time.sleep(0.0015)
    EM1.write(False); EM2.write(False); EM3.write(False)
    time.sleep(1)
    DIR.write(True)
    for _ in range(180): STEP.write(False); time.sleep(0.0015); STEP.write(True); time.sleep(0.0015)

# ------------------- Tension Cell Measurements ----------------------
def measure_plate_mass(serial_number=716326, channels=3):
    cells = setup_tension_cells(serial_number=serial_number, channels=channels)
    time.sleep(2)
    samples = []
    for _ in range(20):
        forces = get_latest_forces()
        if forces:
            vals = [(raw - TENSION_OFFSET)*TENSION_GAIN for raw in forces.values()]
            samples.append(np.mean(vals))
        time.sleep(0.1)
    close_tension_cells(cells)
    return 3 * np.mean(samples)

def measure_object_mass(baseline, serial_number=716326, channels=3):
    cells = setup_tension_cells(serial_number=serial_number, channels=channels)
    time.sleep(2)
    samples = []
    for _ in range(20):
        forces = get_latest_forces()
        if forces:
            vals = [(raw - TENSION_OFFSET)*TENSION_GAIN for raw in forces.values()]
            samples.append(np.mean(vals))
        time.sleep(0.1)
    close_tension_cells(cells)
    return 3 * np.mean(samples) - baseline

# ------------------------ IMU Data & Analysis -----------------------
def record_imu_data():
    offset = read_gyro_z()
    ser.reset_input_buffer()
    times, gyro_z = [], []
    trig = False
    start = time.time()
    while time.time() - start < IMU_RECORD_TIME:
        t = time.time() - start
        if t >= MOTOR_TRIGGER_TIME and not trig:
            trigger_motor(); trig=True
        val = read_gyro_z() - offset
        times.append(t); gyro_z.append(val)
        time.sleep(1/sampling_rate)
    return np.array(times), np.array(gyro_z)

def analyze_imu_data(times, gyro_z, object_mass):
    steady = MOTOR_TRIGGER_TIME + STEADY_DELAY
    mask = times >= steady
    st, gz = times[mask], gyro_z[mask]
    # settling
    def exp_decay(t, A, tau, C): return A*np.exp(-t/tau)+C
    try:
        popt, _ = curve_fit(exp_decay, st[:len(gz)], np.abs(np.convolve(gz, np.ones(10)/10, mode='valid')), maxfev=10000)
        settling = 4 * popt[1]
    except:
        settling = None
    # period & MOI
    peaks, _ = find_peaks(gz, height=0.1)
    if len(peaks)>1:
        period = np.mean(np.diff(st[peaks]))
        moi = object_mass * R**2 * period**2 / (4*np.pi**2*L)
    else:
        period = moi = None
    # figure
    fig, ax = plt.subplots(figsize=(4,3))
    ax.plot(st, gz, label='ω (deg/s)')
    ax.axvline(steady, color='r', linestyle='--', label='Steady Start')
    ax.set_xlabel('Time (s)'); ax.set_ylabel('ω (deg/s)')
    ax.legend(); ax.grid()
    return settling, period, moi, fig

# --------------------------- GUI SETUP ------------------------------
sg.set_options(font=('Helvetica',14))
layout = [
    [sg.Text('🔧 Pendulum Control', expand_x=True, justification='center')],
    [sg.Button('1.Measure Plate', key='PLATE'), sg.Text('', key='PSTAT')],
    [sg.Button('2.Measure Object', key='OBJ', disabled=True), sg.Text('', key='OSTAT')],
    [sg.Button('3.Perform MOI', key='MOI', disabled=True), sg.Text('', key='MSTAT')],
    [sg.Button('4.Show Results', key='RES', disabled=True), sg.Button('Run Again', key='RUN', disabled=True)],
    [sg.Canvas(key='CANVAS')],
    [sg.Multiline('', key='RESULTS', size=(50,5), disabled=True)]
]
window = sg.Window('Pendulum Kiosk', layout, finalize=True)

# helpers to draw figure
canvas_elem = window['CANVAS']
canvas = canvas_elem.TKCanvas

def draw_figure(canvas, figure):
    for child in canvas.winfo_children(): child.destroy()
    agg = FigureCanvasTkAgg(figure, canvas)
    agg.draw(); agg.get_tk_widget().pack()

# state
baseline = object_mass = None
imu_data = None

# reset function
def reset():
    global baseline, object_mass, imu_data
    baseline = object_mass = imu_data = None
    for k in ('PSTAT','OSTAT','MSTAT','RESULTS'): window[k].update('')
    window['PLATE'].update(disabled=False)
    window['OBJ'].update(disabled=True)
    window['MOI'].update(disabled=True)
    window['RES'].update(disabled=True)
    window['RUN'].update(disabled=True)
    draw_figure(canvas, plt.figure())

reset()

# event loop
while True:
    event, vals = window.read()
    if event in (sg.WIN_CLOSED, 'Exit'): break
    if event=='RUN': reset()
    if event=='PLATE':
        window['PSTAT'].update('Measuring...')
        threading.Thread(target=lambda: window.write_event_value('PDONE', measure_plate_mass()), daemon=True).start()
    elif event=='PDONE':
        baseline = vals[event]
        lb = baseline*2.205
        window['PSTAT'].update(f'{baseline:.3f} kg / {lb:.2f} lb')
        window['PLATE'].update(disabled=True); window['OBJ'].update(disabled=False)
    elif event=='OBJ':
        window['OSTAT'].update('Measuring...')
        threading.Thread(target=lambda: window.write_event_value('ODONE', measure_object_mass(baseline)), daemon=True).start()
    elif event=='ODONE':
        object_mass = vals[event]
        lb = object_mass*2.205
        window['OSTAT'].update(f'{object_mass:.3f} kg / {lb:.2f} lb')
        window['OBJ'].update(disabled=True); window['MOI'].update(disabled=False)
    elif event=='MOI':
        window['MSTAT'].update('Recording...')
        threading.Thread(target=lambda: window.write_event_value('MDONE', record_imu_data()), daemon=True).start()
    elif event=='MDONE':
        imu_data = vals[event]
        window['MSTAT'].update('Done')
        window['MOI'].update(disabled=True); window['RES'].update(disabled=False)
    elif event=='RES':
        times, gyro = imu_data
        settling, period, moi, fig = analyze_imu_data(times, gyro, object_mass)
        # draw inside GUI
        draw_figure(canvas, fig)
        # show text
        lines = [f'Object Mass: {object_mass:.3f} kg',
                 #f'Settling Time: {settling:.2f} s' if settling else 'Settling: N/A',
                 f'Period: {period:.3f} s' if period else 'Period: N/A',
                 f'MOI: {moi:.4f} kg·m²' if moi else 'MOI: N/A']
        window['RESULTS'].update('\n'.join(lines))
        window['RES'].update(disabled=True); window['RUN'].update(disabled=False)

window.close()
