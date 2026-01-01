# Raspberry Pi Setup

## TODO

* [ ] HDMI Cables
* [ ] Reuse screenshot
* [ ] foo
* [ ] foo
* [ ] foo
* [ ] foo
* [ ] foo
* [ ] foo

## Kiosk Screens

1. Flash SD Crd
2. Boot Pi
3. Configure Pi
   1. Enable Auto Login: `sudo raspi-config` -> System Options -> S6 Auto Login -> Yes
   2. Configure locales: `sudo dpkg-reconfigure locales` -> Enable at least en_US.UTF-8
   3. Update package manager: `sudo apt update && sudo apt upgrade`
   4. Set larger swap: `sudo sed -i 's/#MaxSizeMiB=2048/MaxSizeMiB=4096/' /etc/rpi/swap.conf && sudo sed -i 's/#FixedSizeMiB=/FixedSizeMiB=4096/' /etc/rpi/swap.conf`
4. Install packages: `sudo apt install --no-install-recommends xserver-xorg x11-xserver-utils xinit openbox chromium`
5. Configure Autostart
   6. `nano ~/.bash_profile && chmod +x ~/.bash_profile`
   7. `sudo nano /etc/xdg/openbox/autostart`
8. Reboot: `sudo reboot`


sudo raspi-config && sudo dpkg-reconfigure locales && sudo apt update && sudo apt upgrade && \
sudo sed -i 's/#MaxSizeMiB=2048/MaxSizeMiB=4096/' /etc/rpi/swap.conf && sudo sed -i 's/#FixedSizeMiB=/FixedSizeMiB=4096/' /etc/rpi/swap.conf && \
sudo apt install --no-install-recommends xserver-xorg x11-xserver-utils xinit openbox chromium && \
nano ~/.bash_profile && chmod +x ~/.bash_profile && \
sudo nano /etc/xdg/openbox/autostart && \
sudo reboot

### Autostart Desktop (`/home/pi/.bash_profile`)

```
if [[ -z $DISPLAY && $XDG_VTNR -eq 1 ]]
then
  startx -- -nocursor
fi
```

### Autostart Script (`/etc/xdg/openbox/autostart`)

```
# Configuration
WEBSITE_URL="http://172.20.10.2/display/bloomberg"
# WEBSITE_URL="http://172.20.10.2/display/market-map"
# WEBSITE_URL="http://172.20.10.2/display/terminal"
# WEBSITE_URL="http://172.20.10.2/display/leaderboard"
# WEBSITE_URL="http://172.20.10.2/display/stock-chart"
# WEBSITE_URL="http://172.20.10.2/display/performance-race"
# WEBSITE_URL="http://172.20.10.2/display/ipo-spotlight"
# WEBSITE_URL="http://172.20.10.2/display/sector-sunburst"

# Disable screensaver, screen blanking, and power management
xset s off
xset s noblank
xset -dpms

# Force resolution
xrandr --display :0 --output HDMI-1 --mode "1280x720"

# Auto-detect screen resolution
RESOLUTION=$(xrandr 2>/dev/null | grep '*' | awk '{print $1}')
if [ -z "$RESOLUTION" ]; then
    RESOLUTION="1920x1080"  # Default fallback can be ="1280x720"
fi
SCREEN_WIDTH=$(echo $RESOLUTION | cut -d 'x' -f1)
SCREEN_HEIGHT=$(echo $RESOLUTION | cut -d 'x' -f2)

echo "Detected screen resolution: ${SCREEN_WIDTH}x${SCREEN_HEIGHT}"

# Check internet connection using ping before launching Chromium
if ping -c 1 -W 2 google.com >/dev/null 2>&1; then
    echo "Internet connected. Proceeding with Chromium launch."
else
    echo "No internet connection detected. Exiting."
fi

# Allow quitting the X server with CTRL-ALT-Backspace
# setxkbmap -option terminate:ctrl_alt_bksp

# Prevent Chromium restore prompts
sed -i 's/"exited_cleanly":false/"exited_cleanly":true/' ~/.config/chromium/'Local State'
sed -i 's/"exit_type":"[^"]\+"/"exit_type":"Normal"/' ~/.config/chromium/Default/Preferences

# Clean up Chromium cache, cookies, and logs
find ~/.config/chromium/Default/ -type f \( -name "Cookies" -o -name "History" -o -name "*.log" -o -name "*.ldb" -o -name "*.sqlite" \) -delete
rm -rf ~/.config/chromium/Default/Logs/*

# Clear system logs
sudo journalctl --vacuum-time=1d
sudo find /var/log -type f \( -name "*.log" -o -name "*.gz" -o -name "*.1" \) -delete
sudo truncate -s 0 /var/log/syslog /var/log/dmesg

# Kill any existing Chromium instances
pkill -9 chromium-browser 2>/dev/null
pkill -9 chromium 2>/dev/null
pkill -9 chrome 2>/dev/null

# Start Chromium in kiosk mode
chromium --no-memcheck --kiosk --disable-gpu --noerrdialogs --disable-infobars --disable-features=Translate,TranslateUI \
    --disable-session-crashed-bubble --no-sandbox --disable-notifications --disable-sync-preferences \
    --disable-background-mode --disable-popup-blocking --no-first-run \
    --enable-gpu-rasterization --disable-translate --disable-logging --disable-default-apps \
    --disable-extensions --disable-crash-reporter --disable-pdf-extension --disable-new-tab-first-run \
    --disable-dev-shm-usage --start-maximized --mute-audio --disable-crashpad --hide-scrollbars \
    --ash-hide-cursor --memory-pressure-off --force-device-scale-factor=1 --window-position=0,0 \
    --window-size=${SCREEN_WIDTH},${SCREEN_HEIGHT} "$WEBSITE_URL" &
    
# mpv mpv --no-cache http://local.srv.ag//api/screenshot/stream/leaderboard

if [ $? -eq 0 ]; then
    echo "Chromium started successfully."
else
    echo "Failed to start Chromium."
    sudo reboot
fi
```


### MISC

`xrandr --display :0`

#