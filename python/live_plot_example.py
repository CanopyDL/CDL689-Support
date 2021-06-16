from CDL689 import *
import time
import time
import numpy as np
import tkinter as Tk
import matplotlib

matplotlib.use("tkagg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import math
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import datetime
import csv


def on_closing():
    global run
    run = 0
    print('closed')

def data_tasks():
    global data_t0
    global acc_data,gyro_data
    t1 = time.time()
    if (t1 - data_t0) > .2 and imu.stream:
        acc_data.append(imu.acc[:,0])
        gyro_data.append(imu.gyro[:,0])
        data_t0=t1


def gui_tasks():
    global gui_t0
    global data_ax
    global sense
    t1 = time.time()
    if (t1 - gui_t0) > .2:
        acc_ax.clear()
        gyro_ax.clear()

        if acc_data:
            acc_ax.plot(acc_data)
        if gyro_data:
            gyro_ax.plot(gyro_data)

        acc_ax.set_ylabel('Acceleration')
        gyro_ax.set_ylabel('Gyroscope')
        acc_ax.grid()
        gyro_ax.grid()
        acc_ax.set_xlabel('Time')
        gyro_ax.set_xlabel('Time')
        # print(sense.humid_data)
        canvas.draw()

        gui_t0 = t1

def connect():
    imu.open(port_var.get())

def disconnect():
    imu.close()

def start_stream():
    imu.setUpdateRate(10000)
    imu.start_stream()

def stop_stream():
    imu.stop_stream()


if __name__ == "__main__":
    ###########
    # GLOBAL VARIABLES
    ###########
    run = 1
    gui_t0 = 0
    data_t0 = 0
    acc_data = []
    gyro_data = []
    ###########
    ########
    # STANDARD TK STUFF
    ########

    imu=CDL689()

    root = Tk.Tk()
    # t0 = time.time()
    # w, h = root.winfo_screenwidth(), root.winfo_screenheight()
    # root.attributes('-zoomed', True)
    root.protocol("WM_DELETE_WINDOW", on_closing)
    f = Figure()

    # gs1 = gridspec.GridSpec(2, 1)
    # gs1.update(wspace=0.025, hspace=0)
    # f.patch.set_facecolor('#f0f0f0')
    acc_ax = f.add_subplot(2,1,1)
    gyro_ax = f.add_subplot(2,1,2)
    # f.tight_layout()
    canvas = FigureCanvasTkAgg(f, master=root)
    NavigationToolbar2Tk(canvas, root)
    canvas.draw()
    canvas.get_tk_widget().pack(side=Tk.LEFT, fill=Tk.BOTH, expand=1)
    ###############

    # OBJECTS
    ##########
    port_var = Tk.StringVar()
    port_var.set('/dev/cu.usbserial-AM00KH14')
    ###########

    # current_date()

    frame = Tk.Frame(root)
    frame.pack(side=Tk.RIGHT, fill=Tk.BOTH)



    Tk.Frame(master=frame, width=200, height=20).pack()

    Tk.Label(master=frame, text="Port:").pack()
    Tk.Entry(master=frame, width=17, textvariable=port_var, justify='center').pack()
    con_button = Tk.Button(master=frame, text='Connect', command=connect, width=17)
    con_button.pack()
    dis_button = Tk.Button(master=frame, text='Disconnect', command=disconnect, width=17)
    dis_button.pack()
    start_button = Tk.Button(master=frame, text='Start Stream', command=start_stream, width=17)
    start_button.pack()
    stop_button = Tk.Button(master=frame, text='Stop Stream', command=stop_stream, width=17)
    stop_button.pack()


    while run:
        root.update_idletasks()
        root.update()
        gui_tasks()
        imu.tasks()
        data_tasks()
        time.sleep(.005)
    root.quit()