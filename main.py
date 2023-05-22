import asyncio
import bleak

from bleak import BleakClient, BleakScanner
from bleak.backends.characteristic import BleakGATTCharacteristic

from kivy.app import App
from kivy.properties import NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy_garden.graph import Graph, LinePlot
from kivy.clock import Clock
import numpy as np

class Plotter(BoxLayout):   
    zoom = NumericProperty(1)
    def __init__(self, main_app):
        super().__init__()

        self.main_app = main_app

        self.zoom = 1
        self.graph_arm = Graph(xmin=0, xmax=100,
                            ymin=0, ymax=10,
                            border_color=[1, 0, 0, 1],
                            tick_color=[1, 0, 0, 1],
                            x_grid=True, y_grid=True,
                            draw_border=False,
                            x_grid_label=True, y_grid_label=True,
                            x_ticks_major=10, y_ticks_major=10)
        self.ids.graph.add_widget(self.graph_arm)
        self.plot_arm_x = np.linspace(0, 1, 100)
        self.plot_arm_y = np.linspace(0, 0, 100)
        self.plot_arm = LinePlot(color=[1, 0, 0, 1], line_width=1.5)
        self.plot_arm.points = [(x, self.plot_arm_y[x]) for x in range(100)]
        self.graph_arm.add_plot(self.plot_arm)

        self.graph_neck = Graph(xmin=0, xmax=100,
                            ymin=0, ymax=10,
                            border_color=[1, 0, 0, 1],
                            tick_color=[1, 0, 0, 1],
                            x_grid=True, y_grid=True,
                            draw_border=False,
                            x_grid_label=True, y_grid_label=True,
                            x_ticks_major=10, y_ticks_major=10)
        self.ids.graph.add_widget(self.graph_neck)
        self.plot_neck_x = np.linspace(0, 1, 100)
        self.plot_neck_y = np.linspace(0, 0, 100)
        self.plot_neck = LinePlot(color=[1, 0, 0, 1], line_width=1.5)
        self.plot_neck.points = [(x, self.plot_neck_y[x]) for x in range(100)]
        self.graph_neck.add_plot(self.plot_neck)

        self.graph_chest = Graph(xmin=0, xmax=100,
                            ymin=0, ymax=50,
                            border_color=[1, 0, 0, 1],
                            tick_color=[1, 0, 0, 1],
                            x_grid=True, y_grid=True,
                            draw_border=False,
                            x_grid_label=True, y_grid_label=True,
                            x_ticks_major=10, y_ticks_major=25)
        self.ids.graph.add_widget(self.graph_chest)
        self.plot_chest_x = np.linspace(0, 1, 100)
        self.plot_chest_y = np.linspace(0, 0, 100)
        self.plot_chest = LinePlot(color=[1, 0, 0, 1], line_width=1.5)
        self.plot_chest.points = [(x, self.plot_chest_y[x]) for x in range(100)]
        self.graph_chest.add_plot(self.plot_chest)
    def update_plot(self, *args):
        self.plot_arm_y = self.main_app.armbar_data[-100:]
        self.plot_arm.points = [(x, self.plot_arm_y[x]) for x in range(len(self.plot_arm_y))]
       
        self.plot_neck_y = self.main_app.choke_data[-100:]
        self.plot_neck.points = [(x, self.plot_neck_y[x]) for x in range(len(self.plot_neck_y))]
       
        self.plot_chest_y = self.main_app.strike_data[-100:]
        self.plot_chest.points = [(x, self.plot_chest_y[x]) for x in range(len(self.plot_chest_y))]
    def update_zoom(self, value):
        if value == '+' and self.zoom < 8:
            self.zoom *= 2
            self.graph_arm.x_ticks_major /= 2
            self.graph_neck.x_ticks_major /= 2
            self.graph_chest.x_ticks_major /= 2
        elif value == '-' and self.zoom > 1:
            self.zoom /= 2
            self.graph_arm.x_ticks_major *= 2
            self.graph_neck.x_ticks_major *= 2
            self.graph_chest.x_ticks_major *= 2

class MainApp(App):
    #Shared Android UI Variables
    pb_armbar = NumericProperty(0.0)
    pb_choke = NumericProperty(0.0)
    pb_strike = NumericProperty(0.0)
    timer = NumericProperty(0.0)

    armbar_data = []
    choke_data = []
    strike_data = []

    def build(self):
        self.plotter = Plotter(self)
        return self.plotter 

    def __init__(self):
        super().__init__()
        self.running = True
        self.pause = True #Specifically for getting updates from notifications or the timer

        self.device_name = 'ESP32'
        self.data_uuid = "70c21748-a8da-11ed-afa1-0242ac120002"
        
        self.pb_armbar = 0.0
        self.pb_choke = 0.0
        self.pb_strike = 0.0
        self.timer = 0.0
        
    #BLE_Functions
    def on_stop(self):
        self.running = False
    async def enable_notifications(self):
        print(f"Starting scan for {self.device_name}")
        device = await BleakScanner.find_device_by_name(self.device_name)
        if device is None:
            print(f"Could not find {self.device_name}...")
        else:
            async with BleakClient(device) as client:
                print(f"Connected to {self.device_name}")
                print(f"Enabling notifications for the sensors:")
                local_data_uuid = self.data_uuid
                await client.start_notify(local_data_uuid, self.notification_handler)
                await asyncio.sleep(1000)
                await client.stop_notify(local_data_uuid)
    def notification_handler(self, characteristic: BleakGATTCharacteristic, characteristic_data: bytearray):   
        if not self.pause:
            data_list = characteristic_data.decode('utf-8').splitlines() #Data are integers represented as strings delimited by newline. 
            armbar_grams = data_list[0]
            choke_grams = data_list[1]
            strike_grams = data_list[2]

            armbar_kg = float(armbar_grams)/1000.0
            armbar_kg = round(armbar_kg, 3)
            self.armbar_data.append(armbar_kg)
            if(armbar_kg > self.pb_armbar):
                print("New Armbar PB: " + str(armbar_kg))
                self.pb_armbar = armbar_kg
            
            choke_kg = float(choke_grams)/1000.0
            choke_kg = round(choke_kg, 3)
            self.choke_data.append(choke_kg)
            if(choke_kg > self.pb_choke):
                self.pb_choke = choke_kg
            
            strike_kg = float(strike_grams)/1000.0
            strike_kg = round(strike_kg, 3)
            self.strike_data.append(strike_kg)
            if(strike_kg > self.pb_strike):
                self.pb_strike = strike_kg

            print("Armbar Reading: " + str(armbar_kg) + " kg")
            print("Choke Reading: " + str(choke_kg) + " kg")
            print("Strike Reading: " + str(strike_kg) + " kg")
    
    #Android UI Functions
    def start(self):
        self.pause = False
        Clock.schedule_once(self.plotter.update_plot, 0)
        Clock.schedule_interval(self.plotter.update_plot, 0.1)
        Clock.schedule_interval(self.timerIncrease, 0.1)
    def toggle_pause(self):
        self.pause = not self.pause
    def clear(self):
        self.armbar_data = []
        self.pb_armbar = 0.0
        
        self.choke_data = []
        self.pb_choke = 0.0
        
        self.strike_data= []
        self.pb_strike = 0.0
        
        self.timer = 0.0
    def timerIncrease(self, *args):
        if not self.pause:
            self.timer = self.timer + .1
            self.timer = round(self.timer, 1)

async def main(app):
    await asyncio.gather(app.async_run("asyncio"), app.enable_notifications())

if __name__ == "__main__":
    # app running on one thread with two async coroutines
    app = MainApp()
    asyncio.run(main(app))
