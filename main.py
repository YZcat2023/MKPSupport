# coding=utf-8
import tkinter as tk  # 导入GUI界面函数库
from tkinter import ttk, scrolledtext
import tkinter.messagebox
import re, os, time, ctypes, sys
from PIL import Image, ImageTk
import base64
from in_png import img as png1
from sys import exit

GSourceFile = ""
try:
    GSourceFile = sys.argv[1]
    print(GSourceFile)
except:
    pass
ctypes.windll.shcore.SetProcessDpiAwareness(1)
ScaleFactor = ctypes.windll.shcore.GetScaleFactorForDevice(0)
# 创建窗口
window = tk.Tk()
window.title('Markpen v3.0')
screenWidth = window.winfo_screenwidth()  # 获取显示区域的宽度
screenHeight = window.winfo_screenheight()  # 获取显示区域的高度
width = 300  # 设定窗口宽度
height = 160  # 设定窗口高度
left = (screenWidth - width) / 2
top = (screenHeight - height) / 2
window.geometry("%dx%d+%d+%d" % (width, height, left, top))
window.resizable(width=False, height=False)
tmp = open('in.png', 'wb')  # 创建临时的文件
tmp.write(base64.b64decode(png1))  ##把这个one图片解码出来，写入文件中去。
tmp.close()
image0 = Image.open("in.png")
image0 = image0.resize((300, 160))
os.remove("in.png")
tk_image = ImageTk.PhotoImage(image0)
label = tk.Label(window, image=tk_image)
label.pack()
window.tk.call('tk', 'scaling', ScaleFactor / 75)

# parameters
# X_Operable=0#X轴移动到此位置即可操作笔杆
# X_Inoperable=0#X轴移动到此位置不可改变笔杆角度
# Y_Lockdown=0#Y轴移动到此位置即使得笔杆锁定到工作位
# Y_Release=0#Y轴移动到此位置使得笔杆不再可工作
Z_Offset = 0  # 笔尖在工作位时比喷嘴更低，这个值是喷嘴与笔尖间的高度差
CustomClean = []  # 自定义擦嘴代码
NocleanThreshold = 0  # 超过该等待时间即进行擦嘴
X_Offset = 0  # 喷嘴与笔尖的X坐标的差值
Y_Offset = 0  # 喷嘴与笔尖的Y坐标的差值
AggressiveRetract = 0  # 不为零时将进行较为激进的回抽
Max_Speed = 0  # 最高移动速度
Max_Acceleration = 0  # 最高加速度
CustomRelease = []  # 自定义收回（收回笔杆）
CustomLock = []  # 自定义锁定（放下笔杆）
# 是否有Mrkcon.ini，如果没有则自动创建
Create_New_Config = 'no'
User_Input = []
Source = []
Marked_path = []
Output_Filename = ''  # 导出文件名
Input_Filename = ""  # 导入文件名
global GcodeExporter, LogExporter


