import tkinter as tk
from tkinter import ttk
import serial
import serial.tools.list_ports
import threading
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class PowerSupplyController:
    def __init__(self, master):
        self.master = master
        self.master.title("Power Supply Controller")

        # Variable to hold the serial connection
        self.ser = None

        # Serial port selection frame
        self.port_frame = ttk.LabelFrame(self.master, text="COM Port Selection")
        self.port_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        ttk.Label(self.port_frame, text="Select COM Port:").grid(row=0, column=0, padx=5, pady=5)
        self.combobox = ttk.Combobox(self.port_frame, values=self.get_serial_ports(), state="readonly")
        self.combobox.grid(row=0, column=1, padx=5, pady=5)

        self.connect_button = ttk.Button(self.port_frame, text="Connect", command=self.connect_port)
        self.connect_button.grid(row=0, column=2, padx=5, pady=5)

        # Control frame
        self.control_frame = ttk.LabelFrame(self.master, text="Control Panel")
        self.control_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        ttk.Label(self.control_frame, text="Voltage (V):").grid(row=0, column=0, padx=5, pady=5)
        self.voltage_entry = ttk.Entry(self.control_frame)
        self.voltage_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(self.control_frame, text="Current (A):").grid(row=1, column=0, padx=5, pady=5)
        self.current_entry = ttk.Entry(self.control_frame)
        self.current_entry.grid(row=1, column=1, padx=5, pady=5)

        self.set_voltage_button = ttk.Button(self.control_frame, text="Set Voltage", command=self.set_voltage)
        self.set_voltage_button.grid(row=0, column=2, padx=5, pady=5)
        self.set_voltage_button.config(state="disabled")

        self.set_current_button = ttk.Button(self.control_frame, text="Set Current", command=self.set_current)
        self.set_current_button.grid(row=1, column=2, padx=5, pady=5)
        self.set_current_button.config(state="disabled")

        self.output_button = ttk.Button(self.control_frame, text="Toggle Output", command=self.toggle_output)
        self.output_button.grid(row=2, column=0, columnspan=3, padx=5, pady=5)
        self.output_button.config(state="disabled")

        # Status frame
        self.status_frame = ttk.LabelFrame(self.master, text="Status")
        self.status_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

        ttk.Label(self.status_frame, text="Measured Voltage (V):").grid(row=0, column=0, padx=5, pady=5)
        self.voltage_label = ttk.Label(self.status_frame, text="0.0")
        self.voltage_label.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(self.status_frame, text="Measured Current (A):").grid(row=1, column=0, padx=5, pady=5)
        self.current_label = ttk.Label(self.status_frame, text="0.0")
        self.current_label.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(self.status_frame, text="Measured Power (W):").grid(row=2, column=0, padx=5, pady=5)
        self.power_label = ttk.Label(self.status_frame, text="0.0")
        self.power_label.grid(row=2, column=1, padx=5, pady=5)

        # Graph frame
        self.graph_frame = ttk.LabelFrame(self.master, text="Real-Time Graph")
        self.graph_frame.grid(row=0, column=1, rowspan=3, padx=10, pady=10, sticky="nsew")

        self.fig, self.ax = plt.subplots(3, 1, figsize=(5, 4), sharex=True)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=1)

        self.voltage_data = []
        self.current_data = []
        self.power_data = []
        self.time_data = []

        self.running = False

    def get_serial_ports(self):
        """Returns a list of available COM ports."""
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    def connect_port(self):
        """Connect to the selected COM port."""
        selected_port = self.combobox.get()
        if selected_port:
            try:
                print(f"Attempting to connect to {selected_port}")
                self.ser = serial.Serial(selected_port, 115200, timeout=1)
                self.set_voltage_button.config(state="normal")
                self.set_current_button.config(state="normal")
                self.output_button.config(state="normal")
                self.running = True
                self.update_thread = threading.Thread(target=self.update_status)
                self.update_thread.start()
                print(f"Connected to {selected_port}")
            except serial.SerialException as e:
                print(f"Failed to connect to {selected_port}: {e}")
                tk.messagebox.showerror("Connection Error", f"Failed to connect to {selected_port}\n{e}")
                self.ser = None

    def send_command(self, command):
        """Send SCPI command to power supply."""
        try:
            print(f"Sending command: {command}")
            self.ser.write((command + '\n').encode())
            response = self.ser.readline().decode().strip()
            print(f"Received response: {response}")
            return response
        except Exception as e:
            print(f"Failed to send command: {command}, Error: {e}")
            tk.messagebox.showerror("Communication Error", f"Failed to send command: {e}")
            return ""

    def set_voltage(self):
        try:
            voltage = self.voltage_entry.get()
            print(f"Setting voltage to {voltage}")
            self.send_command(f"VOLT {voltage}")
        except ValueError as e:
            print(f"Failed to set voltage: {e}")
            tk.messagebox.showerror("Input Error", "Invalid voltage value")

    def set_current(self):
        try:
            current = self.current_entry.get()
            print(f"Setting current to {current}")
            self.send_command(f"CURR {current}")
        except ValueError as e:
            print(f"Failed to set current: {e}")
            tk.messagebox.showerror("Input Error", "Invalid current value")

    def toggle_output(self):
        try:
            current_state = self.send_command("OUTP?")
            print(f"Current output state: {current_state}")
            new_state = "OFF" if current_state == "1" else "ON"
            print(f"Toggling output to {new_state}")
            self.send_command(f"OUTP {new_state}")
        except Exception as e:
            print(f"Failed to toggle output: {e}")
            tk.messagebox.showerror("Output Error", f"Failed to toggle output: {e}")

    def update_status(self):
        while self.running:
            try:
                print("Updating status...")
                voltage = float(self.send_command("MEAS:VOLT?"))
                current = float(self.send_command("MEAS:CURR?"))
                power = float(self.send_command("MEAS:POW?"))

                print(f"Measured Voltage: {voltage}, Current: {current}, Power: {power}")

                self.voltage_label.config(text=f"{voltage:.3f}")
                self.current_label.config(text=f"{current:.3f}")
                self.power_label.config(text=f"{power:.3f}")

                self.time_data.append(time.time())
                self.voltage_data.append(voltage)
                self.current_data.append(current)
                self.power_data.append(power)

                if len(self.time_data) > 100:
                    self.time_data.pop(0)
                    self.voltage_data.pop(0)
                    self.current_data.pop(0)
                    self.power_data.pop(0)

                self.plot_data()

                time.sleep(1)
            except Exception as e:
                print(f"Failed to update status: {e}")
                tk.messagebox.showerror("Update Error", f"Failed to update status: {e}")
                self.running = False

    def plot_data(self):
        try:
            print("Plotting data...")
            self.ax[0].clear()
            self.ax[1].clear()
            self.ax[2].clear()

            self.ax[0].plot(self.time_data, self.voltage_data, label="Voltage (V)")
            self.ax[1].plot(self.time_data, self.current_data, label="Current (A)")
            self.ax[2].plot(self.time_data, self.power_data, label="Power (W)")

            self.ax[0].set_ylabel("Voltage (V)")
            self.ax[1].set_ylabel("Current (A)")
            self.ax[2].set_ylabel("Power (W)")
            self.ax[2].set_xlabel("Time (s)")

            self.canvas.draw()
        except Exception as e:
            print(f"Failed to plot data: {e}")
            tk.messagebox.showerror("Plotting Error", f"Failed to plot data: {e}")

    def close(self):
        print("Closing application...")
        self.running = False
        if self.ser:
            self.ser.close()
        self.master.quit()

# Create the main application window
root = tk.Tk()
app = PowerSupplyController(root)

# Ensure proper cleanup on close
root.protocol("WM_DELETE_WINDOW", app.close)
root.mainloop()
