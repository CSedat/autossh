# Switch AutoSSH

Desteklenen switchlere belirli bir süre ile otomatik SSH bağlantısı sağlayın.

[Netmiko](https://github.com/ktbyers/netmiko "Netmiko GitHub Sayfası") kütüphanesi kullanılarak geliştirilmiş ve çeşitli cihazları destekleyecek şekilde yapılandırılmıştır.

## Kurulum

Bu uygulamayı kullanabilmek için bilgisayarınızda Python'un yüklü olması gerekir.

```bash
git clone https://github.com/CSedat/autossh.git
cd autossh
pip install -r requirements.txt
pip install pyinstaller
python main.py

pyinstaller --onefile --windowed --icon=favicon.ico --name="Uygulama Çıktı Adı" main.py
