# -*- coding: utf-8 -*-
import subprocess , argparse , sys , imp , os, unicodedata
from wifi import Cell , Scheme


'''
DPWO
Default Password Wifi Owner 0.4v
python3
'''

# AIRPORT_PATH = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/A/Resources/airport"
AIRPORT_PATH = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"


class NETOwner():
    def __init__(self, iface, connect=False,brute = False,
                 airport=AIRPORT_PATH, verbosity=0):
        self.iface = iface
        self.brute = brute
        self.connect = connect
        self.airport = airport
        self.verbosity = verbosity
        self.os = sys.platform
        self.plugins = self.load_plugins()

    def load_plugins(self) :
        plugin_folder = "./plugins"
        plugins = []
        possible_plugins = os.listdir(plugin_folder)

        print("load plugins...")

        for f in possible_plugins : 
            location = os.path.join(plugin_folder,f)

            if f[-3:] != '.py' or os.path.isfile(location) != True:
                continue

            info = imp.find_module(f[:-3],[plugin_folder])
            p = imp.load_module(location, *info)
            plugins.append(p)

        print("plugins:")
        print(plugins)
        return plugins

    def osx_networks(self):
        print("scanning osx networks...")

        scan = ""
        while scan == "":  # for some reason airport fails randomly
            scan = subprocess.check_output([self.airport, "scan"]).decode()
            # scan the area for wifi
        scan = scan.encode('ascii','ignore')
        scan = scan.decode().split("\n")

        print("found scan")
        print(scan)

        for wifi in scan:
            print("wifi: ")
            print(wifi)
            obj = unicode.split(wifi)

            if len(obj) > 0:
                yield obj

    def linux_networks(self):
        scan = Cell.all(self.iface)
        for wifi in scan:
            obj = [wifi.ssid, wifi.address, wifi.signal, wifi.channel, wifi]
            yield obj

    def scan_network(self):
        print("scanning...")

        if self.os == "linux" or self.os == "linux2":
            scanner = self.linux_networks()
        elif self.os == "darwin":
            scanner = self.osx_networks()
        # elif os == "win32": TODO

        results = []
        for wifi in scanner:
            if self.verbosity > 1:
                print(wifi)

            # match SSID/MAC to a plugin

            for p in self.plugins : 
                if p.is_vuln(wifi[0],wifi[1]) : 
                    results.append(p.own(wifi[0],wifi[1]))

        return results

    def connect_net(self, wifi):
        if self.os == "linux" or self.os == "linux2":
            status = self.connect_net_linux(wifi)
        elif self.os == "darwin":
            status = self.connect_net_osx(wifi)
        # elif os == "win32":

        return status

    def connect_net_osx(self, wifi):
            connect = subprocess.check_output([
                "networksetup", "-setairportnetwork",
                self.iface, wifi['ssid'], wifi['wifi_password']
            ]).decode()

            if self.verbosity > 0:
                print(connect)

            return "Failed" not in connect

    def connect_net_linux(self, wifi):
        return Scheme.find(self.iface, wifi[1]).activate()

    def own(self):
        print("own....")
        wifi_available = self.scan_network()

        print(wifi_available)

        if len(wifi_available) == 0:
            print("No WiFi available :'(")
        else:
            connected = False
            for wifi in wifi_available:
                print("WI-FI: " + wifi["ssid"])
                print("Password: " + wifi["wifi_password"])
                if self.verbosity > 0:
                    if wifi["admin_login"] and wifi["admin_password"] : 
                        print("Admin credentials of the router: ")
                        print("User: " + wifi["admin_login"])
                        print("Password: " + wifi["admin_password"])

                if not connected and self.connect:
                    print("Trying to connect...")
                    if self.connect_net(wifi):
                        print("Connected! Have fun (:")
                        connected = True
                    else:
                        print("Nope :(")


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument("-i", "--interface", default="wlp3s0",
                        help="Network interface.")
    parser.add_argument("-b", "--brute",action='store_true', default=False,
                        help="Enables bruteforce if needed it.")
    parser.add_argument("-c", "--connect", action="store_true", default=False,
                        help="Autoconnect to the first vulnerable network.")
    parser.add_argument("-a", "--airport", default=AIRPORT_PATH,
                        help="Airport program path.")
    parser.add_argument("-v", "--verbosity", action="count",
                        help="Increase output verbosity.")
    args = parser.parse_args()

    return args


def main():
    print("DPWO      v0.4")
    print("≈≈≈≈≈≈≈≈≈≈≈≈≈≈")

    args = parse_args()

    print(args)

    owner = NETOwner(
        args.interface,
        connect=args.connect,
        brute=args.brute,
        airport=args.airport,
        verbosity=args.verbosity or 0
    )

    owner.own()


if __name__ == "__main__":
    main()
