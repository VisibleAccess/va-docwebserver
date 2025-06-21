

class OPI_ZERO3:

    @classmethod
    def core_temp(cls, core_number):
        try:
            with open(f"/sys/devices/virtual/thermal/thermal_zone{core_number}/temp", "r") as f:
                temp = int(float(f.read())/100)
                return temp/10

        except Exception as e:
            return None


    @classmethod
    def uptime(cls):
        try:
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = int(float(f.readline().split()[0]))
            return uptime_seconds

        except Exception as e:
            return None