def get_preset_values():
    # 创建主窗口
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    # 创建弹窗询问是否使用默认 笔杆操作方式
    # TypeResult = tk.messagebox.askquestion("", "是否使用默认的抬笔/落笔的操作方式？", default=tk.messagebox.YES)
    # CleanResult=tk.messagebox.askquestion("", "您的机器是否支持擦嘴？", default=tkinter.messagebox.YES)
    popup = tk.Toplevel(root)
    popup.resizable(width=False, height=False)
    popup.title("配置向导")
    # 创建标签和输入框
    # if TypeResult=='yes':
    #     labels = ["X轴可操作坐标", "X轴不可操作坐标", "Y轴锁定坐标", "Y轴弹起坐标","喷嘴笔尖高度差","最高移动速度","擦嘴代码","X坐标补偿值","Y坐标补偿值"]
    # else:
    #     labels = ["自定义收起G代码", "自定义放下G代码","喷嘴笔尖高度差","最高移动速度","擦嘴代码","X坐标补偿值","Y坐标补偿值"]
    labels = ["自定义收起G代码", "自定义放下G代码", "喷嘴笔尖高度差", "最高移动速度[MM/S]", "擦嘴代码", "X坐标补偿值",
              "Y坐标补偿值", "熨烫接触面[Y/N]","熨烫速度[MM/S]","熨烫挤出乘数"]
    entries = []
    for i, label in enumerate(labels):
        tk.Label(popup, text=label + ":", justify='left', padx=10).grid(row=i, column=0, sticky='w')
        entry = tk.Entry(popup)
        if label in ["自定义收起G代码", "自定义放下G代码", "擦嘴代码"]:
            # 对于特定的label，使用scrolledtext.ScrolledText来创建带有滚动条的Text控件
            text_box = scrolledtext.ScrolledText(popup, wrap=tk.WORD, width=10, height=3.5)
            text_box.grid(row=i, column=1, padx=10, sticky='ew')  # sticky='ew' 使控件在列中水平扩展
            # 由于我们使用了scrolledtext.ScrolledText，所以不需要单独添加entries到这个列表中
            entries.append(text_box)
        else:
            entry.grid(row=i, column=1, padx=10)
            entries.append(entry)

    def on_submit():
        global User_Input
        for entry in entries:
            if isinstance(entry, tk.Entry):
                User_Input.append(entry.get())
            elif isinstance(entry, scrolledtext.ScrolledText):
                User_Input.append(entry.get(1.0, tk.END))  # Get text from 1.0 to the end
        # User_Input = [entry.get() for entry in entries]
        values = 1
        popup.destroy()
        root.quit()  # 关闭弹窗
        return values

    def on_closing():
        # 在这里执行窗口关闭时的操作，比如询问用户是否确定要关闭窗口
        if tk.messagebox.askokcancel("退出", "您真的要退出吗?"):
            root.destroy()  # 如果用户确认，则关闭窗口
            exit("User cancel")
    # 绑定关闭事件处理函数到窗口关闭事件
    popup.protocol("WM_DELETE_WINDOW", on_closing)

    style = ttk.Style()
    style.configure('Rounded.TButton', roundcorners=25)  # 设置圆角的大小
    ttk.Button(popup, text="确定", style='Rounded.TButton', command=on_submit).grid(row=len(labels), column=1,
                                                                                    pady=10)
    # 进入主循环，等待用户操作
    root.mainloop()
    root.destroy()
    # 这里正常情况下不会执行，因为mainloop会阻塞，直到窗口关闭
    return []


