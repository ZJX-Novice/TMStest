from TMS import Ui_MainWindow
from PyQt5.QtWidgets import QApplication,QMainWindow
from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtWidgets import *
from PyQt5.Qt import QFile, QTextStream
from PyQt5.Qt import *
from PyQt5.QtCore import QDataStream, QFile, QIODevice
import sys
from ctypes import *
import platform
import sys
from time import sleep
from usb_device import *
from usb2lin import *
import threading

#清除缓存
def ClearCache():
    global first_message
    first_message = ""  # 重置全局变量
    ui.textEdit_2.setText("")  # 清除文本框显示
#写数据
def WriteMessage():
    LINMsg = LIN_MSG()
    ID=ui.lineEdit_2.text()
    LINMsg.ID = int(ID,16)  #将文本框中获取的内容转换为16进制
    LINMsg.DataLen = 8
    message=ui.lineEdit.text() 
    ui.textEdit.setText(message) #将数据显示在文本框中
    words = message.split()
    formatted_words = ['0x' + word for word in words]  #对每个切片数据前加入'0x'
    for i in range(0,LINMsg.DataLen):
        LINMsg.Data[i] = int(formatted_words[i],16)
    # 发送LIN帧
    # i = 1
    # while i < 10:  # 无限循环发送帧，直到手动停止
    #     ret = LIN_Write(DevHandles[0], LINMasterIndex, byref(LINMsg), 1)
    #     if ret != LIN_SUCCESS:
    #         print(f"LIN ID[0x{LINMsg.ID:02X}] write data failed!")
    #         sys.exit(app.exec_())
    #     else:
    #         print("M2S", f"[0x{LINMsg.ID:02X}] ", end='')
    #         for i in range(LINMsg.DataLen):
    #             print(f"0x{LINMsg.Data[i]:02X} ", end='')
    #         print("")
    #     # 延时控制周期
    #     sleep(100 / 1000.0)  # 将毫秒转换为秒延时
    #      # 清理缓存
    #     ClearCache()
    #     ReadMessage()
    #     i = i + 1
    ret = LIN_Write(DevHandles[0],LINMasterIndex,byref(LINMsg),1)
    if ret != LIN_SUCCESS:
        print("LIN ID[0x%02X] write data failed!"%LINMsg.ID)
        ui.textEdit.setText("LIN ID[0x%02X] read data failed!"%LINMsg.ID)
    else:
        print("M2S","[0x%02X] "%LINMsg.ID,end='')
        for i in range(LINMsg.DataLen):
            print("0x%02X "%LINMsg.Data[i],end='')
        print("")
    sleep(1)
    ClearCache()


# 读数据
def ReadMessage():
    global global_message  # 全局变量存储首次ASCII码
    LINMsg = LIN_MSG()
    ID = ui.lineEdit_3.text()
    LINMsg.ID = int(ID, 16)
    LINMsg.DataLen = 8
    ret = LIN_Read(DevHandles[0],LINMasterIndex,byref(LINMsg),1)
    if ret != LIN_SUCCESS:
        print("LIN ID[0x%02X] read data failed!"%LINMsg.ID)
        # 显示错误信息给用户，‌而不是退出程序
        ui.textEdit_2.setText("LIN ID[0x%02X] read data failed!"%LINMsg.ID)
        return None
    else:
        message= ""
        for i in range(LINMsg.DataLen-1):
            message += "0x%02X"%LINMsg.Data[i]
            message += " "
        print("S2M [0x%02X]"%LINMsg.ID,message)
        display_message = " ".join(["%02X" % byte for byte in LINMsg.Data[:LINMsg.DataLen-1]])
        ui.textEdit_2.setText(display_message)
        # if 'first_message' not in globals():
        #     first_message = display_message
        # else:
        #     first_message += display_message  # 合并ASCII码
        #     first_message += " "
        # ui.textEdit_2.setText(first_message)  # 更新UI显示合并后的ASCII码
        return display_message

