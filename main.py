import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, scrolledtext
import json
import logging
from netmiko import ConnectHandler
import threading
import time
from datetime import datetime, timedelta

logging.basicConfig(filename='logging.log', level=logging.INFO, 
                    format='%(asctime)s:%(levelname)s:%(message)s')

class AddDeviceDialog(simpledialog.Dialog):
    def body(self, master):
        self.title('Switch Ekle')
        tk.Label(master, text="Cihaz Tipi:").grid(row=0)
        tk.Label(master, text="Host:").grid(row=1)
        tk.Label(master, text="Kullanıcı Adı:").grid(row=2)
        tk.Label(master, text="Şifre:").grid(row=3)

        self.device_types = [
            "a10", "accedian", "adtran_os", "adva_fsp150f2", "adva_fsp150f3", "alcatel_aos", "alcatel_sros", "allied_telesis_awplus", "apresia_aeos", "arista_eos", "arris_cer", "aruba_os", "aruba_osswitch", "aruba_procurve", "audiocode_66", "audiocode_72", "audiocode_shell", "avaya_ers", "avaya_vsp", "broadcom_icos", "brocade_fastiron", "brocade_fos", "brocade_netiron", "brocade_nos", "brocade_vdx", "brocade_vyos", "calix_b6", "casa_cmts", "cdot_cros", "centec_os", "checkpoint_gaia", "ciena_saos", "cisco_asa", "cisco_ftd", "cisco_ios", "cisco_nxos", "cisco_s200", "cisco_s300", "cisco_tp", "cisco_viptela", "cisco_wlc", "cisco_xe", "cisco_xr", "cloudgenix_ion", "coriant", "dell_dnos9", "dell_force10", "dell_isilon", "dell_os10", "dell_os6", "dell_os9", "dell_powerconnect", "dell_sonic", "digi_transport", "dlink_ds", "eltex", "eltex_esr", "endace", "enterasys", "ericsson_ipos", "ericsson_mltn63", "ericsson_mltn66", "extreme", "extreme_ers", "extreme_exos", "extreme_netiron", "extreme_nos", "extreme_slx", "extreme_tierra", "extreme_vdx", "extreme_vsp", "extreme_wing", "f5_linux", "f5_ltm", "f5_tmsh", "fiberstore_fsos", "flexvnf", "fortinet", "generic", "generic_termserver", "hillstone_stoneos", "hp_comware", "hp_procurve", "huawei", "huawei_olt", "huawei_smartax", "huawei_vrp", "huawei_vrpv8", "ipinfusion_ocnos", "juniper", "juniper_junos", "juniper_screenos", "keymile", "keymile_nos", "linux", "maipu", "mellanox", "mellanox_mlnxos", "mikrotik_routeros", "mikrotik_switchos", "mrv_lx", "mrv_optiswitch", "netapp_cdot", "netgear_prosafe", "netscaler", "nokia_srl", "nokia_sros", "oneaccess_oneos", "ovs_linux", "paloalto_panos", "pluribus", "quanta_mesh", "rad_etx", "raisecom_roap", "ruckus_fastiron", "ruijie_os", "sixwind_os", "sophos_sfos", "supermicro_smis", "teldat_cit", "tplink_jetstream", "ubiquiti_edge", "ubiquiti_edgerouter", "ubiquiti_edgeswitch", "ubiquiti_unifiswitch", "vyatta_vyos", "vyos", "watchguard_fireware", "yamaha", "zte_zxros", "zyxel_os",
        ]

        self.device_type_entry = ttk.Combobox(master, values=self.device_types, state="readonly")
        self.device_type_entry.grid(row=0, column=1)
        self.host_entry = tk.Entry(master)
        self.host_entry.grid(row=1, column=1)
        self.username_entry = tk.Entry(master)
        self.username_entry.grid(row=2, column=1)
        self.password_entry = tk.Entry(master)
        self.password_entry.grid(row=3, column=1)

        return self.device_type_entry

    def apply(self):
        device_type = self.device_type_entry.get()
        host = self.host_entry.get()
        username = self.username_entry.get()
        password = self.password_entry.get()
        self.result = {'device_type': device_type, 'host': host, 'username': username, 'password': password}




class DeviceManagerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Switch AutoSSH')
        self.geometry('1300x600')
        self.is_checking = False
        
        self.log_text = scrolledtext.ScrolledText(self, state='disabled', height=10)
        self.log_text.pack(fill=tk.BOTH, expand=True, side=tk.BOTTOM)

        self.tree = ttk.Treeview(self, columns=('Host', 'Type', 'Username', 'Password'), show='headings')
        self.tree.heading('Host', text='Host')
        self.tree.heading('Type', text='Cihaz Tipi')
        self.tree.heading('Username', text='SSH Kullanıcı Adı')
        self.tree.heading('Password', text='SSH Şifresi')
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.load_devices_button = tk.Button(self, text='Switch Listesini Yenile', command=self.load_devices)
        self.load_devices_button.pack(side=tk.LEFT)

        self.add_device_button = tk.Button(self, text='Switch Ekle', command=self.add_device)
        self.add_device_button.pack(side=tk.LEFT)

        self.remove_device_button = tk.Button(self, text='Seçilen Switch Kaldır', command=self.remove_device)
        self.remove_device_button.pack(side=tk.LEFT)
        
        self.show_password_button = tk.Button(self, text='Şifreleri Göster/Gizle', command=self.toggle_passwords)
        self.show_password_button.pack(side=tk.LEFT)
        
        self.interval_hours = tk.Label(self, text="Döngü Süresi (saat):")
        self.interval_hours.pack(side=tk.LEFT)
        
        self.interval_entry = tk.Entry(self)
        self.interval_entry.pack(side=tk.LEFT)
        self.interval_entry.insert(0, "5")
        
        self.start_checking_button = tk.Button(self, text="Başlat", command=self.start_checking, bg='green', activebackground='light green')
        self.start_checking_button.pack(side=tk.LEFT)
        
        self.progress_label = tk.Label(self, text="0/0 cihaz tamamlandı (%0)")
        self.progress_label.pack(side=tk.LEFT)
        self.progress = ttk.Progressbar(self, orient='horizontal', length=200, mode='determinate')
        self.progress.pack(side=tk.LEFT)
        
        self.remaining_time_label = tk.Label(self, text="Bir sonraki kontrol: Bekleniyor...")
        self.remaining_time_label.pack(side=tk.LEFT)


        self.passwords_visible = False

        self.devices = []
        self.load_devices()


    def toggle_passwords(self):
        self.passwords_visible = not self.passwords_visible
        for i, device in enumerate(self.devices):
            password = device['password'] if self.passwords_visible else '*' * len(device['password'])
            self.tree.item(self.tree.get_children()[i], values=(device['host'], device['device_type'], device['username'], password))

    def update_treeview(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for device in self.devices:
            password = device['password'] if self.passwords_visible else '*' * len(device['password'])
            self.tree.insert('', tk.END, values=(device['host'], device['device_type'], device['username'], password))

    def load_devices(self):
        try:
            with open('devices.json', 'r') as file:
                self.devices = json.load(file)
        except FileNotFoundError:
            self.devices = []
        self.update_treeview()

    def save_devices(self):
        with open('devices.json', 'w') as file:
            json.dump(self.devices, file, indent=4)

    def add_device(self):
        dialog = AddDeviceDialog(self)
        if dialog.result:
            new_device = dialog.result
            if all(new_device.values()):  # Tüm değerler doluysa
                self.devices.append(new_device)
                self.update_treeview()
                self.save_devices()
            else:
                messagebox.showwarning("Uyarı", "Tüm alanları doldurun.")

    def remove_device(self):
        selected_items = self.tree.selection()
        if selected_items:
            devices_to_remove = []
            for selected_item in selected_items:
                device_host = self.tree.item(selected_item)['values'][0]  # Host değerini al
                for device in self.devices:
                    if device['host'] == device_host:
                        devices_to_remove.append(device)
                        break
                    
            for device in devices_to_remove:
                self.devices.remove(device)
                for selected_item in selected_items:
                    if self.tree.item(selected_item)['values'][0] == device['host']:
                        self.tree.delete(selected_item)
                        break

            self.save_devices()
        else:
            messagebox.showerror("Hata", "Bir switch seçilmedi.")

            
    def start_checking(self):
        self.start_checking_button.config(state=tk.DISABLED, bg='grey')
        interval_hours = self.interval_entry.get()

        try:
            interval_seconds = float(interval_hours) * 3600
            self.next_check_time = datetime.now() + timedelta(seconds=interval_seconds)
            self.update_remaining_time()

            thread = threading.Thread(target=self.check_devices_periodically, args=(interval_seconds,), daemon=True)
            thread.start()

            start_message = f"Döngü süresi {interval_hours} saat olarak ayarlandı. Cihaz bağlantıları başlatılıyor..."
            self.log_message(start_message)

        except ValueError:
            messagebox.showerror("Hata", "Geçersiz döngü süresi.")
            self.start_checking_button.config(state=tk.NORMAL, bg='green')

    def check_devices_periodically(self, interval_seconds):
        self.check_devices()
        self.next_check_time = datetime.now() + timedelta(seconds=interval_seconds)
        self.after(1000, self.update_remaining_time)

    def update_remaining_time(self):
        now = datetime.now()
        if now < self.next_check_time:
            remaining_seconds = int((self.next_check_time - now).total_seconds())
            self.remaining_time_label.config(text=f"Bir sonraki kontrol: {remaining_seconds} saniye sonra")
            self.after(1000, self.update_remaining_time)
        else:
            self.remaining_time_label.config(text="Kontrol başlıyor...")
            self.start_checking()

    def check_devices(self):
        total_devices = len(self.devices)
        completed_devices = 0

        for index, device in enumerate(self.devices, start=1):
            message = f"{device['host']} cihazına bağlanılıyor..."
            self.log_message(message)
            try:
                net_connect = ConnectHandler(**device)
                net_connect.disconnect()
                message = f"{device['host']} cihazına başarılı bir şekilde bağlanıldı."
                completed_devices += 1
            except Exception as e:
                message = f"{device['host']} cihazına bağlanırken hata oluştu: {str(e)}"
                completed_devices += 1
            finally:
                self.update_progress(completed_devices, total_devices)
    
            self.after(0, self.update_progress, completed_devices, len(self.devices))
            self.log_message(message)

    def update_progress(self, completed, total):
        # İlerleme çubuğunu ve etiketi güncelle
        self.progress['value'] = completed / total * 100
        self.progress_label.config(text=f"{completed}/{total} cihaz tamamlandı (%{int((completed / total) * 100)})")
        self.update_idletasks()  # GUI güncelle

    def log_message(self, message):
        current_time = datetime.now().strftime("%H:%M:%S %d-%m-%Y")
        formatted_message = f"{current_time} - {message}"
        self.log_text.configure(state='normal')
        self.log_text.insert(tk.END, formatted_message + "\n")
        self.log_text.configure(state='disabled')
        self.log_text.yview(tk.END)
                
if __name__ == "__main__":
    app = DeviceManagerApp()
    app.mainloop()
