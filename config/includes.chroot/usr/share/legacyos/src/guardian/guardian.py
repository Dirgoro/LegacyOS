#!/usr/bin/env python3
import gi, psutil, subprocess
gi.require_version('Notify', '0.7')
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Notify, GLib

class LegacyGuardian:
    def __init__(self):
        try:
            Notify.init("Legacy Guardian")
        except Exception:
            pass
        GLib.timeout_add_seconds(60, self.run_checks)

    def run_checks(self):
        try:
            self.check_temperature()
            self.check_disk_space()
            self.check_time_sync()
        except Exception:
            pass
        return True

    def send_notification(self, title, message, urgency, icon="dialog-warning"):
        try:
            Notify.Notification.new(title, message, icon).show()
        except Exception:
            pass

    def check_temperature(self):
        try:
            temps = psutil.sensors_temperatures()
            if 'coretemp' in temps and temps['coretemp']:
                if temps['coretemp'][0].current > 80:
                    self.send_notification("Temperatura Elevada", "CPU acima de 80°C.", Notify.Urgency.CRITICAL)
        except Exception:
            pass

    def check_disk_space(self):
        try:
            if psutil.disk_usage('/').free / (1024**3) < 5.0:
                self.send_notification("Pouco espaço", "Restam menos de 5GB livres.", Notify.Urgency.NORMAL)
        except Exception:
            pass

    def check_time_sync(self):
        try:
            res = subprocess.run(['timedatectl', 'show', '--property=NTPSynchronized', '--value'], capture_output=True, text=True)
            if res.stdout.strip() == "no":
                self.send_notification("Relógio Dessincronizado", "Verifique a data e hora.", Notify.Urgency.NORMAL)
        except Exception:
            pass

if __name__ == "__main__":
    app = LegacyGuardian()
    Gtk.main()