def environment_check():  # 后处理前的操作
    global CustomClean, CustomLock, CustomRelease, Z_Offset, Max_Speed, Iron_Speed,Iron_Flag,Iron_Extrude_Ratio, X_Offset, Y_Offset, Input_Filename, Output_Filename
    valid_con = False
    valid_file = False
    print(os.path.dirname(os.path.abspath(sys.executable)))
    for file in os.listdir(os.path.dirname(os.path.abspath(sys.executable))):
        if "Mrkcon.ini" in file:  # 使用 'in' 来检查子字符串是否存在于文件名中
            valid_con = True
            break  # 如果只需要找到第一个匹配的文件，可以使用 break 跳出循环
    # 如果有配置文件的话:
    if valid_con:
        ConfigReader = open(os.path.dirname(os.path.abspath(sys.executable)) + "\\" + "Mrkcon.ini")

    # 如果没有的话:
    else:
        Create_New_Config = tk.messagebox.askquestion(title='无可用预设', message='当前文件夹下无可用预设。创建新预设？')
        if Create_New_Config == 'yes':
            with open(os.path.dirname(os.path.abspath(sys.executable)) + "\\" + "Mrkcon.ini", "w") as ConfigExporter:
                get_preset_values()
                print(User_Input)
                print("自定义收起G代码:" + os.linesep + str(User_Input[0]), file=ConfigExporter)
                print("自定义放下G代码:" + os.linesep + str(User_Input[1]), file=ConfigExporter)
                print("喷嘴笔尖高度差:" + str(User_Input[2]), file=ConfigExporter)
                print("最高移动速度:" + str(User_Input[3]), file=ConfigExporter)
                print("擦嘴代码:" + os.linesep + str(User_Input[4]), file=ConfigExporter)
                print("X坐标补偿值:" + str(User_Input[5]), file=ConfigExporter)
                print("Y坐标补偿值:" + str(User_Input[6]), file=ConfigExporter)
                print("熨烫接触面[Y/N]:" + str(User_Input[7]), file=ConfigExporter)
                print("熨烫速度:" + str(User_Input[8]), file=ConfigExporter)
                print("熨烫挤出乘数:" + str(User_Input[9]), file=ConfigExporter)
            ConfigExporter.close()
            tk.messagebox.showinfo(title='完成', message='数据已经录入。软件将自动关闭，请重新启动')
            sys.exit("Data Fetched")
        else:
            sys.exit("User cancelled:用户终止")

        ConfigReader = open(os.path.dirname(os.path.abspath(sys.executable)) + "\\" + "Mrkcon.ini")
    # 读入到临时文件里；
    Con_Temp = ConfigReader.read()
    lines = Con_Temp.splitlines()

    Copy_path_flag = False
    for index in range(len(lines)):
        if lines[index].find("自定义收起G代码:") != -1:
            Copy_path_flag = True
        if Copy_path_flag == True:
            if lines[index].find("自定义放下G代码") == -1:
                if lines[index] != "" and lines[index].find("自定义") == -1:
                    CustomRelease.append(lines[index])
            else:

                Copy_path_flag = False
                break
    for index in range(len(lines)):
        if lines[index].find("自定义放下G代码:") != -1:
            Copy_path_flag = True
        if Copy_path_flag == True:
            if lines[index].find("喷嘴笔尖") == -1:
                if lines[index] != "" and lines[index].find("自定义") == -1:
                    CustomLock.append(lines[index])
            else:
                Copy_path_flag = False
                break

    for index in range(len(lines)):
        if lines[index].find("擦嘴代码:") != -1:
            Copy_path_flag = True
        if Copy_path_flag == True:
            if lines[index].find("X坐标") == -1:
                if lines[index] != "" and lines[index].find("擦嘴") == -1:
                    CustomClean.append(lines[index])
            else:
                Copy_path_flag = False
                break

    for index in range(len(lines)):
        if lines[index].find("喷嘴笔尖") != -1:
            Z_Offset = re.findall(r"\d+\.?\d*", lines[index])
        if lines[index].find("最高移动") != -1:
            Max_Speed = re.findall(r"\d+\.?\d*", lines[index])
        if lines[index].find("X坐标补偿值") != -1:
            X_Offset = re.findall(r"\d+\.?\d*", lines[index])
            if lines[index].find("-") != -1:
                X_Offset[0] = "-" + X_Offset[0]
        if lines[index].find("Y坐标补偿值") != -1:
            Y_Offset = re.findall(r"\d+\.?\d*", lines[index])
            if lines[index].find("-") != -1:
                Y_Offset[0] = "-" + Y_Offset[0]
        if lines[index].find("熨烫速度") != -1:
            Iron_Speed = re.findall(r"\d+\.?\d*", lines[index])
        if lines[index].find("熨烫接触面[Y/N]") != -1:
            lineco=lines[index]
            lineco=lineco.replace("熨烫接触面[Y/N]", "")
            if lineco.find("Y")!=-1 or lineco.find("y")!=-1:
                Iron_Flag=True
        if lines[index].find("熨烫挤出乘数") != -1:
            Iron_Extrude_Ratio = re.findall(r"\d+\.?\d*", lines[index])
    try:
        Z_Offset = float(Z_Offset[0])
        Max_Speed = float(Max_Speed[0])
        X_Offset = float(X_Offset[0])
        Y_Offset = float(Y_Offset[0])
        Iron_Speed = float(Iron_Speed[0])
        Iron_Extrude_Ratio = float(Iron_Extrude_Ratio[0])
        Max_Speed=Max_Speed*60
        Iron_Speed=Iron_Speed*60
    except:
        DeleteConfig=tk.messagebox.askquestion(title='错误', message='您填写的预设参数不合法。需要删除这份预设吗？')
        if DeleteConfig:
            ConfigReader.close()
            os.remove(os.path.dirname(os.path.abspath(sys.executable)) + "\\" + "Mrkcon.ini")
        sys.exit("Illegal Input")
    if GSourceFile == "":  # 没有被传参
        # 检索目录下的所有gcode，x3g类文件
        for file in os.listdir():
            # print(os.listdir())
            if file.find(".g") != -1 or file.find(".x3g") != -1 or file.find(".gcode") != -1:  # 识别.G,.GCODE,即输入文件
                # 确定该文件是否已处理过的文件

                if file.find("Output") == -1:
                    Input_Filename = file
                    valid_file = True  # 有文件
                    # break
    else:
        Input_Filename = GSourceFile

    if valid_file != True and GSourceFile == "":
        tk.messagebox.showerror(title='错误', message='程序所在文件夹下无可用Gcode文件')
        sys.exit("No usable gcode:无可用Gcode")

    if GSourceFile == "":
        # 输出时的名称
        Filename_index = Input_Filename.find(".gcode")
        Output_Filename = Input_Filename[0:Filename_index] + "_Output.gcode"
    else:
        Output_Filename = GSourceFile + "_Output.gcode"
    # print(Output_Filename)
    # 清除上一次生成的文件
    # for file in os.listdir():
    #     if file == Output_Filename:
    #         os.remove(file)


def Str_Strip(line):
    Source = re.findall(r"\d+\.?\d*", line)
    Source = list(map(float, Source))
    data = Source[0]
    return data


