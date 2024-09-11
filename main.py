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
    ret = LIN_Write(DevHandles[0],LINMasterIndex,byref(LINMsg),1)
    if ret != LIN_SUCCESS:
        print("LIN ID[0x%02X] write data failed!"%LINMsg.ID)
        sys.exit(app.exec_())
    else:
        print("M2S","[0x%02X] "%LINMsg.ID,end='')
        for i in range(LINMsg.DataLen):
            print("0x%02X "%LINMsg.Data[i],end='')
        print("")
    sleep(0.01)
    ClearCache()
    # print(formatted_words)
    # print("写入成功!",words)

#读数据 
def ReadMessage():
    global first_message  # 全局变量存储首次ASCII码
    LINMsg = LIN_MSG()
    ID = ui.lineEdit_3.text()
    LINMsg.ID = int(ID, 16)
    LINMsg.DataLen = 8
    ret = LIN_Read(DevHandles[0],LINMasterIndex,byref(LINMsg),1)
    if ret != LIN_SUCCESS:
        print("LIN ID[0x%02X] read data failed!" % LINMsg.ID)
        # 显示错误信息给用户，‌而不是退出程序
        ui.textEdit_2.setText("Error reading LIN data.")
    else:
        message= ""
        for i in range(LINMsg.DataLen-1):
            message += "0x%02X"%LINMsg.Data[i]
            message += " "
        print("S2M [0x%02X]"%LINMsg.ID,message)
        display_message = " ".join(["%02X" % byte for byte in LINMsg.Data[:LINMsg.DataLen-1]])
        if 'first_message' not in globals():
            first_message = display_message
        else:
            first_message += display_message  # 合并ASCII码
            first_message += " "
        ui.textEdit_2.setText(first_message)  # 更新UI显示合并后的ASCII码

def Old_Version():
    ASCllLen=len(first_message)
    if ASCllLen == 48:
        message_str1=first_message[18:24]
        message_str2=first_message[30:38]
        message_str=message_str1+message_str2
        ascll_message = ''.join([chr(int(byte, 16)) for byte in message_str.split()[:ASCllLen]])
        ui.lineEdit_5.setText(ascll_message)
        print("SW:",ascll_message)
    elif ASCllLen == 24:
        message_str=first_message[15:23]
        ascll_message = ''.join([chr(int(byte, 16)) for byte in message_str.split()[:ASCllLen]])
        ui.lineEdit_6.setText(ascll_message)
        print("HW:",ascll_message)

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

#打开文件夹
def OpenFileFolder(self):
    FileFolder=QFileDialog.getExistingDirectory(None,'选择文件夹','C:\\')
    ui.lineEdit.setText(FileFolder)
    print(FileFolder)

#打开文件
def OpenFile(self):
    Files,_ = QFileDialog.getOpenFileName(None, '打开列表文件', 'C:\\', 'LIN List File (*.bin);;MLX LIN List File (*.lin);;Any file (*)')
    ui.lineEdit.setText(Files)
    print(Files)

    file = QFile(Files)
    #读取文件
    if file.open(QIODevice.ReadOnly):
        array = file.readLine()
        hex_data = array.data().hex()   
        hex_newlines = '\n'.join([hex_data[i:i+32] for i in range(0, len(hex_data), 32)])  # 每32个字符后换行
        ui.textEdit.setText(hex_newlines)

        print(len(array.data()))
        file.close()
    else:
        print("未选择文件")


#写入文件
def writeFile():
    Files = ui.lineEdit.text()
    file = QFile(Files)
    if file.open(QIODevice.WriteOnly):
        text = ui.textEdit.toPlainText()
        file.write(text.encode('utf-8'))
        file.close()
        print("写入成功")


#关闭设备
def Close():
    ret = USB_CloseDevice(DevHandles[0])
    if(bool(ret)):
        print("Close device success!")
    else:
        print("Close device faild!")
    sys.exit(app.exec_())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    MainWindow = QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()

    LINMasterIndex = 0
    DevHandles = (c_uint * 20)()
    # Scan device
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
    ui.pushButton_2.clicked.connect(Close)
    ui.pushButton_4.clicked.connect(Old_Version)
    ui.pushButton_5.clicked.connect(New_Version)

    sys.exit(app.exec_())





    # def ReadMessage():
#     LINMsg = LIN_MSG()
#     ID=ui.lineEdit_3.text()
#     LINMsg.ID = int(ID,16)
#     LINMsg.DataLen = 8
#     ret = LIN_Read(DevHandles[0],LINMasterIndex,byref(LINMsg),1)
#     if ret != LIN_SUCCESS:
#         print("LIN ID[0x%02X] read data failed!"%LINMsg.ID)
#         sys.exit(app.exec_())
#     else:
#         message= ""
#         for i in range(LINMsg.DataLen-1):
#             message += "0x%02X"%LINMsg.Data[i]
#             message += " "
#         print("S2M [0x%02X]"%LINMsg.ID,message)

#         display_message = " ".join(["%02X" % byte for byte in LINMsg.Data[:LINMsg.DataLen-1]])
#         ui.textEdit_2.setText(display_message)
#         ascll_message = ''.join([chr(int(byte, 16)) for byte in display_message.split()[:LINMsg.DataLen]])
#         # 将ASCII码字符串显示或输出
#         print("ASCII Message:", ascll_message)
#         # 或者更新到UI组件中
#         #ui.textEdit_2.setText(ascii_message)
#     sleep(0.01)