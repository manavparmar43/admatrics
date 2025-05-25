import platform
import subprocess
import requests
import getpass
import socket
import os


def get_ip_info():
    try:
        response = requests.get("https://ipinfo.io/json")
        data = response.json()
        return {
            "region": data.get("region"),
            "location": data.get("loc"),
            "city": data.get("city"),
            "country": data.get("country"),
            "ip": data.get("ip"),
        }
    except Exception as e:
        return {"error": str(e)}


def get_device_type():
    system = platform.system()
    if system == "Linux":
        if "ANDROID_ROOT" in os.environ:
            return "Mobile"
        return "Laptop"
    elif system in ["Windows", "Darwin"]:
        return "Laptop"
    else:
        return "Unknown"


def get_laptop_info():
    try:
        if platform.system() == "Windows":
            manufacturer = (
                subprocess.check_output(
                    "wmic computersystem get manufacturer", shell=True
                )
                .decode()
                .split("\n")[1]
                .strip()
            )
            model = (
                subprocess.check_output("wmic computersystem get model", shell=True)
                .decode()
                .split("\n")[1]
                .strip()
            )
            return manufacturer, model
        elif platform.system() == "Linux":
            with open("/sys/class/dmi/id/sys_vendor", "r") as f:
                manufacturer = f.read().strip()
            with open("/sys/class/dmi/id/product_name", "r") as f:
                model = f.read().strip()
            return manufacturer, model
        elif platform.system() == "Darwin":  # macOS
            manufacturer = "Apple"
            model = (
                subprocess.check_output(["sysctl", "-n", "hw.model"]).decode().strip()
            )
            return manufacturer, model
    except Exception:
        return None, None


def get_mobile_info():
    try:
        if "ANDROID_ROOT" in os.environ:
            manufacturer = (
                subprocess.check_output("getprop ro.product.manufacturer", shell=True)
                .decode()
                .strip()
            )
            model = (
                subprocess.check_output("getprop ro.product.model", shell=True)
                .decode()
                .strip()
            )
            return manufacturer, model
    except Exception:
        return None, None


def get_device_info():
    device_type = get_device_type()
    if device_type == "Laptop":
        company, model = get_laptop_info()
    elif device_type == "Mobile":
        company, model = get_mobile_info()
    else:
        company, model = None, None

    return {
        "device_type": device_type,
        "company": company,
        "model": model,
        "platform": platform.system(),
        "platform_release": platform.release(),
        "username": getpass.getuser(),
        "placement": socket.gethostname(),
    }


def get_current_info():
    ip_info = get_ip_info()
    device_info = get_device_info()

    result = {
        "region": ip_info.get("region"),
        "city": ip_info.get("city"),
        "country": ip_info.get("country"),
        "device_type": device_info.get("device_type"),
        "device_company": device_info.get("company"),
        "platform": device_info.get("platform"),
        "platform_hostname": device_info.get("placement"),
        "location": ip_info.get("loc"),
        "name": device_info.get("username"),
        "ip": ip_info.get("ip"),
    }

    return result


# # Run logic