def format_xy_string(text):
    def process_data(match):
        if match:
            return f"{match.group(1)}{float(match.group(2)):.3f}"
        return ""

    text = re.sub(r'(X)([\d.]+)', lambda m: process_data(m), text)
    text = re.sub(r'(Y)([\d.]+)', lambda m: process_data(m), text)
    return text

def format_xy_string_ironing(text):
    def process_data(match):
        if match:
            return f"{match.group(1)}{float(match.group(2)):.3f}"
        return ""

    text = re.sub(r'(X)([\d.]+)', lambda m: process_data(m), text)
    text = re.sub(r'(Y)([\d.]+)', lambda m: process_data(m), text)
    text = re.sub(r'(E)([\d.]+)', lambda m: process_data(m), text)
    return text
def process_text(text, x_offset, y_offset):
    text = format_xy_string(text)
    pattern = r"(X|Y)(\d+\.\d+)"  # 匹配X或Y，后面跟着一个或多个数字和小数点
    match = re.findall(pattern, text)
    # print(match)
    # 创建一个字典存储修改后的数值
    values = {}
    for m in match:
        key, value = m
        if key == 'X':
            values[key] = round(float(value) + x_offset, 3)
        else:
            values[key] = round(float(value) + y_offset, 3)

    # 替换原文本中的数值
    for key, value in values.items():
        text = re.sub(rf"{key}\d+\.\d+", f"{key}{value}", text)
    # pattern = r"E[\-\+]?\d+\.\d+"
    # pattern = r"E[\.\-\+]?\d*"
    if (text.find("E") < text.find(";") and text.find(";") != -1 and text.find("E") != -1) or (
            text.find("E") != -1 and text.find(";") == -1):  # 如果E出现在注释；前面或者没有注释但是有E
        text = text[:text.find("E")]

    if (text.find("Z") < text.find(";") and text.find(";") != -1 and text.find("Z") != -1) or (
            text.find("Z") != -1 and text.find(";") == -1):  # 如果E出现在注释；前面或者没有注释但是有E
        text = text[:text.find("Z")]
    # text=text+";Cured"
    # text = re.sub(pattern, "", text)
    return text


def process_ironing(text, x_offset, y_offset):
    text = format_xy_string_ironing(text)
    pattern = r"(X|Y|E)(\d+\.\d+)"  # 匹配X或Y，后面跟着一个或多个数字和小数点
    match = re.findall(pattern, text)
    # print(match)
    # 创建一个字典存储修改后的数值
    values = {}
    for m in match:
        key, value = m
        if key == 'X':
            values[key] = round(float(value) + x_offset, 3)
        elif key == 'Y':
            values[key] = round(float(value) + y_offset, 3)
        elif key == 'E':
            values[key] = round(float(value) * Iron_Extrude_Ratio, 3)
    # 替换原文本中的数值
    for key, value in values.items():
        text = re.sub(rf"{key}\d+\.\d+", f"{key}{value}", text)
    # pattern = r"E[\-\+]?\d+\.\d+"
    # pattern = r"E[\.\-\+]?\d*"

    if (text.find("Z") < text.find(";") and text.find(";") != -1 and text.find("Z") != -1) or (
            text.find("Z") != -1 and text.find(";") == -1):  # 如果E出现在注释；前面或者没有注释但是有E
        text = text[:text.find("Z")]
    # text=text+";Cured"
    # text = re.sub(pattern, "", text)
    return text


