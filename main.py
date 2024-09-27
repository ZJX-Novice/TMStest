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
import re

finish_data = []

#清除缓存
def ClearCache():
    global first_message
    first_message = ""  # 重置全局变量
    ui.textEdit_2.setText("")  # 清除文本框显示

#写数据
def WriteMessage():
    LINMsg = LIN_MSG()
    if ui.lineEdit_2.text()=="":
        #ui.textEdit.setText("请输入请求ID!")
        QMessageBox.information(MainWindow, "提示", "请输入请求ID")
        return
    ID=ui.lineEdit_2.text()
    # 尝试将ID转换为16进制数，如果失败则提醒用户输入错误
    try:
        LINMsg.ID = int(ID, 16)     # 将文本框中获取的内容转换为16进制
    except ValueError:
        #ui.textEdit.setText("请求ID无效，请输入正确的16进制数！")
        QMessageBox.warning(MainWindow, "警告", "请求ID无效,请输入正确的16进制数!")
        return
    if not (0x00 <= LINMsg.ID <= 0xFF):
        QMessageBox.warning(MainWindow, "警告", "请求ID无效,ID必须是两位十六进制数!(范围:00-FF)")
        return
    LINMsg.DataLen = 8
    message=ui.lineEdit.text() 
    if ui.lineEdit.text()=="":
        #ui.textEdit.setText("请输入请求报文!")
        QMessageBox.information(MainWindow, "提示", "请输入请求报文")
        return
        # 检查报文格式是否正确，确保由8组十六进制数组成
    words = message.split()
    if len(words) != 8:     # 确保报文由8个帧组成
        QMessageBox.warning(MainWindow, "警告","报文格式错误！")
        return

    # 正则表达式检查每个报文帧是否是有效的十六进制数
    hex_pattern = re.compile(r'^[0-9A-Fa-f]{2}$')
    for word in words:
        if not hex_pattern.match(word):
            QMessageBox.warning(MainWindow, "警告", f"报文帧 '{word}' 格式不正确，请输入有效的两位十六进制数!")
            return
    ui.textEdit.insertPlainText(message)
    ui.textEdit.insertPlainText('\n')
    #ui.textEdit.setText(message) #将数据显示在文本框中
    formatted_words = ['0x' + word for word in words]   #对每个切片数据前加入'0x'
    for i in range(0,LINMsg.DataLen):
        LINMsg.Data[i] = int(formatted_words[i],16)
    ret = LIN_Write(DevHandles[0],LINMasterIndex,byref(LINMsg),1)
    if ret != LIN_SUCCESS:
        print("LIN ID[0x%02X] write data failed!"%LINMsg.ID)
        ui.textEdit.setText("LIN ID[0x%02X] read data failed!"%LINMsg.ID)
    else:
        print("M2S","[0x%02X] "%LINMsg.ID,end='')
        for i in range(LINMsg.DataLen):
            print("0x%02X "%LINMsg.Data[i],end='')
        print("")
    sleep(0.1)
    #ClearCache()
    
# 读数据
def ReadMessage():
    global first_message    # 全局变量存储首次ASCII码
    LINMsgRead = LIN_MSG()
    if ui.lineEdit_3.text()=="":
        QMessageBox.information(MainWindow, "提示", "请输入响应ID")
        return
    ID = ui.lineEdit_3.text()
    try:
        LINMsgRead.ID = int(ID, 16)     # 将文本框中获取的内容转换为16进制
    except ValueError:
        QMessageBox.warning(MainWindow, "警告", "响应ID无效，请输入正确的16进制数！")
        return
    if not (0x00 <= LINMsgRead.ID <= 0xFF):
        QMessageBox.warning(MainWindow, "警告", "请求ID无效,ID必须是两位十六进制数!(范围:00-FF)")
        return
    LINMsgRead.DataLen = 8
    ret = LIN_Read(DevHandles[0],LINMasterIndex,byref(LINMsgRead),1)
    if ret != LIN_SUCCESS:
        print("LIN ID[0x%02X] read data failed!"%LINMsgRead.ID)
        # 显示错误信息给用户，‌而不是退出程序
        ui.textEdit_2.setText("LIN ID[0x%02X] read data failed!"%LINMsgRead.ID)
        return None
    else:
        message= ""
        for i in range(LINMsgRead.DataLen-1):
            message += "0x%02X"%LINMsgRead.Data[i]
            message += " "
        print("S2M [0x%02X]"%LINMsgRead.ID,message)
        display_message = " ".join(["%02X" % byte for byte in LINMsgRead.Data[:LINMsgRead.DataLen-1]])

        ui.textEdit_2.insertPlainText(display_message)
        ui.textEdit_2.insertPlainText('\n')

        return display_message

