import os
import sys
import subprocess
import tempfile
import socket
import time

def torcheck1(host='127.0.0.1', port=9150, timeout=1):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, port))
        s.close()
        return True
    except (socket.error, ConnectionRefusedError):
        return False

def torshell1():
    current_os = sys.platform
    is_windows = current_os == "win32"
    
    tor_socks_port = "9150"
    
    tor_is_active = torcheck1(port=int(tor_socks_port))
    
    if not tor_is_active:
        print(f"[!] Tor Service NOT detected on 127.0.0.1:{tor_socks_port}")
        print("[*] Waiting for Tor Service to start... Press Ctrl+C to stop waiting.")
        
        while not tor_is_active:
            try:
                time.sleep(2)
                tor_is_active = torcheck1(port=int(tor_socks_port))
                if tor_is_active:
                    print("\n[+] Tor Service DETECTED. Proceeding to launch shell.")
                    break
            except KeyboardInterrupt:
                print("\n[*] Tor startup wait interrupted by user.")
                break

    proxy_settings = {
        "HTTP_PROXY": f"socks5h://127.0.0.1:{tor_socks_port}",
        "HTTPS_PROXY": f"socks5h://127.0.0.1:{tor_socks_port}",
        "ALL_PROXY": f"socks5h://127.0.0.1:{tor_socks_port}",
        "NO_PROXY": "localhost,127.0.0.1"
    }
    
    env = os.environ.copy()
    for key, value in proxy_settings.items():
        env[key.upper()] = value
        env[key.lower()] = value

    if not tor_is_active:
        print("[!] The launched shell WILL NOT route traffic through Tor.")
        print("[!] Network requests will likely fail unless Tor is started *after* launch.")
    else:
        print("[+] Tor Service DETECTED.")
        print("[*] Configuring environment for Tor proxy...")
        print(f"[+] Proxy set to socks5h://127.0.0.1:{tor_socks_port}")

    print("\n[*] Clearing screen in 3 seconds...")
    time.sleep(3)

    clear_command = 'cls' if is_windows else 'clear'
    os.system(clear_command)

    temp_script_path = None
    try:
        if is_windows:
            suffix = '.bat'
            shell_command = "cmd /K"
        else:
            suffix = '.sh'
            shell_command = "${SHELL:-/bin/bash}"

        with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as temp_file:
            temp_script_path = temp_file.name
            
            if tor_is_active:
                cmd_message = "echo All traffic will be routed through Tor."
            else:
                cmd_message = "echo [WARNING] Tor is NOT running. Traffic routing WILL FAIL."

            if is_windows:
                script_content = (
                    "@echo off\n"
                    "title Tor-Routed Terminal\n"
                    "echo.\n"
                    f"{cmd_message}\n"
                    "echo Type 'exit' to close this window.\n"
                    "echo.\n"
                    f"{shell_command}\n"
                )
            else:
                script_content = (
                    "#!/bin/bash\n"
                    "clear\n"
                    "echo\n"
                    f"{cmd_message}\n"
                    "echo Type 'exit' to close this terminal.\n"
                    "echo\n"
                    f"exec {shell_command}\n"
                )
                
            temp_file.write(script_content)

        if not is_windows:
            os.chmod(temp_script_path, 0o755)

        print("[*] Launching new shell window...")
        
        if is_windows:
            shell_path = os.environ.get("COMSPEC", "cmd.exe")
            subprocess.Popen([shell_path, '/C', temp_script_path], env=env)
        else:
            subprocess.Popen([temp_script_path], env=env)

        if tor_is_active:
            print("[+] New Tor shell launched successfully (Tor active).")
        else:
            print("[+] New shell launched (Tor inactive, see warning above).")

        if tor_is_active:
            print("[*] Monitoring Tor connection status...")
            tor_status = True
            
            while True:
                time.sleep(5)
                
                current_tor_running = torcheck1(port=int(tor_socks_port))
                
                if tor_status and not current_tor_running:
                    tor_status = False
                    print("")
                    print("[!] TOR CONNECTION LOST. TOR SERVICE HAS STOPPED RUNNING.")
                    print("[!] All further network traffic from the shell is now UNENCRYPTED.")
                    print("")
                    
                elif not tor_status and current_tor_running:
                    tor_status = True
                    print("")                    
                    print("[+] Tor connection re-established.")
                    print("")

    except Exception as e:
        print(f"[!] An unexpected error occurred: {e}")
    finally:
        if temp_script_path and os.path.exists(temp_script_path):
            time.sleep(1)
            os.remove(temp_script_path)

if __name__ == "__main__":
    torshell1()
