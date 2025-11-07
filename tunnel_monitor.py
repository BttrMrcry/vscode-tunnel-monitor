"""
VS Code Remote Tunnel Monitor
Monitors the VS Code tunnel service and displays status in system tray
"""
import subprocess
import json
import time
import threading
import logging
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw
import pystray
from pystray import MenuItem as item

# Configuration
CHECK_INTERVAL = 30  # seconds
RETRY_DELAY = 10  # seconds
MAX_RETRIES = 3
LOG_FILE = Path.home() / "tunnel_monitor.log"
CODE_CLI = Path.home() / "AppData" / "Local" / "Programs" / "Microsoft VS Code" / "bin" / "code.cmd"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

class TunnelMonitor:
    def __init__(self):
        self.is_running = False
        self.tunnel_connected = False
        self.tunnel_name = "Unknown"
        self.last_check_time = None
        self.icon = None
        self.monitoring_thread = None
        
    def create_icon_image(self, color):
        """Create a colored circle icon"""
        size = 64
        image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Draw outer circle (border)
        draw.ellipse([2, 2, size-2, size-2], fill=color, outline='white', width=2)
        
        # Add a small indicator dot
        if color == 'green':
            # Add checkmark effect
            draw.ellipse([size//2-4, size//2-4, size//2+4, size//2+4], fill='white')
        
        return image
    
    def check_tunnel_status(self):
        """Check if the tunnel is running and connected"""
        try:
            result = subprocess.run(
                [str(CODE_CLI), 'tunnel', 'status'],
                capture_output=True,
                text=True,
                timeout=10,
                shell=True
            )
            
            if result.returncode == 0:
                status_data = json.loads(result.stdout)
                tunnel_info = status_data.get('tunnel', {})
                
                is_connected = tunnel_info.get('tunnel') == 'Connected'
                tunnel_name = tunnel_info.get('name', 'Unknown')
                
                self.tunnel_connected = is_connected
                self.tunnel_name = tunnel_name
                self.last_check_time = datetime.now()
                
                if is_connected:
                    logging.info(f"Tunnel '{tunnel_name}' is connected")
                else:
                    logging.warning(f"Tunnel '{tunnel_name}' is not connected")
                
                return is_connected
            else:
                logging.error(f"Failed to check tunnel status: {result.stderr}")
                self.tunnel_connected = False
                return False
                
        except subprocess.TimeoutExpired:
            logging.error("Timeout checking tunnel status")
            self.tunnel_connected = False
            return False
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse tunnel status JSON: {e}")
            self.tunnel_connected = False
            return False
        except Exception as e:
            logging.error(f"Error checking tunnel status: {e}")
            self.tunnel_connected = False
            return False
    
    def restart_tunnel(self):
        """Attempt to restart the tunnel service"""
        logging.info("Attempting to restart tunnel...")
        
        try:
            # Try to restart the service
            result = subprocess.run(
                [str(CODE_CLI), 'tunnel', 'service', 'restart'],
                capture_output=True,
                text=True,
                timeout=30,
                shell=True
            )
            
            if result.returncode == 0:
                logging.info("Tunnel service restart command executed")
                time.sleep(5)  # Wait for service to start
                return self.check_tunnel_status()
            else:
                logging.error(f"Failed to restart tunnel: {result.stderr}")
                return False
                
        except Exception as e:
            logging.error(f"Error restarting tunnel: {e}")
            return False
    
    def monitoring_loop(self):
        """Main monitoring loop"""
        retry_count = 0
        
        while self.is_running:
            try:
                is_connected = self.check_tunnel_status()
                
                if is_connected:
                    retry_count = 0
                    self.update_icon('green')
                else:
                    self.update_icon('red')
                    
                    if retry_count < MAX_RETRIES:
                        logging.warning(f"Tunnel disconnected. Attempting restart (attempt {retry_count + 1}/{MAX_RETRIES})")
                        if self.restart_tunnel():
                            logging.info("Tunnel successfully restarted")
                            retry_count = 0
                        else:
                            retry_count += 1
                            time.sleep(RETRY_DELAY)
                    else:
                        logging.error(f"Failed to restart tunnel after {MAX_RETRIES} attempts")
                        time.sleep(CHECK_INTERVAL)
                
                time.sleep(CHECK_INTERVAL)
                
            except Exception as e:
                logging.error(f"Error in monitoring loop: {e}")
                time.sleep(CHECK_INTERVAL)
    
    def update_icon(self, color):
        """Update the system tray icon color"""
        if self.icon:
            self.icon.icon = self.create_icon_image(color)
    
    def get_status_text(self):
        """Get status text for tooltip"""
        if self.tunnel_connected:
            status = f"✓ Connected\nTunnel: {self.tunnel_name}"
        else:
            status = "✗ Disconnected"
        
        if self.last_check_time:
            status += f"\nLast check: {self.last_check_time.strftime('%H:%M:%S')}"
        
        return status
    
    def on_clicked(self, icon, item):
        """Handle icon click - show status"""
        icon.notify(self.get_status_text(), "Tunnel Monitor")
    
    def on_check_now(self, icon, item):
        """Manually trigger a status check"""
        threading.Thread(target=self.check_tunnel_status, daemon=True).start()
        icon.notify("Checking tunnel status...", "Tunnel Monitor")
    
    def on_restart(self, icon, item):
        """Manually restart the tunnel"""
        def restart():
            icon.notify("Restarting tunnel...", "Tunnel Monitor")
            if self.restart_tunnel():
                icon.notify("Tunnel restarted successfully", "Tunnel Monitor")
            else:
                icon.notify("Failed to restart tunnel", "Tunnel Monitor")
        
        threading.Thread(target=restart, daemon=True).start()
    
    def on_view_logs(self, icon, item):
        """Open log file"""
        try:
            subprocess.run(['notepad', str(LOG_FILE)])
        except Exception as e:
            logging.error(f"Failed to open log file: {e}")
    
    def on_quit(self, icon, item):
        """Quit the application"""
        logging.info("Tunnel monitor stopping...")
        self.is_running = False
        icon.stop()
    
    def start(self):
        """Start the monitor"""
        self.is_running = True
        
        # Initial status check
        self.check_tunnel_status()
        
        # Start monitoring thread
        self.monitoring_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        # Create system tray icon
        icon_color = 'green' if self.tunnel_connected else 'red'
        menu = pystray.Menu(
            item('Status', self.on_clicked, default=True),
            item('Check Now', self.on_check_now),
            item('Restart Tunnel', self.on_restart),
            pystray.Menu.SEPARATOR,
            item('View Logs', self.on_view_logs),
            pystray.Menu.SEPARATOR,
            item('Exit', self.on_quit)
        )
        
        self.icon = pystray.Icon(
            "tunnel_monitor",
            self.create_icon_image(icon_color),
            "VS Code Tunnel Monitor",
            menu
        )
        
        logging.info("Tunnel monitor started")
        
        # Run the icon (this blocks)
        self.icon.run()

if __name__ == '__main__':
    logging.info("=" * 50)
    logging.info("VS Code Tunnel Monitor starting...")
    logging.info(f"Log file: {LOG_FILE}")
    logging.info("=" * 50)
    
    monitor = TunnelMonitor()
    try:
        monitor.start()
    except KeyboardInterrupt:
        logging.info("Received keyboard interrupt")
    except Exception as e:
        logging.error(f"Fatal error: {e}", exc_info=True)
    finally:
        logging.info("Tunnel monitor stopped")
