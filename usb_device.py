"""
文件说明：USB2XXX设备操作相关函数集合
更多帮助：www.toomoss.com
使用说明：程序正常运行，需要将sdk/libs目录复制到程序目录下
"""

from ctypes import *
import platform
import os
import shutil

# Device info define
class DEVICE_INFO(Structure):
    _fields_ = [
        ("FirmwareName", c_char*32),   # firmware name string
        ("BuildDate", c_char*32),      # firmware build date and time string
        ("HardwareVersion", c_uint),   # hardware version
        ("FirmwareVersion",c_uint),    # firmware version
        ("SerialNumber",c_uint*3),     # USB2XXX serial number
        ("Functions",c_uint)           # USB2XXX functions
    ]

# 定义电压输出值
POWER_LEVEL_NONE    = 0 # 不输出
POWER_LEVEL_1V8     = 1 # 输出1.8V
POWER_LEVEL_2V5     = 2 # 输出2.5V
POWER_LEVEL_3V3     = 3 # 输出3.3V
POWER_LEVEL_5V0     = 4 # 输出5.0V

#复制库文件到程序目录下


#根据系统自动导入对应的库文件，若没能识别到正确的系统，可以修改下面的源码
if(platform.system()=="Windows"):
    if "64bit" in platform.architecture():
        windll.LoadLibrary(os.getcwd()+"/libs/windows/x86_64/libusb-1.0.dll" )
        USB2XXXLib = windll.LoadLibrary(os.getcwd()+"/libs/windows/x86_64/USB2XXX.dll" )
    else:
        windll.LoadLibrary(os.getcwd()+"/libs/windows/x86/libusb-1.0.dll" )
        USB2XXXLib = windll.LoadLibrary(os.getcwd()+"/libs/windows/x86/USB2XXX.dll" )
elif(platform.system()=="Darwin"):
    cdll.LoadLibrary(os.getcwd()+"/libs/mac_os/libusb-1.0.dylib" )
    USB2XXXLib = cdll.LoadLibrary(os.getcwd()+"/libs/mac_os/libUSB2XXX.dylib" )
elif(platform.system()=="Linux"):
    if 'armv7' in platform.machine():
        cdll.LoadLibrary(os.getcwd()+"/libs/linux/armv7/libusb-1.0.so" )
        USB2XXXLib = cdll.LoadLibrary(os.getcwd()+"/libs/linux/armv7/libUSB2XXX.so" )
    elif 'mips64' in platform.machine():
        cdll.LoadLibrary(os.getcwd()+"/libs/linux/mips64/libusb-1.0.so" )
        USB2XXXLib = cdll.LoadLibrary(os.getcwd()+"/libs/linux/mips64/libUSB2XXX.so" )
    elif 'aarch64' in platform.machine():
        cdll.LoadLibrary(os.getcwd()+"/libs/linux/aarch64/libusb-1.0.so" )
        USB2XXXLib = cdll.LoadLibrary(os.getcwd()+"/libs/linux/aarch64/libUSB2XXX.so" )
    elif 'arm64' in platform.machine():
        cdll.LoadLibrary(os.getcwd()+"/libs/linux/arm64/libusb-1.0.so" )
        USB2XXXLib = cdll.LoadLibrary(os.getcwd()+"/libs/linux/arm64/libUSB2XXX.so" )
    else:
        if "64bit" in platform.architecture():
            cdll.LoadLibrary(os.getcwd()+"/libs/linux/x86_64/libusb-1.0.so" )
            USB2XXXLib = cdll.LoadLibrary(os.getcwd()+"/lib/linux/x86_64/libUSB2XXX.so" )
        else:
            cdll.LoadLibrary(os.getcwd()+"/libs/linux/x86/libusb-1.0.so" )
            USB2XXXLib = cdll.LoadLibrary(os.getcwd()+"/libs/linux/x86/libUSB2XXX.so" )
else:
    print("unsupported system")
    exit()

# Scan device
def USB_ScanDevice(pDevHandle):
    return USB2XXXLib.USB_ScanDevice(pDevHandle)

# Open device
def USB_OpenDevice(DevHandle):
    return USB2XXXLib.USB_OpenDevice(DevHandle)

# Reset device
def USB_ResetDevice(DevHandle):
    return USB2XXXLib.USB_ResetDevice(DevHandle)

# Get USB2XXX infomation
def DEV_GetDeviceInfo(DevHandle, pDevInfo, pFunctionStr):
    return USB2XXXLib.DEV_GetDeviceInfo(DevHandle, pDevInfo, pFunctionStr)

# Close device
def USB_CloseDevice(DevHandle):
    return USB2XXXLib.USB_CloseDevice(DevHandle)

def DEV_EraseUserData(DevHandle):
    return USB2XXXLib.DEV_EraseUserData(DevHandle)

def DEV_WriteUserData(DevHandle,OffsetAddr,pWriteData,DataLen):
    return USB2XXXLib.DEV_WriteUserData(DevHandle,OffsetAddr,pWriteData,DataLen)

def DEV_ReadUserData(DevHandle,OffsetAddr,pReadData,DataLen):
    return USB2XXXLib.DEV_ReadUserData(DevHandle,OffsetAddr,pReadData,DataLen)

def DEV_SetPowerLevel(DevHandle,PowerLevel):
    return USB2XXXLib.DEV_SetPowerLevel(DevHandle,PowerLevel)

def DEV_GetTimestamp(DevHandle,BusType,pTimestamp):
    return USB2XXXLib.DEV_GetTimestamp(DevHandle,BusType,pTimestamp)