# 旧版本读取
def Old_Version():
    LINMsg = LIN_MSG()
    LINMsg.ID = 0x3C
    LINMsg.DataLen = 8
    
    # 发送并读取软硬件版本号
    write_message = [
        "7F 03 22 A6 34 FF FF FF",  # 软件版本号请求
        "7F 03 22 A6 35 FF FF FF"   # 硬件版本号请求
    ]
    
    for index, word in enumerate(write_message):
        # 准备并发送请求报文
        wd = word.split(' ')
        formatted_words = ['0x' + w for w in wd]
        for i in range(LINMsg.DataLen):
            LINMsg.Data[i] = int(formatted_words[i], 16)  
        ret = LIN_Write(DevHandles[0], LINMasterIndex, byref(LINMsg), 1)
        if ret != LIN_SUCCESS:
            print("LIN write data failed!")
            return
        else:
            print("M2S", "[0x%02X] " % LINMsg.ID, end='')
            for i in range(LINMsg.DataLen):
                print("0x%02X " % LINMsg.Data[i], end='')
            print("") 
        sleep(0.01)  # 等待设备响应

        # 开始读取响应
        LINMsg.ID = 0x3D
        full_response = ""
        flag = True
        while flag :
            ret = LIN_Read(DevHandles[0], LINMasterIndex, byref(LINMsg), 1)
            if ret != LIN_SUCCESS:
                print("LIN read data failed!")
                ui.textEdit_2.setText("LIN read data failed!")
            # 处理接收到的帧数据
            message = " ".join("0x%02X" % LINMsg.Data[i] for i in range(LINMsg.DataLen - 1))
            print("S2M [0x%02X] %s" % (LINMsg.ID, message.strip()))   

            # 累积响应数据
            display_message = " ".join(["%02X" % byte for byte in LINMsg.Data[:LINMsg.DataLen - 1]])
            full_response += display_message + " "
        
            # 判断帧类型
            get_type = '0x{:02X}'.format(int(get_frame(display_message, 1),16))  # 帧类型通常是第二个字节
            print("帧类型: ", get_type)

            if get_type == '0x10':  # 首帧
                print("读取到首帧")
                while True:
                    #持续读取
                    ret = LIN_Read(DevHandles[0], LINMasterIndex, byref(LINMsg), 1)
                    message = " ".join("0x%02X" % LINMsg.Data[i] for i in range(LINMsg.DataLen - 1))
                    print("S2M [0x%02X] %s" % (LINMsg.ID, message.strip()))
                    get_type = '0x{:02X}'.format(int(get_frame(message, 1),16))  # 帧类型通常是第二个字节
                    print("帧类型: ", get_type)
                    if '0x20' <= get_type <= '0x2F':  # 续帧
                        print("读取到续帧，继续读取")
                        ret = LIN_Read(DevHandles[0], LINMasterIndex, byref(LINMsg), 1)
                        message = " ".join("0x%02X" % LINMsg.Data[i] for i in range(LINMsg.DataLen - 1))
                        print("S2M [0x%02X] %s" % (LINMsg.ID, message.strip()))
                        if message == '':
                            break
                        else:
                            get_type = '0x{:02X}'.format(int(get_frame(message, 1),16))
                            print("帧类型:", get_type)
                    else:
                        print ("读取完成")
                        flag = False
                        #break
            else:  #读取到单帧
                print("读取到单帧")
                ret = LIN_Read(DevHandles[0], LINMasterIndex, byref(LINMsg), 1)
                message = " ".join("0x%02X" % LINMsg.Data[i] for i in range(LINMsg.DataLen - 1))
                print("S2M [0x%02X] %s" % (LINMsg.ID, message.strip()))
                flag = False

        # 根据索引处理软件版本和硬件版本
        if index == 0:  # 软件版本
            message_str1 = full_response[18:24]
            message_str2 = full_response[30:38]
            message_str = message_str1 + message_str2
            ascll_message = ''.join([chr(int(byte, 16)) for byte in message_str.split()])
            ui.lineEdit_5.setText(ascll_message)
            print("SW:", ascll_message)

        else:  # 硬件版本
            message_str = full_response[15:23]
            ascll_message = ''.join([chr(int(byte, 16)) for byte in message_str.split()])
            ui.lineEdit_6.setText(ascll_message)
            print("HW:", ascll_message)





    # ASCllLen=len(first_message)
    # if ASCllLen == 48:
    #     message_str1=first_message[18:24]
    #     message_str2=first_message[30:38]
    #     message_str=message_str1+message_str2
    #     ascll_message = ''.join([chr(int(byte, 16)) for byte in message_str.split()[:ASCllLen]])
    #     ui.lineEdit_5.setText(ascll_message)
    #     print("SW:",ascll_message)
    # elif ASCllLen == 24:
    #     message_str=first_message[15:23]
    #     ascll_message = ''.join([chr(int(byte, 16)) for byte in message_str.split()[:ASCllLen]])
    #     ui.lineEdit_6.setText(ascll_message)
    #     print("HW:",ascll_message)

