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

finish_data = []

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


# 读数据
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


# 打开文件夹
def OpenFileFolder(self):
    FileFolder = QFileDialog.getExistingDirectory(None, '选择文件夹', 'C:\\')
    ui.lineEdit_9.setText(FileFolder)
    print(FileFolder)


# 打开文件
def OpenFile(self):

    Files, _ = QFileDialog.getOpenFileName(None, '打开列表文件', 'C:\\','LIN List File (*.bin);;MLX LIN List File (*.lin);;Any file (*)')
    ui.lineEdit_9.setText(Files)
    print(Files)

    file = QFile(Files)
    # 读取文件
    if file.open(QIODevice.ReadOnly):
        all_hex_data = []  # 用于存储所有行的原始十六进制数据
        change_hex_data = []     # 用于存储转换过后的数据
        while not file.atEnd():
            array = file.readLine()  # 逐行读取
            data = array.data()
            hex_data = array.data().hex()
            all_hex_data.append(hex_data)
            # 检测数据类型并进行处理
            processed_data = ''
            for byte in data:
                # 如果是ASCII字符范围（通常可打印字符）
                if 0x20 <= byte <= 0x7E:  # 字符的范围
                    processed_data += chr(byte)
                else:
                    processed_data += '_'  # 非字符数据，转换为下划线

            change_hex_data.append(processed_data)  # 将处理后的结果存储在列表中

        print(f"Total lines processed: {len(all_hex_data)}")  # 打印处理的行数

        file.close()

        convert_and_send_init_data(Files)
    else:
        print("未选择文件")


def convert_and_send_init_data(file_name):   # 处理数据
    NAD = "7F"
    first_frame_PCI = "10"
    first_frame_LEN = "82"
    first_frame_SID = "36"
    frame_ID = "01"
    # 打开文件
    with open(file_name, "rb") as f:
        binary_data = f.read()

    # 转换为16进制
    hex_data = binary_data.hex().upper()

    # 一行128字节数据
    lines = [hex_data[i:i + 256] for i in range(0, len(hex_data), 256)]

    # 存储最后的数据
    global finish_data

    for line in lines:
        # 确保一行128字节数据，不够补0

        if len(line) < 256:
            line = line.ljust(256, '0')
        # 将每 2 个十六进制字符转换回字节
        line_bytes = bytes.fromhex(line)
        # 首帧格式
        first_frame_data = [
            NAD,
            first_frame_PCI,
            first_frame_LEN,
            first_frame_SID,
            frame_ID,
            ' '.join([line_bytes[0:1].hex().upper(), line_bytes[1:2].hex().upper(), line_bytes[2:3].hex().upper()]) # D1, D2, D3
        ]
        finish_data.append(" ".join(first_frame_data))

        # 连续帧格式
        pci_counter = 0x21  # 首个连续帧PCI
        # ID格式
        continue_frame_ID = int(frame_ID,16)+1
        if continue_frame_ID > 255 :
            continue_frame_ID = 0
        frame_ID = "{:02X}".format(continue_frame_ID)
        for i in range(3, 128, 6):
            # D1-D6，如果小于 6 字节，用 FF 填充
            data_chunk = line_bytes[i:i + 6]
            if len(data_chunk) < 6:
                data_chunk = data_chunk.ljust(6, b'\xFF')

            pci = f"{pci_counter:02X}"
            consecutive_frame_data = [NAD, pci] + [data_chunk[j:j + 1].hex().upper() for j in range(6)]
            finish_data.append(" ".join(consecutive_frame_data))

            # PCI的格式
            pci_counter += 1
            if pci_counter > 0x2F:
                pci_counter = 0x20


def send_frame():
    # 发送数据
    # 最后的输出帧
    for frame in finish_data:
        #print(f"3C: {frame}")
        LINMsg = LIN_MSG()
        ID = "3C"
        LINMsg.ID = int(ID, 16)  # 将文本框中获取的内容转换为16进制
        LINMsg.DataLen = 8
        message = frame
        ui.textEdit_3.setText(message)  # 将数据显示在文本框中
        words = message.split()
        formatted_words = ['0x' + word for word in words]  # 对每个切片数据前加入'0x'
        for i in range(0, LINMsg.DataLen):
            LINMsg.Data[i] = int(formatted_words[i], 16)
        ret = LIN_Write(DevHandles[0], LINMasterIndex, byref(LINMsg), 1)
        if ret != LIN_SUCCESS:
            print("LIN ID[0x%02X] write data failed!" % LINMsg.ID)
            sys.exit(app.exec_())
        else:
            print("M2S", "[0x%02X] " % LINMsg.ID, end='')
            for i in range(LINMsg.DataLen):
                print("0x%02X " % LINMsg.Data[i], end='')
            print("")
        sleep(0.01)


# 关闭设备
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
    ui.pushButton_2.clicked.connect(Close)
    ui.pushButton_4.clicked.connect(Old_Version)
    ui.pushButton_5.clicked.connect(New_Version)
    ui.pushButton_6.clicked.connect(OpenFile)
    ui.pushButton_7.clicked.connect(send_frame)

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