# 旧版本读取
def Old_Version():
    Old_Sw_LINMsg = LIN_MSG()
    Old_Sw_LINMsg.ID = 0x3C
    Old_Sw_LINMsg.DataLen = 8
    # 发送并读取软件版本号
    Sw_message = "7F 03 22 A6 34 FF FF FF"
    wd = Sw_message.split(' ')
    formatted_words = ['0x' + w for w in wd]
    for i in range(Old_Sw_LINMsg.DataLen):
        Old_Sw_LINMsg.Data[i] = int(formatted_words[i], 16)
    ret = LIN_Write(DevHandles[0], LINMasterIndex, byref(Old_Sw_LINMsg), 1)
    if ret != LIN_SUCCESS:
        print("LIN write data failed!")
        return
    else:
        print("M2S", "[0x%02X] " % Old_Sw_LINMsg.ID, end='')
        for i in range(Old_Sw_LINMsg.DataLen):
            print("0x%02X " % Old_Sw_LINMsg.Data[i], end='')
        print("")
    sleep(0.01)  # 等待设备响应

    # 两次读取软件版本号
    Swdata_byte1 = ReadMessage().strip()
    Swdata_byte2 = ReadMessage().strip()
    Swdata_byte = f'{Swdata_byte1} {Swdata_byte2}'
    Sw_data=Swdata_byte[18:24]+Swdata_byte[30:38]
    Sw_ascll_message = ''.join([chr(int(byte, 16)) for byte in Sw_data.split()])
    ui.lineEdit_5.setText(Sw_ascll_message)
    print("SW:",Sw_ascll_message)

    #读取硬件版本号
    data_buffer = (c_byte*8)(0x7F,0x03,0x22,0xA6,0x35,0xFF,0xFF,0xFF)
    Old_Hw_LINMsg = LIN_MSG()
    Old_Hw_LINMsg.ID = 0x3C
    Old_Hw_LINMsg.DataLen = 8
    # 发送并读取硬件版本号
    for i in range(0,Old_Hw_LINMsg.DataLen):
        Old_Hw_LINMsg.Data[i] = data_buffer[i]
    ret = LIN_Write(DevHandles[0], LINMasterIndex, byref(Old_Hw_LINMsg), 1)
    if ret != LIN_SUCCESS:
        print("LIN write data failed!")
        return
    else:
        print("M2S", "[0x%02X] " % Old_Hw_LINMsg.ID, end='')
        for i in range(Old_Hw_LINMsg.DataLen):
            print("0x%02X " % Old_Hw_LINMsg.Data[i], end='')
        print("")
    sleep(0.01)  # 等待设备响应
    #读硬件数据
    Hwdata_byte = ReadMessage().strip()
    Hw_data = Hwdata_byte[15:23]
    Hw_ascll_message = ''.join([chr(int(byte, 16)) for byte in Hw_data.split()])
    ui.lineEdit_6.setText(Hw_ascll_message)
    print("HW:",Hw_ascll_message)
    