# 新版本读取
def New_Version():
    ASCllLen=len(first_message)
    if ASCllLen == 48:
        message_str1=first_message[18:24]
        message_str2=first_message[30:38]
        message_str=message_str1+message_str2
        ascll_message = ''.join([chr(int(byte, 16)) for byte in message_str.split()[:ASCllLen]])
        ui.lineEdit_7.setText(ascll_message)
        print("SW:",ascll_message)
    elif ASCllLen == 24:
        message_str=first_message[15:23]
        ascll_message = ''.join([chr(int(byte, 16)) for byte in message_str.split()[:ASCllLen]])
        ui.lineEdit_8.setText(ascll_message)
        print("HW:",ascll_message)
# 获取指定位置的帧
def get_frame(words, index):
    words_split = words.split(' ')
    return words_split[index].replace('0x', '')

if __name__ == "__main__":
    app = QApplication(sys.argv)
    MainWindow = QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()

    LINMasterIndex = 0
    DevHandles = (c_uint * 20)()
    #Scan device
    ret = USB_ScanDevice(byref(DevHandles))
    if(ret == 0):
        print("No device connected!")
        sys.exit(app.exec_())
    else:
        print("Have %d device connected!"%ret)
    # Open device
    ret = USB_OpenDevice(DevHandles[0])
    if(bool(ret)):
        print("Open device success!")
    else:
        print("Open device faild!")
        sys.exit(app.exec_())
    # Get device infomation
    USB2XXXInfo = DEVICE_INFO()
    USB2XXXFunctionString = (c_char * 256)()
    ret = DEV_GetDeviceInfo(DevHandles[0],byref(USB2XXXInfo),byref(USB2XXXFunctionString))
    if(bool(ret)):
        print("USB2XXX device infomation:")
        print("--Firmware Name: %s"%bytes(USB2XXXInfo.FirmwareName).decode('ascii'))
        print("--Firmware Version: v%d.%d.%d"%((USB2XXXInfo.FirmwareVersion>>24)&0xFF,(USB2XXXInfo.FirmwareVersion>>16)&0xFF,USB2XXXInfo.FirmwareVersion&0xFFFF))
        print("--Hardware Version: v%d.%d.%d"%((USB2XXXInfo.HardwareVersion>>24)&0xFF,(USB2XXXInfo.HardwareVersion>>16)&0xFF,USB2XXXInfo.HardwareVersion&0xFFFF))
        print("--Build Date: %s"%bytes(USB2XXXInfo.BuildDate).decode('ascii'))
        print("--Serial Number: ",end='')
        for i in range(0, len(USB2XXXInfo.SerialNumber)):
            print("%08X"%USB2XXXInfo.SerialNumber[i],end='')
        print("")
        print("--Function String: %s"%bytes(USB2XXXFunctionString.value).decode('ascii'))
    else:
        print("Get device infomation faild!")
        sys.exit(app.exec_())

    # 初始化配置主LIN
    LINConfig = LIN_CONFIG()
    LINConfig.BaudRate = 19200
    LINConfig.BreakBits = LIN_BREAK_BITS_11
    LINConfig.CheckMode = LIN_CHECK_MODE_EXT
    LINConfig.MasterMode = LIN_MASTER
    ret = LIN_Init(DevHandles[0],LINMasterIndex,byref(LINConfig))
    if ret != LIN_SUCCESS:
        print("Config Master LIN failed!")
        sys.exit(app.exec_())
    else:
        print("Config Master LIN Success!")
    #发送BREAK信号，一般用于唤醒设备
    ret = LIN_SendBreak(DevHandles[0],LINMasterIndex)
    if ret != LIN_SUCCESS:
        print("Send LIN break failed!")
        sys.exit(app.exec_())
    else:
        print("Send LIN break success!")
    sleep(0.01)




    ui.pushButton.clicked.connect(WriteMessage)
    ui.pushButton_3.clicked.connect(ReadMessage)
    #ui.pushButton_2.clicked.connect(Close)
    ui.pushButton_4.clicked.connect(Old_Version)
    ui.pushButton_5.clicked.connect(New_Version)
    #ui.pushButton_6.clicked.connect(OpenFile)
    #ui.pushButton_7.clicked.connect(send_frame)

    sys.exit(app.exec_())