def main():
    Is_first_th = True
    primary_th = ""
    Layer_Flag = False
    Copy_Flag = False
    InterFace = []
    Current_Layer_Height = 0
    Interrupt_flag = False
    environment_check()
    #print(process_ironing("G1 X6 Y6 E3",0.2,0))
    temp_file_name = Input_Filename.strip(".gcode")
    TempExporter = open(Output_Filename, "w", encoding="utf-8")
    with open(Input_Filename, "r", encoding="utf-8", errors='ignore') as f:  # 读取输入文件,此过程粗处理文件
        for line in f.readlines():
            line = line.strip('\n')  # 去掉换行符

            # 检查模型主体采用的是哪一个
            if (line.find("T") == 0 and Is_first_th == True):
                primary_th = line
                Is_first_th = False

                print("Primary Toolhead:" + primary_th)

            # 检查层高的变化，并且实时记录。可能有点多余
            if line.find(";LAYER_CHANGE") != -1:
                Layer_Flag = True

            if Layer_Flag == True and line.find(";Z:") != -1:
                Current_Layer_Height = Str_Strip(line)
                Layer_Flag = False

            if line.find(";AFTER_LAYER_CHANGE") != -1:
                if Copy_Flag == True:
                    Interrupt_flag = True

            # 发现不是模型主体的材料，那就是要开始记录了
            if line.find("T") == 0 and line != primary_th:
                print("This Toolhead is:" + line)
                Copy_Flag = True  # 开始记录
            if Copy_Flag == True and line.find("G1") != -1 and line.find("G1 E") == -1 and line.find(
                    "G1 Z") == -1 and line.find("G1 F") == -1:  # 只记录G1指令
                InterFace.append(line)  # 记录

            # 层间中断
            if Interrupt_flag == True:
                Interrupt_flag = False  # 不再记录
                #ironing
                if Iron_Flag:
                    print(";Ironing", file=TempExporter)
                    print("G1 F" + str(Iron_Speed), file=TempExporter)
                    for index in range(len(InterFace)):
                        print(process_text(InterFace[index],0.2, 0), file=TempExporter)
                    print(";Ironing finished", file=TempExporter)
                print("G1 Z" + str(round(Current_Layer_Height + Z_Offset + 3, 3)) + ";Avoid Hitting", file=TempExporter)
                for index in range(len(CustomLock)):
                    print(CustomLock[index], file=TempExporter)
                print(process_text(InterFace[0], X_Offset, Y_Offset)+";In position", file=TempExporter)
                print("G1 F" + str(Max_Speed)+";MKPSpeed", file=TempExporter)
                print("G1 Z" + str(round(Current_Layer_Height + Z_Offset, 3)) + ";Adjust Nozzle", file=TempExporter)
                for index in range(len(InterFace)):
                    print(process_text(InterFace[index], X_Offset, Y_Offset), file=TempExporter)
                InterFace.clear()  # 输出并清空已捕获的内容
                print("G1 Z" + str(round(Current_Layer_Height+Z_Offset+2, 3)) + ";Avoid leaking", file=TempExporter)
                for index in range(len(CustomRelease)):
                    print(CustomRelease[index], file=TempExporter)
                for index in range(len(CustomClean)):
                    print(CustomClean[index], file=TempExporter)
                print("G1 Z" + str(round(Current_Layer_Height, 3)) + ";Lower nozzle", file=TempExporter)
            # 又用到主体的材料了
            if line == primary_th and Copy_Flag == True:
                Copy_Flag = False  # 不再记录
                if InterFace:
                    if Iron_Flag:
                        print(";Ironing", file=TempExporter)
                        print("G1 F" + str(Iron_Speed), file=TempExporter)
                        for index in range(len(InterFace)):
                            print(process_text(InterFace[index], 0.2, 0), file=TempExporter)
                        print(";Ironing finished", file=TempExporter)
                    print("G1 Z" + str(round(Current_Layer_Height + Z_Offset + 3, 3)) + ";Avoid Hitting",
                          file=TempExporter)
                    # print("G1 Z" + str(round(Current_Layer_Height + Z_Offset, 3)) + ";Lift nozzle", file=TempExporter)
                    for index in range(len(CustomLock)):
                        print(CustomLock[index], file=TempExporter)
                    print(process_text(InterFace[0], X_Offset, Y_Offset) + ";In position", file=TempExporter)
                    print("G1 F" + str(Max_Speed) + ";MKPSpeed", file=TempExporter)
                    print("G1 Z" + str(round(Current_Layer_Height + Z_Offset, 3)) + ";Adjust Nozzle", file=TempExporter)
                    for index in range(len(InterFace)):
                        print(process_text(InterFace[index], X_Offset, Y_Offset), file=TempExporter)
                    InterFace.clear()  # 输出并清空已捕获的内容
                    print("G1 Z" + str(round(Current_Layer_Height + Z_Offset + 2, 3)) + ";Avoid leaking",
                          file=TempExporter)
                    for index in range(len(CustomRelease)):
                        print(CustomRelease[index], file=TempExporter)
                    for index in range(len(CustomClean)):
                        print(CustomClean[index], file=TempExporter)
                    print("G1 Z" + str(round(Current_Layer_Height, 3)) + ";Lower nozzle", file=TempExporter)
            print(line, file=TempExporter)
    f.close()
    TempExporter.close()
    try:
        if GSourceFile != "":
            print(Output_Filename)
            if os.path.exists(Output_Filename):
                os.remove(GSourceFile)
                os.rename(Output_Filename, GSourceFile)
            else:
                pass
        else:
            tk.messagebox.showinfo(title='警报', message='错误。请调整打印件位置后重新切片')
    except:
        tk.messagebox.showinfo(title='警报', message='错误。请调整打印件位置后重新切片')
    exit(0)


if __name__ == "__main__":
    main()
# 等2秒再关闭

time.sleep(2)
window.destroy()
window.mainloop()
exit(0)