# 新版本读取
def New_Version():
    New_Sw_LINMsg = LIN_MSG()
    New_Sw_LINMsg.ID = 0x3C
    New_Sw_LINMsg.DataLen = 8
    # 发送并读取软件版本号
    Sw_message = "7F 03 22 A6 34 FF FF FF"
    wd = Sw_message.split(' ')
    formatted_words = ['0x' + w for w in wd]
    for i in range(New_Sw_LINMsg.DataLen):
        New_Sw_LINMsg.Data[i] = int(formatted_words[i], 16)
    ret = LIN_Write(DevHandles[0], LINMasterIndex, byref(New_Sw_LINMsg), 1)
    if ret != LIN_SUCCESS:
        print("LIN write data failed!")
        return
    else:
        print("M2S", "[0x%02X] " % New_Sw_LINMsg.ID, end='')
        for i in range(New_Sw_LINMsg.DataLen):
            print("0x%02X " % New_Sw_LINMsg.Data[i], end='')
        print("")
    sleep(0.01)  # 等待设备响应

    # 两次读取软件版本号
    Swdata_byte1 = ReadMessage().strip()
    print(Swdata_byte1)
    Swdata_byte2 = ReadMessage().strip()
    print(Swdata_byte2)
    Swdata_byte = f'{Swdata_byte1} {Swdata_byte2}'
    Sw_data=Swdata_byte[18:24]+Swdata_byte[30:38]
    Sw_ascll_message = ''.join([chr(int(byte, 16)) for byte in Sw_data.split()])
    ui.lineEdit_7.setText(Sw_ascll_message)
    print("SW:",Sw_ascll_message)

    #读取硬件版本号
    data_buffer = (c_byte*8)(0x7F,0x03,0x22,0xA6,0x35,0xFF,0xFF,0xFF)
    New_Hw_LINMsg = LIN_MSG()
    New_Hw_LINMsg.ID = 0x3C
    New_Hw_LINMsg.DataLen = 8
    # 发送并读取硬件版本号
    for i in range(0,New_Hw_LINMsg.DataLen):
        New_Hw_LINMsg.Data[i] = data_buffer[i]
    ret = LIN_Write(DevHandles[0], LINMasterIndex, byref(New_Hw_LINMsg), 1)
    if ret != LIN_SUCCESS:
        print("LIN write data failed!")
        return
    else:
        print("M2S", "[0x%02X] " % New_Hw_LINMsg.ID, end='')
        for i in range(New_Hw_LINMsg.DataLen):
            print("0x%02X " % New_Hw_LINMsg.Data[i], end='')
        print("")
    sleep(0.01)  # 等待设备响应
    #读硬件数据
    Hwdata_byte = ReadMessage().strip()
    print(Hwdata_byte)
    Hw_data = Hwdata_byte[15:23]
    Hw_ascll_message = ''.join([chr(int(byte, 16)) for byte in Hw_data.split()])
    ui.lineEdit_8.setText(Hw_ascll_message)
    print("HW:",Hw_ascll_message)


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
        QMessageBox.information(MainWindow,"提示","未选择文件，请重新选择！")

def convert_and_send_init_data(file_name):   # 处理数据
    NAD = "01"
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

#解密函数
def DiagSvcSecAccess_SaccKey(seed):
    key_result = (((seed >> 1) ^ seed) << 3) ^ (seed >> 2)
    SaccKey = (key_result ^ 0xFFFF)&0xFFFF
    return SaccKey

