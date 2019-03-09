from PyQt5.QtWidgets import QFileDialog, QMainWindow, QApplication
import sys
import matplotlib.pyplot as plt
from statistics import median, variance, mean
from math import sqrt
import numpy as np
from scipy.signal import butter, lfilter, freqz


class DataVisualisation(QMainWindow):
    def __init__(self):
        super().__init__()

        self.l_pos = []
        self.timings = []
        self.l_press = []
        self.r_pos = []
        self.r_press = []
        self.navinfo = []

        self.pos_info = {"l_pos": 0,
                         "r_pos": 0,
                         "time": 0,
                         "lat": 0,
                         "lon": 0,
                         "car_spd": 0}

        self.process_raw_info = {"l_pos":[],
                                "r_pos":[],
                                "time":[],
                                "lat":[],
                                "lon":[],
                                "car_spd": []}

        self.process_info = {"l_pos": [],
                                 "r_pos": [],
                                 "time": [],
                                 "lat": [],
                                 "lon": [],
                                 "car_spd": []}


        self.open_file()

    def open_file(self):
        fnamesRaw = QFileDialog.getOpenFileNames(self,'Open File', 'C:\\Users\\ADiKo\\Desktop\\', 'txt file (*.txt)')[0]
        print(fnamesRaw)
        #self.csvFileName = fname.split('.')[0] + ".csv"
        results_dict = {"comp": 0, "cycle": 0, "x": [], "y": []}
        results_data = []
        csv_results = []
        csv_dict = {"comp": 0, "cycle": 0, "cs": 0, "hs": []}
        curComp = -1
        curCycle = 0
        lastCycleInFile = 0
        fnames_dict = {}
        for f in fnamesRaw:
            k = f.split(".")[-2].split("_")[-1]
            fnames_dict[k] = f
        print(fnames_dict)
        l_dict = fnames_dict.keys()
        l_dict = list(l_dict)
        l_dict.sort()
        print(l_dict)
        try:
            for k in l_dict:
                fname = fnames_dict[k]
                f = open(fname, 'r')
                print("file opened: ", end="")
                print(fname)
                for line in f:
                    if len(line) > 2:
                        if line.startswith("Comp"):
                            if curComp >= 0:
                                results_data.append(results_dict)
                                csv_results.append(csv_dict)
                                results_dict = {"comp": 0, "cycle": 0, "x": [], "y": []}
                                csv_dict = {"comp": 0, "cycle": 0, "cs": 0, "hs": []}
                            curComp = int(line[7])
                            results_dict["comp"] = curComp
                            csv_dict["comp"] = curComp
                        elif line.startswith("Cyle"):
                            l = line.split(" ")
                            curCycle = int(l[2])
                            print("cur cycle is: %d" % (curCycle))
                            if curComp == 0:
                                curCycle = int(curCycle / 2) + 1
                            else:
                                curCycle = int(curCycle / 2)
                            curCycle += lastCycleInFile
                            results_dict["cycle"] = curCycle
                            csv_dict["cycle"] = curCycle
                            #lastCycleInFile = curCycle
                        else:
                            if line.startswith("cs") or line.startswith("hs"):
                                l = line.split(",")
                                results_dict["x"].append(int(l[1]))
                                results_dict["y"].append(int(l[2]))
                            else:
                                l = line.split(",")
                                results_dict["x"].append(int(l[1]))
                                results_dict["y"].append(int(l[2]))

                            if line.startswith("cs"):
                                l = line.split(",")
                                csv_dict["cs"] = int(l[4]) - int(l[1])
                            elif line.startswith("hs"):
                                l = line.split(",")
                                csv_dict["hs"].append(int(l[4]) - int(l[1]))

                results_data.append(results_dict)
                csv_results.append(csv_dict)
                f.close()
                lastCycleInFile = curCycle
        except Exception as ex:
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            print(message)

        for r in results_data:
            print(r)
        print()
        for r in csv_results:
            print(r)

        self.write_to_csv("Common Data.csv", csv_results)

        '''
        for r in results_data:
            plt.figure(r["cycle"])
            if r["comp"] == 0:
                plt.plot(r["x"], r["y"], "r*-")
            else:
                plt.plot(r["x"], r["y"], "b*-")

        plt.show()
        '''



    def show_graphs(self):
        self.process_info['time'] = self.time_ms_to_s(self.process_raw_info['time'])
        #self.process_info['l_pos'] = self.adc_to_m(self.process_raw_info['l_pos'])
        self.process_info['l_pos'] = self.process_raw_info['l_pos']
        self.process_info['r_pos'] = self.process_raw_info['r_pos']

        self.process_info['car_spd'] = self.process_raw_info['car_spd']
        self.process_info['lat'] = self.process_raw_info['lat'][:]
        self.process_info['lon'] = self.process_raw_info['lon'][:]

        #self.write_to_csv("demo.csv", self.process_info)
        self.write_to_csv(self.csvFileName, self.process_info)



    def write_to_csv(self, csv_name, data):
        try:
            f = open(csv_name, 'w')

            max_hs_steps = 0
            for d in data:
                if len(d["hs"]) > max_hs_steps:
                    max_hs_steps = len(d["hs"])

            message_line = "Compressor\tCycle\tCold (s)\tMean HOT (s)"

            for i in range(max_hs_steps):
                message_line += "\tHot (s)"

            message_line += "\n"

            f.write(message_line)

            for d in data:
                if d["comp"] == 0:
                    message_line = ""
                    if d["comp"] == 0:
                        message_line = "China\t"
                    elif d["comp"] == 1:
                        message_line = "Viair\t"

                    message_line += str(d["cycle"]) + "\t"

                    message_line += str(round(d["cs"] / 1000, 1)) + "\t"

                    hs_mean = 0
                    hs_counter = 0
                    for hs in d["hs"]:
                        hs_counter += 1
                        hs_mean += hs

                    hs_mean = hs_mean / hs_counter
                    message_line += str(round(hs_mean / 1000, 1))

                    for hs in d["hs"]:
                        message_line += "\t" + str(round(hs / 1000, 1))

                    message_line += "\n"

                    f.write(message_line.replace(".", ","))
            for d in data:
                if d["comp"] == 1:
                    message_line = ""
                    if d["comp"] == 0:
                        message_line = "China\t"
                    elif d["comp"] == 1:
                        message_line = "Viair\t"

                    message_line += str(d["cycle"]) + "\t"

                    message_line += str(round(d["cs"] / 1000, 1)) + "\t"

                    hs_mean = 0
                    hs_counter = 0
                    for hs in d["hs"]:
                        hs_counter += 1
                        hs_mean += hs

                    hs_mean = hs_mean / hs_counter
                    message_line += str(round(hs_mean / 1000, 1))

                    for hs in d["hs"]:
                        message_line += "\t" + str(round(hs / 1000, 1))

                    message_line += "\n"

                    f.write(message_line.replace(".", ","))


            f.close()
        except Exception as ex:
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            print(message)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = DataVisualisation()
    #sys.exit(app.exec_())