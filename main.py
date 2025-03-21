# coding=utf-8
import tkinter as tk  # 导入GUI界面函数库
import tkinter.font as tkFont
from tkinter import ttk, scrolledtext
import tkinter.messagebox
import re, os, ctypes, sys
from PIL import Image, ImageTk
import base64
from in_png import img as png1
from tower import Temp_Wiping_Gcode, Temp_Tower_Base_Layer_Gcode
from sys import exit
import toml,argparse
GSourceFile = ""
TomlName=""
Modify_Config_Flag=False
try:
    parser = argparse.ArgumentParser(description='MKP loading')
    parser.add_argument('--Toml', type=str, help='TOML配置文件路径')
    parser.add_argument('--Gcode', type=str, help='Gcode文件路径')
    args = parser.parse_args()
    Modify_Config_Flag = True
    if args.Toml:
        TomlName = args.Toml
        Modify_Config_Flag = False
    if args.Gcode:
        GSourceFile = args.Gcode
    print(args.Gcode,args.Toml,Modify_Config_Flag)

except:
    Modify_Config_Flag=True
    # GSourceFile = "C:\\Users\\Administrator\\Desktop\\GcodeTest\\test.gcode"
ctypes.windll.shcore.SetProcessDpiAwareness(1)
ScaleFactor = ctypes.windll.shcore.GetScaleFactorForDevice(0)
# 创建窗口
def center_window(window):
    window.update_idletasks()
    x = (window.winfo_screenwidth() // 2) - (width // 2)
    y = (window.winfo_screenheight() // 2) - (height // 2)
    window.geometry('+{}+{}'.format(x, y))
window = tk.Tk()
window.title('Markpen v3.1')
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

class para:
    # parameters
    Enable_ironing=None#这是识别是否开启熨烫功能的
    Have_Wiping_Components=None#这是识别是否用内置擦嘴塔的
    # Enable_ironing=True
    # Have_Wiping_Components=True
    Iron_Extrude_Ratio=0#熨烫挤出乘数
    Tower_Extrude_Ratio=0#擦料塔挤出乘数
    Z_Offset = 0  # 笔尖在工作位时比喷嘴更低，这个值是喷嘴与笔尖间的高度差
    Wiping_Gcode = []  # 自定义擦嘴代码
    X_Offset = 0  # 喷嘴与笔尖的X坐标的差值
    Y_Offset = 0  # 喷嘴与笔尖的Y坐标的差值
    Max_Speed = 0  # 最高移动速度
    Ironing_Speed = 0#熨烫速度
    Custom_Unmount_Gcode = []  # 自定义卸载胶箱
    Custom_Mount_Gcode = []  # 自定义装载胶箱
    Tower_Base_Layer_Gcode=[]#擦料塔首层代码
    Crash_Flag=False#程序是否被用户意外结束
    Path_Copy_Button_Flag=False#路径复制按钮是否被点击
    Travel_Speed=0#空驶速度
    Nozzle_Diameter = 0#喷嘴直径
    Wiper_x=0#擦嘴塔的起始X坐标
    Wiper_y=0#擦嘴塔的起始Y坐标
    Preset_Name=""#预设名称
    First_Layer_Height=0#首层层高
    Typical_Layer_Height=0#典型层高（取值来自默认层高）
    First_Layer_Speed=0#首层速度
    Typical_Layer_Speed=0#典型打印速度（取值来自外墙）
    Retract_Length=0#回抽长度
User_Input = []#存用户输入的参数
Output_Filename=""#输出文件名，最终会被更名

def Invert_Flag(Flag):
    newvalue=not Flag.get()
    Flag.set(newvalue)
    print(Flag.get())
def get_preset_values(Mode):
    # 创建主窗口
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    popup = tk.Toplevel(root)
    winWidth = 510
    winHeight = 460
    # 获取屏幕分辨率
    screenWidth = window.winfo_screenwidth()
    screenHeight = window.winfo_screenheight()
    x = int((screenWidth - winWidth) / 2)
    y = int((screenHeight - winHeight) / 2)
    #更改窗口的初始显示位置和大小
    popup.geometry("%sx%s+%s+%s" % (winWidth, winHeight, x, y))
    popup.resizable(width=False, height=False)
    popup.title("配置向导")
    labels = ["涂胶速度限制[MM/S]", "X坐标补偿值[MM]", "Y坐标补偿值[MM]", "喷嘴笔尖高度差[MM]", "自定义工具头获取 G-code", "自定义工具头收起 G-code",
              "开启熨烫功能","熨烫速度[MM/S]","熨烫挤出乘数","使用内置擦嘴塔","擦料塔的起始点"]
    entries = []
    custom_font = tkFont.Font(family="SimHei", size=12)
    root.option_add("*Font", custom_font)
    # 在 tk.Tk() 创建后初始化 BooleanVar
    para.Enable_ironing = tk.BooleanVar(value=False)
    para.Have_Wiping_Components = tk.BooleanVar(value=True)
    
    def Enable_ironing():
        para.Enable_ironing.set(not para.Enable_ironing.get())
        # para.Enable_ironing = not para.Enable_ironing
        print(para.Enable_ironing.get())
    #下面的这个函数还会负责禁用输入框
    def Have_Wiping_Components():
        para.Have_Wiping_Components.set(not para.Have_Wiping_Components.get())
        if para.Have_Wiping_Components.get()!=True:
            entry_x.config(state='disabled', disabledbackground='light grey')
            entry_y.config(state='disabled', disabledbackground='light grey')
        else:
            entry_x.config(state='normal')
            entry_y.config(state='normal')
            pass         
        print(para.Have_Wiping_Components.get())

    def create_right_click_menu(widget):#创建右键菜单
        menu = tk.Menu(widget, tearoff=0)
        menu.add_command(label="剪切", command=lambda: widget.event_generate("<<Cut>>"))
        menu.add_command(label="复制", command=lambda: widget.event_generate("<<Copy>>"))
        menu.add_command(label="粘贴", command=lambda: widget.event_generate("<<Paste>>"))
        menu.add_command(label="删除", command=lambda: widget.delete("sel.first", "sel.last"))
        menu.add_separator()
        menu.add_command(label="全选", command=lambda: widget.event_generate("<<SelectAll>>"))

        def show_menu(event):
            menu.post(event.x_root, event.y_root)

        widget.bind("<Button-3>", show_menu)
    #以下是创建弹窗各个输入框的代码
    for i, label in enumerate(labels):
        if label  not in ["擦嘴代码", "擦料塔首层"]:
            tk.Label(popup, text=label + ":", justify='left', padx=10).grid(row=i, column=0, sticky='w')
        entry = tk.Entry(popup)
        if label in ["自定义工具头获取 G-code", "自定义工具头收起 G-code"]:
            # 对于特定的label，使用scrolledtext.ScrolledText来创建带有滚动条的Text控件
            text_box = scrolledtext.ScrolledText(popup, wrap=tk.WORD, width=10, height=3.5)
            text_box.grid(row=i, column=1, padx=10, sticky='ew')  # sticky='ew' 使控件在列中水平扩展
            create_right_click_menu(text_box)
            # 由于我们使用了scrolledtext.ScrolledText，所以不需要单独添加entries到这个列表中
            entries.append(text_box)
        elif label == "开启熨烫功能":
            ironing_checkbox = tk.Checkbutton(popup, variable=para.Enable_ironing, command=Enable_ironing)
            ironing_checkbox.grid(row=i, column=1, padx=5, sticky='w')  # 与标签左对齐
            # ironing_checkbox.select()
            entries.append(ironing_checkbox)  # 将 BooleanVar 对象添加到 entries 列表中
        elif label == "使用内置擦嘴塔":
            use_wiper_checkbox = tk.Checkbutton(popup, variable=para.Have_Wiping_Components,
                                                command=Have_Wiping_Components)
            use_wiper_checkbox.grid(row=i, column=1, padx=5, sticky='w')  # 与标签左对齐
            
            entries.append(use_wiper_checkbox)  # 将 BooleanVar 对象添加到 entries 列表中
        elif label == "擦料塔的起始点":
            tk.Label(popup, text="擦料塔的起始点：", justify='left', padx=10).grid(row=i, column=0, sticky='w')
            frame = tk.Frame(popup)
            frame.grid(row=i, column=1, padx=5, sticky='w')
            label_x = tk.Label(frame, text="X:")
            label_x.pack(side='left')
            entry_x = tk.Entry(frame, width=6)
            entry_x.pack(side='left', padx=2)
            entry_x.insert(0, "5")
            label_y = tk.Label(frame, text="Y:")
            label_y.pack(side='left')
            entry_y = tk.Entry(frame, width=6)
            entry_y.pack(side='left', padx=2)
            entry_y.insert(0, "5")
            entry_y.config(state='normal')
            entry_x.config(state='normal')
            entries.append((entry_x, entry_y))
        else:
            entry.grid(row=i, column=1, padx=10)
            entries.append(entry)

    use_wiper_checkbox.select()
    
    if Mode == "Modify":#如果是修改模式，还读取配置文件的数据
        for i, label in enumerate(labels):
            if label == "涂胶速度限制[MM/S]":
                entries[i].insert(0, para.Max_Speed)
                # entry.insert(0, para.Max_Speed)
            if label == "X坐标补偿值[MM]":
                entries[i].insert(0, para.X_Offset)
                # entry.insert(0, para.X_Offset)
            if label == "Y坐标补偿值[MM]":
                entries[i].insert(0, para.Y_Offset)
                # entry.insert(0, para.Y_Offset)
            if label == "喷嘴笔尖高度差[MM]":
                entries[i].insert(0, para.Z_Offset)
                # entry.insert(0, para.Z_Offset)
            if label == "熨烫速度[MM/S]":
                entries[i].insert(0, para.Ironing_Speed)
                # entry.insert(0, para.Ironing_Speed)
            if label == "熨烫挤出乘数":
                entries[i].insert(0, para.Iron_Extrude_Ratio)
                # entry.insert(0, para.Iron_Extrude_Ratio)
            if label == "自定义工具头获取 G-code":
                entries[i].insert(tk.END, para.Custom_Mount_Gcode)
                # text_box.insert(tk.END, para.Custom_Mount_Gcode)
            if label == "自定义工具头收起 G-code":
                entries[i].insert(tk.END, para.Custom_Unmount_Gcode)
                # text_box.insert(tk.END, para.Custom_Unmount_Gcode)
            if para.Have_Wiping_Components.get()!=True:
                use_wiper_checkbox.deselect()
            else:
                use_wiper_checkbox.select() 
            if para.Enable_ironing.get()!=True:
                ironing_checkbox.deselect()
            else:
                ironing_checkbox.select()
            if label == "擦料塔的起始点":
                entry_x.delete(0, tk.END)
                entry_y.delete(0, tk.END)
                entry_x.insert(0, para.Wiper_x)
                entry_y.insert(0, para.Wiper_y)

    def on_submit():
        global User_Input
        for entry in entries:
            if isinstance(entry, tk.Entry):
                User_Input.append(entry.get())
            elif isinstance(entry, scrolledtext.ScrolledText):
                try:
                    User_Input.append(entry.get(1.0, tk.END))  # Get text from 1.0 to the end
                except tk.TclError:
                    print("ScrolledText widget has been destroyed.")
                    User_Input.append("")  # Append an empty string if the widget is destroyed
        User_Input.append(para.Enable_ironing.get())
        User_Input.append(para.Have_Wiping_Components.get())
        User_Input.append(entry_x.get())
        User_Input.append(entry_y.get())
        print(User_Input)
        values = 1
        popup.destroy()
        root.quit()  # 关闭弹窗
        return values

    def on_closing():
        # 如果用户点击了关闭按钮，弹出确认对话框
        if tk.messagebox.askokcancel("退出", "您真的要退出吗?"):
            para.Crash_Flag = True
            try:
                popup.destroy()
            except:
                pass
            try:
                window.destroy()
            except:
                pass
            root.quit()  # 关闭弹窗
            return False
    popup.protocol("WM_DELETE_WINDOW", on_closing)    # 绑定关闭事件处理函数到窗口关闭事件
    window.protocol("WM_DELETE_WINDOW", on_closing)
    style = ttk.Style()
    style.configure('Rounded.TButton', roundcorners=25,font="SimHei")  # 设置圆角的大小
    ttk.Button(popup, text="确定", style='Rounded.TButton', command=on_submit).grid(row=len(labels), column=1,
                                                                                    pady=10)
    root.mainloop()
#这个函数用来在documets文件夹下创建一个名为MKPSupport的文件夹
def create_mkpsupport_dir():
    documents_path = os.path.expanduser("~/Documents") # Cross-platform Documents path
    mkpsupport_path = os.path.join(documents_path, "MKPSupport")
    if not os.path.exists(mkpsupport_path):
        os.makedirs(mkpsupport_path)
    return mkpsupport_path
#这个函数用来把User_Input中用户输入的参数赋值给para类中的变量
def read_dialog_input():
    global User_Input   
    # print(User_Input)
    para.Max_Speed = round(float(User_Input[0]), 3)
    para.X_Offset = round(float(User_Input[1]), 3)
    para.Y_Offset = round(float(User_Input[2]), 3)
    para.Z_Offset = round(float(User_Input[3]), 3)
    para.Custom_Mount_Gcode = User_Input[4]
    para.Custom_Unmount_Gcode = User_Input[5]
    para.Enable_ironing.set(User_Input[8])
    para.Ironing_Speed = round(float(User_Input[6]), 3)
    para.Iron_Extrude_Ratio = round(float(User_Input[7]), 3)
    para.Have_Wiping_Components.set(User_Input[9])
    para.Wiper_x = round(float(User_Input[10]), 3)
    para.Wiper_y = round(float(User_Input[11]), 3)
#这个函数用来从传入的filepath读取配置到para类中的变量
def read_toml_config(file_path):
    para.Enable_ironing = tk.BooleanVar(value=False)
    para.Have_Wiping_Components = tk.BooleanVar(value=False)
    para.Wiping_Gcode=Temp_Wiping_Gcode.strip().splitlines()
    para.Tower_Base_Layer_Gcode=Temp_Tower_Base_Layer_Gcode.strip().splitlines()
    with open(file_path, 'r', encoding='utf-8') as f:
        config = toml.load(f)
    if config:
        # 访问配置数据
        toolhead_config = config['toolhead']
        para.Max_Speed = toolhead_config['speed_limit']
        para.offset = toolhead_config['offset']
        para.X_Offset=para.offset['x']
        para.Y_Offset = para.offset['y']
        para.Z_Offset=para.offset['z']
        try:
            para.Custom_Mount_Gcode = toolhead_config['custom_mount_gcode']
        except:
            para.Custom_Mount_Gcode = ";MKPSupport: Mount Gcode\n"
        try:
            para.Custom_Unmount_Gcode = toolhead_config['custom_unmount_gcode']
        except:
            para.Custom_Unmount_Gcode = "M117 MKPSupport: Unmount Gcode\n"
        ironing_config = config['ironing']
        para.Enable_ironing.set(ironing_config['enabled'])
        para.Ironing_Speed = ironing_config['speed']
        para.Iron_Extrude_Ratio = ironing_config['extrusion_multiplier']
        wiping_config = config['wiping']
        para.Have_Wiping_Components.set(wiping_config['have_wiping_components'])
        if para.Have_Wiping_Components.get()==True:
            para.Wiper_x = wiping_config['wiper_x']
            para.Wiper_y = wiping_config['wiper_y']
    
    print("para data:",para.Max_Speed,para.X_Offset,para.Y_Offset,para.Z_Offset,para.Custom_Mount_Gcode,para.Custom_Unmount_Gcode,para.Enable_ironing.get(),para.Ironing_Speed,para.Iron_Extrude_Ratio,para.Have_Wiping_Components.get(),para.Wiper_x,para.Wiper_y)
#这个函数用来创建一个输入框，目前只是用来输入预设名称
def create_input_dialog(title, prompt):
    def on_submit():
        user_input = entry.get()
        if not user_input:
            tk.messagebox.showwarning("警告", "输入不能为空！")
        else:
            para.Preset_Name = user_input
            root.destroy()
            root.quit()
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    custom_font = tkFont.Font(family="SimHei", size=12)
    root.option_add("*Font", custom_font)
    winWidth = 300
    winHeight = 130
    # 获取屏幕分辨率
    screenWidth = window.winfo_screenwidth()
    screenHeight = window.winfo_screenheight()
    x = int((screenWidth - winWidth) / 2)
    y = int((screenHeight - winHeight) / 2)
    #更改窗口的初始显示位置和大小
    root.geometry("%sx%s+%s+%s" % (winWidth, winHeight, x, y))
    root.title(title)
    root.deiconify()
    root.resizable(0, 0)  # 固定窗口大小
    label = tk.Label(root, text=prompt)
    label.pack(padx=10, pady=5)
    entry = tk.Entry(root)
    entry.pack(padx=10, pady=5)
    submit_button = ttk.Button(root, text="确定", command=on_submit, style='Rounded.TButton')
    submit_button.pack(side='bottom',pady=10)
    root.protocol("WM_DELETE_WINDOW", root.quit)
    root.mainloop()
#这个函数用来写入配置到文件名为file_path的文件中    
def write_toml_config(file_path):
    read_dialog_input()
    with open(file_path, 'w', encoding='utf-8') as f:
        if para.Enable_ironing.get()==False:
            Enable_ironing_str="false"
        else:
            Enable_ironing_str="true"
        if para.Have_Wiping_Components.get()==False:
            Use_wiper_str="false"
        else:
            Use_wiper_str="true"
        if isinstance(para.Custom_Mount_Gcode, list):
            para.Custom_Mount_Gcode = "\n".join(para.Custom_Mount_Gcode)
        if isinstance(para.Custom_Unmount_Gcode, list):
            para.Custom_Unmount_Gcode = "\n".join(para.Custom_Unmount_Gcode)
        print("#胶笔配置", file=f)
        print("[toolhead]", file=f)
        print("speed_limit = " + str(para.Max_Speed) + "  #涂胶速度限制 (mm/s)", file=f)
        print("offset = { x = " + str(para.X_Offset) + ", y = " + str(para.Y_Offset) + ", z = " + str(para.Z_Offset) + "}# 笔尖偏移", file=f)
        print("# 自定义工具头获取 G-code", file=f)
        print("custom_mount_gcode = \"\"\"" + "\n" + para.Custom_Mount_Gcode + "\"\"\"", file=f)
        print("# 自定义工具头收起 G-code", file=f)
        print("custom_unmount_gcode = \"\"\"" + "\n" + para.Custom_Unmount_Gcode + "\"\"\"", file=f)
        print("#熨烫设置", file=f)
        print("[ironing]", file=f)
        print("enabled = " + Enable_ironing_str, file=f)
        print("speed = " + str(para.Ironing_Speed), file=f)
        print("extrusion_multiplier = " + str(para.Iron_Extrude_Ratio) + " # 熨烫挤出乘数Ironing extrusion multiplier", file=f)
        print("#擦嘴配置", file=f)
        print("[wiping]", file=f)
        print("have_wiping_components = "+Use_wiper_str+"#使用内置擦嘴塔Enable wiping components",file=f)
        print("wiper_x = "+str(para.Wiper_x),file=f)
        print("wiper_y = "+str(para.Wiper_y),file=f)
#这个函数用来创建一个弹窗，让用户点击按钮复制命令到剪贴板
def copy_user_command():
    root1 = tk.Tk()
    root1.title('文件路径')
    center_window(root1)
    def copy_curr_exe_path():
        root1.clipboard_clear()
        root1.clipboard_append(  '"' + os.path.abspath(sys.executable) + '"'+ ' --Toml ' +'"' +  para.Preset_Name+'"' + " --Gcode " )
        tk.messagebox.showinfo(title='完成', message='路径已复制。软件将自动关闭')
        root1.quit()
    custom_font = tkFont.Font(family="SimHei", size=12)
    root1.option_add("*Font", custom_font)
    style = ttk.Style()
    style.configure('Rounded.TButton', roundcorners=25,font=("SimHei",12))  # 设置圆角的大小
    message = '点击“复制”拷贝程序所在的路径，并粘贴入工艺->其他->后处理脚本框中。'
    label = tk.Label(root1, text=message)
    label.pack()
    # 创建一个框架来包含文本框和滚动条
    frame = tk.Frame(root1)
    frame.pack()

    # 创建文本框
    path_text = tk.Text(frame, height=1, width=50, wrap='none')
    path_text.pack(side='top', fill='x', expand=True)

    # 创建水平滚动条
    scroll_x = tk.Scrollbar(frame, orient='horizontal', command=path_text.xview)
    scroll_x.pack(side='top', fill='x')

    # 将文本框与滚动条关联
    path_text.config(xscrollcommand=scroll_x.set)
    path_text.insert(tk.END, '"' + os.path.abspath(sys.executable) + '"'+ ' --Toml ' +'"' +  para.Preset_Name+'"' + " --Gcode ")
    path_text.pack()
    copy_button = ttk.Button(root1, style='Rounded.TButton',text='复制',command=copy_curr_exe_path)
    # print(para.Path_Copy_Button_Flag)
    copy_button.pack(padx=10, pady=10)
    root1.protocol("WM_DELETE_WINDOW", lambda: root1.destroy())
    root1.mainloop()
#这个函数用来对那些传入Z.9这样子不符合标准数字表示方法的GCode进行处理
def format_xyze_string(text):
    def process_data(match):
        if match:
            return f"{match.group(1)}{float(match.group(2)):.3f}"
        return ""
    text = re.sub(r'(X)([\d.]+)', lambda m: process_data(m), text)
    text = re.sub(r'(Y)([\d.]+)', lambda m: process_data(m), text)
    text = re.sub(r'(E)([\d.]+)', lambda m: process_data(m), text)
    text = re.sub(r'(Z)([\d.]+)', lambda m: process_data(m), text)
    return text
# print(format_xyze_string('G1 X.9 Y.9 Z.9'))

#这个函数用来做Gcode的偏移，也负责E挤出的流量调整
def Process_GCode_Offset(GCommand, x_offset, y_offset,z_offset, Mode):
    if GCommand.find("F") != -1:
        GCommand=GCommand[:GCommand.find("F")]
    GCommand = format_xyze_string(GCommand)
    pattern = r"(X|Y|E|Z)(\d+\.\d+)"  # 匹配X或Y或者E或者Z，后面跟着一个或多个数字和小数点
    match = re.findall(pattern, GCommand)
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
            if Mode=='ironing':
                values[key] = round(float(value) * para.Iron_Extrude_Ratio, 3)
            elif Mode=='tower':
                values[key] = round(float(value) * para.Tower_Extrude_Ratio, 3)
            else:
                values[key] = 12345
        elif key == 'Z' and Mode!='ironing':
            values[key] = round(float(value) + z_offset, 3)
                
    # 替换原文本中的数值
    for key, value in values.items():
        GCommand = re.sub(rf"{key}\d+\.\d+", f"{key}{value}", GCommand)

    GCommand = re.sub("E12345", "", GCommand)

    if Mode!='ironing' and Mode!='tower':
        if (GCommand.find("E") < GCommand.find(";") and GCommand.find(";") != -1 and GCommand.find("E") != -1) or (
                GCommand.find("E") != -1 and GCommand.find(";") == -1):  # 如果E出现在注释；前面或者没有注释但是有E
            GCommand = GCommand[:GCommand.find("E")]
    return GCommand
#这个函数负责获取line里的数字
def Num_Strip(line):
    Source = re.findall(r"\d+\.?\d*", line)
    Source = list(map(float, Source))
    data = Source
    return data

def refresh(self):
    self.destroy()
    self.__init__()
#这是预设管理器的实现部分
def select_toml_file():
    # 创建主窗口
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    folder_path = create_mkpsupport_dir()
    toml_files = [f for f in os.listdir(folder_path) if f.endswith('.toml')]
    Have_Toml_Flag = True
    Create_New_Config = 'no'
    if not toml_files:
        Have_Toml_Flag = False
    # 检查是新建还是修改
    if Have_Toml_Flag!=True:
        Create_New_Config = tk.messagebox.askquestion(title='无可用预设', message='当前文件夹下无可用预设。创建新预设？')
        if Create_New_Config == 'yes':
            new_preset_name=""
            create_input_dialog("新建预设", "请输入新预设的名称:")
            new_preset_name = para.Preset_Name
            get_preset_values("Normal")
            write_toml_config(os.path.join(folder_path, new_preset_name + ".toml"))
        else:
            exit("User cancelled:用户终止")
    #这个函数是负责在刚刚打开以及新建，删除后刷新的
    def refresh_toml_list():
        def on_select(value):
            selected_toml.set(value)
        for widget in selection_dialog.winfo_children():
            widget.destroy()
        
        toml_files = [f for f in os.listdir(folder_path) if f.endswith('.toml')]
        radio_buttons = []
        toml_file_paths = []
        for toml_file in toml_files:
            filePath = os.path.join(folder_path, toml_file)
            toml_file_paths.append(filePath)
            radio_button = tk.Radiobutton(selection_dialog, text=toml_file, variable=selected_toml, value=filePath, command=lambda v=filePath: on_select(v))
            radio_button.pack(anchor='w', padx=10, pady=5)
            radio_buttons.append(radio_button)
        # selected_toml.set(None)
        # selected_toml.set(toml_file_paths[0])
        radio_buttons[0].select()
        selected_toml.set(toml_file_paths[0])
        button_frame = tk.Frame(selection_dialog)
        button_frame.pack(side='bottom', fill='x', pady=10)

        confirm_button = ttk.Button(button_frame, text="确定", command=on_confirm, style='Rounded.TButton')
        confirm_button.pack(side='left', padx=10)

        new_button = ttk.Button(button_frame, text="新建", command=on_new, style='Rounded.TButton')
        new_button.pack(side='left', padx=10)

        edit_button = ttk.Button(button_frame, text="编辑", command=on_edit, style='Rounded.TButton')
        edit_button.pack(side='left', padx=10)

        delete_button = ttk.Button(button_frame, text="删除", command=on_delete, style='Rounded.TButton')
        delete_button.pack(side='left', padx=10)
        


    # 创建选择 toml 文件的对话框
    selection_dialog = tk.Toplevel(root)
    selection_dialog.title("预设管理器")
    selection_dialog.geometry("550x400")
    selected_toml = tk.StringVar()
    def on_confirm():
        para.Preset_Name = selected_toml.get()
        copy_user_command()
        selection_dialog.destroy()
    def on_delete():
        selected_file = selected_toml.get()
        if selected_file:
            Delete_Flag= tk.messagebox.askquestion("提示", f"是否要删除预设: {selected_file}?")
            if Delete_Flag=="yes":
                os.remove(selected_file)
            else:
                pass
            refresh_toml_list()

    def on_edit():
        selected_file = selected_toml.get()
        read_toml_config(selected_file)
        get_preset_values("Modify")
        write_toml_config(selected_file)

    def on_new():
        new_preset_name=""
        create_input_dialog("新建预设", "请输入新预设的名称:")
        new_preset_name = para.Preset_Name
        mkpsupport_path = create_mkpsupport_dir() + "\\" + str(new_preset_name)+ ".toml"
        get_preset_values("Normal")
        write_toml_config(mkpsupport_path)
        refresh_toml_list()
    
    style = ttk.Style()
    style.configure('Rounded.TButton', font=("SimHei", 12), padding=10, relief="flat", borderwidth=1, background="#4CAF50", foreground="white")
    refresh_toml_list()
    root.wait_window(selection_dialog)
#完全废弃的函数
def environment_check():
    pass

def main():
    Layer_Flag = False#不再使用了
    Copy_Flag = False#指示当前的gcode是否应当拷贝
    Act_Flag = False#指示是否应该开始写入mkp相关的涂胶或者熨烫
    InterFace = []#存储接触面
    Current_Layer_Height = 0#当前的Z高度（相对于热床）
    Last_Layer_Height = 0#上一层的Z高度（相对于热床）
    First_layer_Flag=True#是否是首层
    Start_Index=0#接触面开始在哪里
    End_Index=0#结束在哪里
    last_xy_command_in_other_features=""#用来补全移动。因为我们插入的位置前面还有一个空驶
    First_XY_Command_IN_Flag=False#跟下面那个的用途都忘记了
    Last_XY_Command_FE_Flag=True
    Layer_Thickness=0
    #如果用户是修改预设而不是唤起切片，就在这停下
    if Modify_Config_Flag:
        select_toml_file()
        exit("Manager Exit")
    # tk.messagebox.showinfo(title='警报', message="GSourceFile:"+GSourceFile)
    # tk.messagebox.showinfo(title='警报', message="TomlName:"+TomlName)
    read_toml_config(TomlName)
    environment_check()
    Layer_Height_Index = {}#存储接触面的数据，回头在第二次循环还需要用
    para.Ironing_Speed=para.Ironing_Speed*60#换算
    para.Max_Speed=para.Max_Speed*60
    with open(GSourceFile, 'r', encoding='utf-8') as file:
        content = file.readlines()

    #逆序从content中查找参数
    Diameter_Count=0
    for i in range(len(content)):
        CurrGCommand = content[i]
        if CurrGCommand.find("; travel_speed =") != -1:
            para.Travel_Speed = Num_Strip(CurrGCommand)[0]
            Diameter_Count+=1
        if CurrGCommand.find("; nozzle_diameter = ") != -1:
            para.Nozzle_Diameter = Num_Strip(CurrGCommand)[0]
            Diameter_Count+=1
        if CurrGCommand.find("; initial_layer_print_height =") != -1:
            para.First_Layer_Height = Num_Strip(CurrGCommand)[0]
            Diameter_Count+=1
        if CurrGCommand.find("; layer_height = ") != -1:
            para.Typical_Layer_Height = Num_Strip(CurrGCommand)[0]
            Diameter_Count+=1
        if CurrGCommand.find("; initial_layer_speed =") != -1:
            para.First_Layer_Speed = Num_Strip(CurrGCommand)[0]
            Diameter_Count+=1
        if CurrGCommand.find("; outer_wall_speed =") != -1:
            para.Typical_Layer_Speed = Num_Strip(CurrGCommand)[0]
            Diameter_Count+=1
        if CurrGCommand.find("; retraction_length = ") != -1:
            para.Retract_Length = Num_Strip(CurrGCommand)[0]
            Diameter_Count+=1
        if Diameter_Count==7:
            break
    
    with open(GSourceFile, 'r', encoding='utf-8') as file:
        content = file.readlines()
    Output_Filename = GSourceFile + "_Output.gcode"
    TempExporter = open(Output_Filename+'.te', "w", encoding="utf-8")
    #第一次循环。这个循环的主要任务是输出涂胶和熨烫，记录接触面的轨迹方便下一次循环的预涂胶
    for i in range(len(content)):
        CurrGCommand = content[i].strip("\n")
        # if CurrGCommand.find("G1 X") != -1 or CurrGCommand.find("G1 Y") != -1 and Last_XY_Command_FE_Flag:
        #     last_xy_command_in_other_features=CurrGCommand
        if ( CurrGCommand.find("G1 X") != -1 or CurrGCommand.find("G1 Y") != -1 ) and CurrGCommand.find("E") == -1 and Last_XY_Command_FE_Flag:
            last_xy_command_in_other_features=CurrGCommand
        # if i+1<len(content):
        #     NextGCommand = content[i + 1].strip("\n")
        if CurrGCommand.find("; Z_HEIGHT: ") != -1:
            Last_Layer_Height = Current_Layer_Height
            Current_Layer_Height = Num_Strip(CurrGCommand)[0]
            Layer_Thickness=Current_Layer_Height-Last_Layer_Height
            
        if CurrGCommand.find("; FEATURE: Support interface") != -1:
            Copy_Flag=True
            Start_Index=i
            Last_XY_Command_FE_Flag=False
            # print(";LSTXY:"+last_xy_command_in_other_features)
            # print("start_index:",Start_Index)
        if Copy_Flag==True and CurrGCommand.find("; CHANGE_LAYER") != -1:
            #提前结算
            End_Index=i-1
            InterFace.extend(content[Start_Index:End_Index])
            Start_Index=i
            Act_Flag=True
        if CurrGCommand.find("; FEATURE:")!=-1 and CurrGCommand.find("; FEATURE: Support interface") == -1 and Copy_Flag:#这是另外一种挤出
            Copy_Flag=False
            End_Index=i
            InterFace.extend(content[Start_Index:End_Index])
            Act_Flag=True
        if CurrGCommand.find("; CHANGE_LAYER") != -1 and Act_Flag:
            Last_XY_Command_FE_Flag=True
            Act_Flag=False
            # print(len(InterFace))
            InterFaceIroning = []
            InterFaceGlueing = []
            InterFacePreGlueing = []#预涂胶部分
            InterFacePreGlueing.extend(InterFace)
            InterFaceIroning.extend(InterFace)
            InterFaceGlueing.extend(InterFace)
            if para.Enable_ironing.get()==True:
                print(";Rising nozzle to avoid collision", file=TempExporter)
                print("G1 Z" + str(round(Current_Layer_Height+0.5, 3)), file=TempExporter)
                print(";Inposition", file=TempExporter)
                print(Process_GCode_Offset(last_xy_command_in_other_features,0.5*para.Nozzle_Diameter, 0, 0.5,'normal').strip("\n"), file=TempExporter)#Inposition
                print("G1 Z" + str(round(Current_Layer_Height, 3)), file=TempExporter)
                print(";Ironing Started", file=TempExporter)
                print("G1 F"+str(para.Ironing_Speed),file=TempExporter)
                for i in range(len(InterFaceIroning)):
                    if InterFaceIroning[i].find("G1 ") != -1 and InterFaceIroning[i].find("G1 E") == -1 and InterFaceIroning[i].find("G1 F") == -1:
                        InterFaceIroning[i]=Process_GCode_Offset(InterFaceIroning[i], 0.5*para.Nozzle_Diameter, 0, 0,'ironing')
                        InterFaceIroning[i].strip("\n")
                        print(InterFaceIroning[i].strip("\n"), file=TempExporter)
                print(";Ironing Finished", file=TempExporter)
            # print("G92 E0",file=TempExporter)
            print(";Rising Nozzle", file=TempExporter)
            print("G1 Z" + str(round(Current_Layer_Height+para.Z_Offset+3, 3)), file=TempExporter)#Avoid collision

            print(";Mounting Toolhead", file=TempExporter)
            print(para.Custom_Mount_Gcode.strip("\n"), file=TempExporter)
            print(";Toolhead Mounted", file=TempExporter)
            
            print(";Glueing Started", file=TempExporter)
            print(";Inposition", file=TempExporter)
            print("G1 F" + str(para.Travel_Speed*60), file=TempExporter) 
            print(Process_GCode_Offset(last_xy_command_in_other_features, para.X_Offset, para.Y_Offset, para.Z_Offset+3,'normal').strip("\n"), file=TempExporter)#Inposition
            print("G1 Z" + str(round(Current_Layer_Height+para.Z_Offset, 3)), file=TempExporter)#Adjust
            print("G1 F"+str(para.Max_Speed),file=TempExporter)
            First_XY_Command_IN_Flag=True
            for i in range(len(InterFaceGlueing)):
                if InterFaceGlueing[i].find("G1 ") != -1 and InterFaceGlueing[i].find("G1 E") == -1 and InterFaceGlueing[i].find("G1 F") == -1:
                    if InterFaceGlueing[i].find("G1 X") != -1 or InterFaceGlueing[i].find("G1 Y") != -1:
                        Physical_Glueing_Point=Process_GCode_Offset(InterFaceGlueing[i], 0, 0, para.Z_Offset+3,'normal')
                        if First_XY_Command_IN_Flag==True:
                            first_xy_command_in_interface=Physical_Glueing_Point
                            # print(";First XY Command:"+first_xy_command_in_interface)
                            First_XY_Command_IN_Flag=False
                    InterFaceGlueing[i]=Process_GCode_Offset(InterFaceGlueing[i], para.X_Offset, para.Y_Offset, para.Z_Offset,'normal')
                    print(InterFaceGlueing[i].strip("\n"),file=TempExporter)

            print(";Glueing Finished", file=TempExporter)
            print("G1 Z" + str(round(Current_Layer_Height+para.Z_Offset+3, 3)), file=TempExporter)#Avoid collision
            print(";Unmounting Toolhead", file=TempExporter)
            print(para.Custom_Unmount_Gcode.strip("\n"), file=TempExporter)
            print(";Toolhead Unmounted", file=TempExporter)
            print(";Move to the next print start position", file=TempExporter)
            print("G1 F" + str(para.Travel_Speed*60), file=TempExporter) 
            print(Physical_Glueing_Point,file=TempExporter)
            print(";Lowering Nozzle", file=TempExporter)
            print("G1 Z" + str(round(Last_Layer_Height, 3)), file=TempExporter)
            # Insert InterfaceGlueing into Layer_Height_Index
            for i in range(len(InterFacePreGlueing)):
                if InterFacePreGlueing[i].find("G1 ") != -1 and InterFacePreGlueing[i].find("G1 E") == -1 and InterFacePreGlueing[i].find("G1 F") == -1:
                    InterFacePreGlueing[i]=Process_GCode_Offset(InterFacePreGlueing[i], para.X_Offset, para.Y_Offset, para.Z_Offset+Last_Layer_Height-Current_Layer_Height,'normal')
                    
            Layer_Height_Index[Current_Layer_Height] = ['','','','','']
            Layer_Height_Index[Current_Layer_Height][0]= InterFacePreGlueing.copy()
            Layer_Height_Index[Current_Layer_Height][1]= Last_Layer_Height
            Layer_Height_Index[Current_Layer_Height][2]= Process_GCode_Offset(last_xy_command_in_other_features, para.X_Offset, para.Y_Offset, para.Z_Offset+3,'normal').strip("\n")
            Layer_Height_Index[Current_Layer_Height][3]=Process_GCode_Offset(last_xy_command_in_other_features,0, 0, para.Z_Offset+3,'normal').strip("\n")
            Layer_Height_Index[Current_Layer_Height][4]=Layer_Thickness
            InterFaceGlueing.clear()
            InterFaceIroning.clear()
            InterFacePreGlueing.clear()
            InterFace.clear()
        print(CurrGCommand, file=TempExporter)
        pass
    TempExporter.close()

    #输出的预涂胶代码
    Trigger_Flag=False
    Tower_Flag=True
    FirstLayer_Tower_Height=0
    First_layer_Tower_Flag=True
    First_layer_Flag=True
    Last_Layer_Height=0
    Last_Key=max(Layer_Height_Index.keys())
    # print("Last Key:",Last_Key)
    Output_Filename = GSourceFile + "_Output.gcode"
    with open(Output_Filename+'.te', 'r', encoding='utf-8') as file:
        content = file.readlines()
    GcodeExporter = open(Output_Filename, "w", encoding="utf-8")
    for i in range(len(content)):
        CurrGCommand = content[i].strip("\n")
        if CurrGCommand.find("; Z_HEIGHT: ") != -1:
            Last_Layer_Height = Current_Layer_Height
            Current_Layer_Height = Num_Strip(CurrGCommand)[0]
            if Current_Layer_Height in Layer_Height_Index and Current_Layer_Height>0.4:
                Trigger_Flag=True
            if para.Have_Wiping_Components.get()==True and First_layer_Flag==True and Current_Layer_Height>0.01:
                First_layer_Flag=False
                FirstLayer_Tower_Height=Current_Layer_Height
            if Current_Layer_Height<Last_Key+0.4:
                Tower_Flag=True
        #输出首层塔代码
        if CurrGCommand.find("; CHANGE_LAYER") != -1 and First_layer_Tower_Flag==True and para.Have_Wiping_Components.get()==True:
            First_layer_Tower_Flag=False
            print("G1 Z" + str(round(para.First_Layer_Height, 3) )+ ";TowerBase Z", file=GcodeExporter)#Adjust z height
            para.Tower_Extrude_Ratio = round(para.First_Layer_Height/ 0.2, 3)
            print("G1 F" + str(para.Travel_Speed*60), file=GcodeExporter) 
            for j in range(len(para.Tower_Base_Layer_Gcode)):
                if para.Tower_Base_Layer_Gcode[j].find("EXTRUDER_REFILL")!=-1:
                    print("G92 E0",file=GcodeExporter)
                    print("G1 E"+str(para.Retract_Length),file=GcodeExporter)
                    print("G92 E0",file=GcodeExporter)
                elif para.Tower_Base_Layer_Gcode[j].find("EXTRUDER_RETRACT")!=-1:
                    print("G92 E0",file=GcodeExporter)
                    print("G1 E-"+str(para.Retract_Length),file=GcodeExporter)
                    print("G92 E0",file=GcodeExporter)
                elif para.Tower_Base_Layer_Gcode[j].find("G92 E0") != -1:
                    print("G92 E0",file=GcodeExporter)
                elif para.Tower_Base_Layer_Gcode[j].find("G1 ") != -1 and para.Tower_Base_Layer_Gcode[j].find("G1 E") == -1 and para.Tower_Base_Layer_Gcode[j].find("G1 F") == -1:
                    # print(para.Tower_Base_Layer_Gcode[1])
                    TowerGCTemp=Process_GCode_Offset(para.Tower_Base_Layer_Gcode[j],para.Wiper_x-5, para.Wiper_y-5, 0,'tower')
                    # para.Tower_Base_Layer_Gcode[j] = Process_GCode_Offset(para.Tower_Base_Layer_Gcode[j],0, 0, 0,'tower')
                    print(TowerGCTemp.strip("\n"), file=GcodeExporter)
                elif para.Tower_Base_Layer_Gcode[j].find("G1 F9600") != -1:
                    print("G1 F" + str(para.First_Layer_Speed*60), file=GcodeExporter)
            print("G1 F" + str(para.Travel_Speed*60), file=GcodeExporter) 
        
        if Trigger_Flag==True and CurrGCommand.find("; update layer progress") != -1 and Layer_Height_Index[Current_Layer_Height][0] != []:
            Trigger_Flag=False
            print(";Rising Nozzle", file=GcodeExporter)
            print("G1 Z" + str(round(Layer_Height_Index[Current_Layer_Height][1]+para.Z_Offset+3, 3)), file=GcodeExporter)#Avoid collision
            
            print(";Mounting Toolhead", file=GcodeExporter)
            print(para.Custom_Mount_Gcode.strip("\n"), file=GcodeExporter)
            print(";Toolhead Mounted", file=GcodeExporter)
            
            print(";Inposition", file=GcodeExporter)
            print("G1 F" + str(para.Travel_Speed*60), file=GcodeExporter) 
            print(Layer_Height_Index[Current_Layer_Height][2], file=GcodeExporter)
            print(";Adjusting Nozzle", file=GcodeExporter)
            print("G1 Z" + str(round(Layer_Height_Index[Current_Layer_Height][1]+para.Z_Offset, 3)), file=GcodeExporter)
            print(";Preglueing Started", file=GcodeExporter)
            print("G1 F" + str(para.Max_Speed), file=GcodeExporter)
            for j in range(len(Layer_Height_Index[Current_Layer_Height][0])):

                if Layer_Height_Index[Current_Layer_Height][0][j].find("G1 ") != -1 and Layer_Height_Index[Current_Layer_Height][0][j].find("G1 E") == -1 and Layer_Height_Index[Current_Layer_Height][0][j].find("G1 F") == -1:
                    # Layer_Height_Index[Current_Layer_Height][0][j] = Process_GCode_Offset(Layer_Height_Index[Current_Layer_Height][0][j], para.X_Offset, para.Y_Offset, para.Z_Offset,'normal')
                    print(Layer_Height_Index[Current_Layer_Height][0][j].strip("\n"), file=GcodeExporter)
            Layer_Height_Index[Current_Layer_Height][0].clear()
            print(";Preglueing Finished", file=GcodeExporter)
            print(";Unmounting Toolhead", file=GcodeExporter)
            print(para.Custom_Unmount_Gcode.strip("\n"), file=GcodeExporter)
            print(";Toolhead Unmounted", file=GcodeExporter)
        #输出后续塔代码
        if CurrGCommand.find("; update layer progress") != -1 and para.Have_Wiping_Components.get()==True and Tower_Flag==True and First_layer_Tower_Flag==False:
            Tower_Flag=False
            print("G1 F" + str(para.Travel_Speed*60), file=GcodeExporter)
            print("G1 Z"+ str(round(Current_Layer_Height, 3))+";Tower Z", file=GcodeExporter)
            para.Tower_Extrude_Ratio=round((Current_Layer_Height-Last_Layer_Height) / 0.2,3)
            if para.Tower_Extrude_Ratio<0 or para.Tower_Extrude_Ratio==0:
                para.Tower_Extrude_Ratio=round(para.Typical_Layer_Height / 0.2, 3)
            for j in range(len(para.Wiping_Gcode)):
                # if para.Wiping_Gcode[j].find("G1 ") != -1 and para.Wiping_Gcode[j].find("G1 E") == -1 and para.Wiping_Gcode[j].find("G1 F") == -1:
                if para.Wiping_Gcode[j].find("G1 F9600") != -1:#替换为用户自己切片的外墙速度
                    print("G1 F" + str(para.Typical_Layer_Speed*60), file=GcodeExporter)
                elif para.Wiping_Gcode[j].find("EXTRUDER_REFILL")!=-1:#补偿挤出
                    print("G92 E0",file=GcodeExporter)
                    print("G1 E"+str(para.Retract_Length),file=GcodeExporter)
                    print("G92 E0",file=GcodeExporter)
                elif para.Wiping_Gcode[j].find("EXTRUDER_RETRACT")!=-1:#预防性回抽
                    print("G92 E0",file=GcodeExporter)
                    print("G1 E-"+str(para.Retract_Length),file=GcodeExporter)
                    print("G92 E0",file=GcodeExporter)
                elif para.Wiping_Gcode[j].find("G1 E-.21 F5400") != -1:
                    print("G1 E-.21 F5400",file=GcodeExporter)
                elif para.Wiping_Gcode[j].find("G1 E.3 F5400") != -1:
                    print("G1 E.3 F5400",file=GcodeExporter)
                elif para.Wiping_Gcode[j].find("G92 E0") != -1:
                    print("G92 E0",file=GcodeExporter)
                else:
                    TowerGCTemp = Process_GCode_Offset(para.Wiping_Gcode[j], para.Wiper_x-5, para.Wiper_y-5, 0,'tower')
                    print(TowerGCTemp.strip("\n"),file=GcodeExporter)
            print("G1 F" + str(para.Travel_Speed*60), file=GcodeExporter)
        print(CurrGCommand, file=GcodeExporter)
    GcodeExporter.close()
    try:
        os.remove(GSourceFile)
        os.remove(Output_Filename+'.te')
        os.rename(Output_Filename, GSourceFile)
    except:
        tk.messagebox.showinfo(title='警报', message='错误')
    exit(0)

if __name__ == "__main__":
    main()
# 等2秒再关闭
window.destroy()
window.mainloop()
exit(0)