#扩展会话+安全校验
def send_frame():
    LINMsg = LIN_MSG()
    ID = "3C"
    LINMsg.ID = int(ID, 16)  # 将文本框中获取的内容转换为16进制
    LINMsg.DataLen = 8
    check_words = [
        "01 02 10 03 FF FF FF FF",
        "01 02 27 01 FF FF FF FF",
        "01 04 27 02 F9 AD FF FF",
        "01 02 10 02 FF FF FF FF",
        "01 02 27 01 FF FF FF FF",
        "01 04 27 02 F9 AD FF FF",
        "01 10 0E 31 01 DF FF 44",  
        "01 21 00 01 58 00 00 01",
        "01 22 C9 6B 00 FF FF FF",
        "01 04 31 03 DF FF FF FF", 
        "01 10 0B 34 00 44 00 01",
        "01 21 58 00 00 01 C9 6B"
    ]
    resp_words = [
        "01 02 50 03 FF FF FF FF",
        "01 04 67 01 00 8B FF FF",
        "01 02 67 02 FF FF FF FF",
        "01 02 50 02 FF FF FF FF",
        "01 04 67 01 00 8B FF FF",
        "01 02 67 02 FF FF FF FF",
#如果第二位pci为10，就继续执行发送报文，直到第二位不在范围0x20~0x2F（包含20和2F）里,进行接收响应
        "",
        "01 21 00 01 58 00 00 01",
        "01 06 71 01 DF FF 01 F4",
        "01 04 71 03 DF FF FF FF",
        "",
        "01 04 74 20 00 82 FF FF"
    ]
    # 遍历 check_words
    for index, word in enumerate(check_words):
        max_retries = 3  # 设置最大重发次数
        retry_count = 0   # 初始化重发计数器
        # 发送报文
        wd = word.split(' ')
        formatted_words = ['0x' + w for w in wd]  # 对每个切片数据前加入'0x'
        for i in range(0, LINMsg.DataLen):
            LINMsg.Data[i] = int(formatted_words[i], 16)

        res = resp_words[index].split(' ')
        formatted_resp = " ".join([ r for r in res]).strip()

        flag = True
        while flag:
            send_1=hex(int(get_frame(word, 1),16))
            if(send_1=='0x10'):
                print("--------",index,"发送首帧")
                flag = False
            if '0x20'<=send_1<='0x2F':
                print("--------",index,"发送续帧")
                #flag = False

            ret = LIN_Write(DevHandles[0], LINMasterIndex, byref(LINMsg), 1)
            if ret != LIN_SUCCESS:
                print("LIN ID[0x%02X] write data failed!" % LINMsg.ID)
                sys.exit(app.exec_())
            else:
                print("M2S", "[0x%02X] " % LINMsg.ID, end='')
                for i in range(LINMsg.DataLen):
                    print("0x%02X " % LINMsg.Data[i], end='')
                print("")
            sleep(0.1)
            #ClearCache()
            # 接收报文并去掉空格
            if ui.lineEdit_3.text()=="":
                ui.textEdit_2.setText("请输入响应ID!")
                return
            send_res = ReadMessage().strip()

            print("============================================================")
            print(index,"-------------------------",send_res)
            print(index,"-------------------------",formatted_resp)
            print("============================================================")

            if send_res == formatted_resp:
                print("-------",index,"匹配成功！")
                flag = False
                break
            else:
                print("-------",index,"匹配失败，正在重发...")
                if retry_count >= max_retries:
                    print("重发次数已超过最大限制，无法匹配！")
                    QMessageBox.warning(MainWindow, "警告", "重发次数已超过最大限制，无法匹配！")
                    return
                retry_count+=1
                    
            # else:
            #     if index ==0:

            # 处理数组的第二个和第五个报文 (index == 1 or index == 4)
            if index == 1 :
                if send_res.strip() == '':
                    continue
                # 获取第 5 6 位 帧，去掉 0x
                seed_part2_5 = get_frame(send_res, 4)
                seed_part2_6 = get_frame(send_res, 5)
                seed = int(seed_part2_5 + seed_part2_6, 16)
                decrypted_key2 = DiagSvcSecAccess_SaccKey(seed)  # 调用解密函数
                print(f"Decrypted key: 0x{decrypted_key2:04X}")  # 输出解密后的密钥
                # 将解密后的值更新到第三个报文的第五位和第六位
                third_message = check_words[2].split(' ')  # 获取第三个报文
                third_message[4] = f"{(decrypted_key2 >> 8):02X}"  # 替换第五位
                third_message[5] = f"{(decrypted_key2 & 0xFF):02X}"  # 替换第六位
                # 更新请求报文
                set_frame(check_words, 2, " ".join(third_message))
                print(f"Updated third message: {check_words}")
                # 第 2 5 条发送报文无需验证
                print("解密成功！")
                flag = False

            if index == 4 :
                if send_res.strip() == '':
                    continue
                # 获取第 5 6 位 帧，去掉 0x
                seed_part5_5 = get_frame(send_res, 4)
                seed_part5_6 = get_frame(send_res, 5)
                seed = int(seed_part5_5 + seed_part5_6, 16)
                decrypted_key5 = DiagSvcSecAccess_SaccKey(seed)  # 调用解密函数
                print(f"Decrypted key: 0x{decrypted_key5:04X}")  # 输出解密后的密钥
                # 将解密后的值更新到第五个报文的第五位和第六位
                fifth_message = check_words[5].split(' ')  # 获取第六个报文
                fifth_message[4] = f"{(decrypted_key5 >> 8):02X}"  # 替换第五位
                fifth_message[5] = f"{(decrypted_key5 & 0xFF):02X}"  # 替换第六位
                # 更新请求报文
                set_frame(check_words, 5, " ".join(fifth_message))
                print(f"Updated fifth message: {check_words}")
                # 第 5 条发送报文无需验证
                print("解密成功！")
                flag = False
    return True

def flash_message():
    # 校验连接状态
    if(not DeviceOperate().checkConnected()):
        QMessageBox.warning(MainWindow, "警告", "请检查连接状态")
        return

    # # 校验是否选择文件
    # Files = ui.lineEdit_9.text()
    # if not Files:
    #     QMessageBox.warning(MainWindow, "警告", "未选择文件，请选择文件！")
    #     return

    ret = send_frame()
    if ret == True:
        print("安全校验成功，开始烧录！")
        index = 0
        max_retries = 3  # 设置最大重发次数
        retry_count = 0   # 初始化重发计数器

        while index < len(finish_data):
            frame = finish_data[index]
            ui.textEdit.setText(frame)  # 将数据显示在文本框中
            LINMsg = LIN_MSG()
            ID_Write = "3C"
            LINMsg.ID = int(ID_Write, 16)
            LINMsg.DataLen = 8
            words = frame.split(' ')
            formatted_words = ['0x' + word for word in words]
            for i in range(0, LINMsg.DataLen):
                LINMsg.Data[i] = int(formatted_words[i], 16)

            ret = LIN_Write(DevHandles[0], LINMasterIndex, byref(LINMsg), 1)
            if ret != LIN_SUCCESS:
                print("LIN ID[0x%02X] write data failed!" % LINMsg.ID)
                ui.textEdit.setText("LIN ID[0x%02X] write data failed!" % LINMsg.ID)
                return
            else:
                print(index, "----M2S", "[0x%02X] " % LINMsg.ID, end='')
                for i in range(LINMsg.DataLen):
                    print("0x%02X " % LINMsg.Data[i], end='')
                print("")

                # 检查是否发送了22条报文
                if (index+1) % 22 == 0:
                    while True:
                        resread = ReadMessage().strip()
                        if resread == frame.strip():
                            print("=======================================================未收到响应，重新发送=======================================================")
                            retry_count += 1
                            if retry_count > max_retries:
                                print(f"重发已达{max_retries}次，退出程序")
                                QMessageBox.warning(MainWindow, "警告", f"已重发{max_retries}次，未收到响应。请检查设备状态。")
                                return
                            index -= 22  # 将index减少22，重新发送
                            break
                        else:
                            print("收到响应，继续发送")
                            retry_count = 0  # 重置重发计数器
                            break  # 收到响应，跳出循环继续发送下一条
            index += 1  # 手动增加 index
            sleep(0.05)
    else:
        QMessageBox.warning(MainWindow, "警告", "安全校验失败，请检查设备状态!")

# 获取指定位置的帧
def get_frame(words, index):
    words_split = words.split(' ')
    return words_split[index].replace('0x', '')
# 更新帧的指定位置设置为指定值
def set_frame(frame,index,value):
    for i in range(len(frame)):
        if i == index:
            frame[i] = value

# Device Operate finish               
class DeviceOperate():
    # 连接是否成功
    isConnected = False
    def checkConnected() -> bool:
        return bool(DeviceOperate.isConnected)

    def __init__(self) -> None:
        pass

    def checkConnected(self) -> bool:
        return bool(self.isConnected)

    def ScanDevice(self):
        ret = USB_ScanDevice(byref(DevHandles))
        if(ret == 0):
            QMessageBox.critical(MainWindow,"提示","没有设备连接，请连接后重试！")
            sys.exit(app.exec_())
        else:
            print("Have %d device connected!"%ret)   
        return ret

    def OpenDevice(self):
        self.ScanDevice()
        ret = USB_OpenDevice(DevHandles[0])
        if(bool(ret)):
            ui.textEdit_3.insertPlainText("Open device success!")    
            ui.textEdit_3.insertPlainText('\n')
        else:
            ui.textEdit_3.insertPlainText("Open device faild!")       
            ui.textEdit_3.insertPlainText('\n') 
            sys.exit(app.exec_())
        USB2XXXInfo = DEVICE_INFO()
        USB2XXXFunctionString = (c_char * 256)()
        ret = DEV_GetDeviceInfo(DevHandles[0],byref(USB2XXXInfo),byref(USB2XXXFunctionString))
        if(bool(ret)):
            ui.textEdit_3.insertPlainText("USB2XXX device infomation:")
            ui.textEdit_3.insertPlainText('\n')
            ui.textEdit_3.insertPlainText("--Firmware Name: %s"%bytes(USB2XXXInfo.FirmwareName).decode('ascii'))
            ui.textEdit_3.insertPlainText('\n')        
            ui.textEdit_3.insertPlainText("--Firmware Version: v%d.%d.%d"%((USB2XXXInfo.FirmwareVersion>>24)&0xFF,(USB2XXXInfo.FirmwareVersion>>16)&0xFF,USB2XXXInfo.FirmwareVersion&0xFFFF))
            ui.textEdit_3.insertPlainText('\n')        
            ui.textEdit_3.insertPlainText("--Hardware Version: v%d.%d.%d"%((USB2XXXInfo.HardwareVersion>>24)&0xFF,(USB2XXXInfo.HardwareVersion>>16)&0xFF,USB2XXXInfo.HardwareVersion&0xFFFF))
            ui.textEdit_3.insertPlainText('\n')        
            ui.textEdit_3.insertPlainText("--Build Date: %s"%bytes(USB2XXXInfo.BuildDate).decode('ascii'))
            ui.textEdit_3.insertPlainText('\n')
            
            serial_number_str = "--serial Number: "
            for i in range(0, len(USB2XXXInfo.SerialNumber)):
                serial_number_str += "%08X"%USB2XXXInfo.SerialNumber[i]
            ui.textEdit_3.insertPlainText(serial_number_str)  # 输出完整的序列号字符串
            ui.textEdit_3.insertPlainText('\n')
            
            ui.textEdit_3.insertPlainText("")
            ui.textEdit_3.insertPlainText("--Function String: %s"%bytes(USB2XXXFunctionString.value).decode('ascii'))  
            ui.textEdit_3.insertPlainText('\n')
        else:
            ui.textEdit_3.insertPlainText("Get device infomation faild!")
            ui.textEdit_3.insertPlainText('\n')       
            sys.exit(app.exec_()) 
            
        # 初始化配置主LIN
        LINConfig = LIN_CONFIG()
        LINConfig.BaudRate = 19200
        LINConfig.BreakBits = LIN_BREAK_BITS_11
        LINConfig.CheckMode = LIN_CHECK_MODE_EXT
        LINConfig.MasterMode = LIN_MASTER
        ret = LIN_Init(DevHandles[0],LINMasterIndex,byref(LINConfig))
        if ret != LIN_SUCCESS:
            ui.textEdit_3.insertPlainText("Config Master LIN failed!")
            ui.textEdit_3.insertPlainText('\n')
            sys.exit(app.exec_())
        else:
            DeviceOperate.isConnected = True
            ui.textEdit_3.insertPlainText("Config Master LIN Success!")
            ui.textEdit_3.insertPlainText('\n')
        sleep(0.01)

    def CloseDevice(self):
        self.ScanDevice()
        ret = USB_CloseDevice(DevHandles[0])
        if(bool(ret)):
            ui.textEdit_3.insertPlainText("close device success!")
            ui.textEdit_3.insertPlainText('\n')
        else:
            ui.textEdit_3.insertPlainText("close device faild!")
            sys.exit(app.exec_())

    def ClosePanel(self):
        print("close panel success!")
        sys.exit(app.exec_())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    MainWindow = QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    
    LINMasterIndex = 0
    DevHandles = (c_uint * 20)()
    DeviceCMD = DeviceOperate()

    ui.pushButton.clicked.connect(WriteMessage)
    ui.pushButton_3.clicked.connect(ReadMessage)
    ui.pushButton_2.clicked.connect(DeviceCMD.ClosePanel)
    ui.pushButton_8.clicked.connect(DeviceCMD.OpenDevice)
    ui.pushButton_9.clicked.connect(DeviceCMD.CloseDevice)
    ui.pushButton_4.clicked.connect(Old_Version)
    ui.pushButton_5.clicked.connect(New_Version)
    ui.pushButton_6.clicked.connect(OpenFile)
    ui.pushButton_7.clicked.connect(flash_message)

    sys.exit(app.exec_())
