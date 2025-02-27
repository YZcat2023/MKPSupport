# coding=utf-8
import tkinter as tk  # 导入GUI界面函数库
import tkinter.font as tkFont
from tkinter import ttk, scrolledtext
import tkinter.messagebox
import re, os, time, ctypes, sys
from PIL import Image, ImageTk
import base64
from in_png import img as png1
from sys import exit
import toml,argparse
GSourceFile = ""
Modify_Config_Flag=False
try:
    GSourceFile = sys.argv[1]
    print(GSourceFile)
except:
    Modify_Config_Flag=True
    # pass
    # # sys.exit("Not called by slicers")
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
    Enable_ironing=None
    Have_Wiping_Components=None
    # Enable_ironing=True
    # Have_Wiping_Components=True
    Iron_Extrude_Ratio=0
    Z_Offset = 0  # 笔尖在工作位时比喷嘴更低，这个值是喷嘴与笔尖间的高度差
    Wiping_Gcode = []  # 自定义擦嘴代码
    X_Offset = 0  # 喷嘴与笔尖的X坐标的差值
    Y_Offset = 0  # 喷嘴与笔尖的Y坐标的差值
    Max_Speed = 0  # 最高移动速度
    Ironing_Speed = 0#熨烫速度
    Custom_Unmount_Gcode = []  # 自定义收回（收回笔杆）
    Custom_Mount_Gcode = []  # 自定义锁定（放下笔杆）
    Tower_Base_Layer_Gcode=[]
    Crash_Flag=False
    Path_Copy_Button_Flag=False
User_Input = []
Output_Filename=""

def Invert_Flag(Flag):
    newvalue=not Flag.get()
    Flag.set(newvalue)
    print(Flag.get())
def get_preset_values():
    # 创建主窗口
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口

    popup = tk.Toplevel(root)
    # center_window(popup)
    popup.resizable(width=False, height=False)
    popup.title("配置向导")
    labels = ["涂胶速度限制[MM/S]", "X坐标补偿值[MM]", "Y坐标补偿值[MM]", "喷嘴笔尖高度差[MM]", "自定义工具头获取 G-code", "自定义工具头收起 G-code",
              "开启熨烫功能","熨烫速度[MM/S]","熨烫挤出乘数","使用擦嘴组件","擦嘴代码","擦料塔首层"]
    entries = []
    custom_font = tkFont.Font(family="SimHei", size=12)
    root.option_add("*Font", custom_font)
    # 在 tk.Tk() 创建后初始化 BooleanVar
    para.Enable_ironing = tk.BooleanVar(value=False)
    para.Have_Wiping_Components = tk.BooleanVar(value=False)
    def Enable_ironing():
        para.Enable_ironing.set(not para.Enable_ironing.get())
        # para.Enable_ironing = not para.Enable_ironing
        print(para.Enable_ironing.get())

    def Have_Wiping_Components():
        para.Have_Wiping_Components.set(not para.Have_Wiping_Components.get())
        # para.Have_Wiping_Components = not para.Have_Wiping_Components
        print(para.Have_Wiping_Components.get())
    def create_right_click_menu(widget):
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
    for i, label in enumerate(labels):
        tk.Label(popup, text=label + ":", justify='left', padx=10).grid(row=i, column=0, sticky='w')
        entry = tk.Entry(popup)
        if label in ["自定义工具头获取 G-code", "自定义工具头收起 G-code", "擦嘴代码", "擦料塔首层"]:
            # 对于特定的label，使用scrolledtext.ScrolledText来创建带有滚动条的Text控件
            text_box = scrolledtext.ScrolledText(popup, wrap=tk.WORD, width=10, height=3.5)
            text_box.grid(row=i, column=1, padx=10, sticky='ew')  # sticky='ew' 使控件在列中水平扩展
            # 由于我们使用了scrolledtext.ScrolledText，所以不需要单独添加entries到这个列表中
            create_right_click_menu(text_box)
            entries.append(text_box)
        elif label == "开启熨烫功能":
            ironing_checkbox = tk.Checkbutton(popup, variable=para.Enable_ironing, command=Enable_ironing)
            ironing_checkbox.grid(row=i, column=1, padx=5, sticky='w')  # 与标签左对齐
            # ironing_checkbox.select()
            entries.append(ironing_checkbox)  # 将 BooleanVar 对象添加到 entries 列表中
        elif label == "使用擦嘴组件":
            use_wiper_checkbox = tk.Checkbutton(popup, variable=para.Have_Wiping_Components,
                                                command=Have_Wiping_Components)
            use_wiper_checkbox.grid(row=i, column=1, padx=5, sticky='w')  # 与标签左对齐
            # use_wiper_checkbox.select()
            entries.append(use_wiper_checkbox)  # 将 BooleanVar 对象添加到 entries 列表中
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
        User_Input.append(para.Enable_ironing.get())
        User_Input.append(para.Have_Wiping_Components.get())
        print(User_Input)
        values = 1
        popup.destroy()
        root.quit()  # 关闭弹窗
        return values

    def on_closing():
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
    


    # 绑定关闭事件处理函数到窗口关闭事件
    popup.protocol("WM_DELETE_WINDOW", on_closing)
    window.protocol("WM_DELETE_WINDOW", on_closing)
    style = ttk.Style()
    style.configure('Rounded.TButton', roundcorners=25,font=("SimHei",12))  # 设置圆角的大小
    ttk.Button(popup, text="确定", style='Rounded.TButton', command=on_submit).grid(row=len(labels), column=1,
                                                                                    pady=10)
    # 进入主循环，等待用户操作
    root.mainloop()
    root.destroy()
    # 这里正常情况下不会执行，因为mainloop会阻塞，直到窗口关闭

def modify_preset_values():
    # 创建主窗口
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    popup = tk.Toplevel(root)
    # center_window(popup)
    popup.resizable(width=False, height=False)
    popup.title("配置向导")
    labels = ["涂胶速度限制[MM/S]", "X坐标补偿值[MM]", "Y坐标补偿值[MM]", "喷嘴笔尖高度差[MM]", "自定义工具头获取 G-code", "自定义工具头收起 G-code",
              "开启熨烫功能","熨烫速度[MM/S]","熨烫挤出乘数","使用擦嘴组件","擦嘴代码","擦料塔首层"]
    entries = []
    custom_font = tkFont.Font(family="SimHei", size=12)
    root.option_add("*Font", custom_font)
    # 在 tk.Tk() 创建后初始化 BooleanVar
    # para.Enable_ironing = tk.BooleanVar(value=True)
    # para.Have_Wiping_Components = tk.BooleanVar(value=True)
    def Enable_ironing():
        para.Enable_ironing.set(not para.Enable_ironing.get())
        # para.Enable_ironing = not para.Enable_ironing
        print(para.Enable_ironing.get())

    def Have_Wiping_Components():
        para.Have_Wiping_Components.set(not para.Have_Wiping_Components.get())
        # para.Have_Wiping_Components = not para.Have_Wiping_Components
        print(para.Have_Wiping_Components.get())
    def create_right_click_menu(widget):
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
    for i, label in enumerate(labels):
        tk.Label(popup, text=label + ":", justify='left', padx=10).grid(row=i, column=0, sticky='w')
        entry = tk.Entry(popup)
        if label in ["自定义工具头获取 G-code", "自定义工具头收起 G-code", "擦嘴代码", "擦料塔首层"]:
            # 对于特定的label，使用scrolledtext.ScrolledText来创建带有滚动条的Text控件
            text_box = scrolledtext.ScrolledText(popup, wrap=tk.WORD, width=10, height=3.5)
            text_box.grid(row=i, column=1, padx=10, sticky='ew')  # sticky='ew' 使控件在列中水平扩展
            create_right_click_menu(text_box)
            # 由于我们使用了scrolledtext.ScrolledText，所以不需要单独添加entries到这个列表中
            entries.append(text_box)
        elif label == "开启熨烫功能":
            ironing_checkbox = tk.Checkbutton(popup, variable=para.Enable_ironing, command=Enable_ironing)
            ironing_checkbox.grid(row=i, column=1, padx=5, sticky='w')  # 与标签左对齐
            if para.Enable_ironing.get():
                ironing_checkbox.select()
                para.Enable_ironing.set(True)
            entries.append(ironing_checkbox)  # 将 BooleanVar 对象添加到 entries 列表中
        elif label == "使用擦嘴组件":
            use_wiper_checkbox = tk.Checkbutton(popup, variable=para.Have_Wiping_Components,
                                                command=Have_Wiping_Components)
            use_wiper_checkbox.grid(row=i, column=1, padx=5, sticky='w')  # 与标签左对齐
            if para.Have_Wiping_Components.get():
                use_wiper_checkbox.select()
                para.Have_Wiping_Components.set(True)
            entries.append(use_wiper_checkbox)  # 将 BooleanVar 对象添加到 entries 列表中
        else:
            entry.grid(row=i, column=1, padx=10)
            entries.append(entry)
        if label == "涂胶速度限制[MM/S]":
            entry.insert(0, para.Max_Speed)
        if label == "X坐标补偿值[MM]":
            entry.insert(0, para.X_Offset)
        if label == "Y坐标补偿值[MM]":
            entry.insert(0, para.Y_Offset)
        if label == "喷嘴笔尖高度差[MM]":
            entry.insert(0, para.Z_Offset)
        if label == "熨烫速度[MM/S]":
            entry.insert(0, para.Ironing_Speed)
        if label == "熨烫挤出乘数":
            entry.insert(0, para.Iron_Extrude_Ratio)
        if label == "自定义工具头获取 G-code":
            text_box.insert(tk.END, para.Custom_Mount_Gcode)
        if label == "自定义工具头收起 G-code":
            text_box.insert(tk.END, para.Custom_Unmount_Gcode)
        if label == "擦嘴代码":
            text_box.insert(tk.END, para.Wiping_Gcode)
        if label == "擦料塔首层":
            text_box.insert(tk.END, para.Tower_Base_Layer_Gcode)

    def on_submit():
        global User_Input
        for entry in entries:
            if isinstance(entry, tk.Entry):
                User_Input.append(entry.get())
            elif isinstance(entry, scrolledtext.ScrolledText):
                User_Input.append(entry.get(1.0, tk.END))  # Get text from 1.0 to the end
        User_Input.append(para.Enable_ironing.get())
        User_Input.append(para.Have_Wiping_Components.get())
        # print(User_Input)
        values = 1
        popup.destroy()
        root.quit()  # 关闭弹窗
        return values

    def on_closing():
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

    # 绑定关闭事件处理函数到窗口关闭事件
    popup.protocol("WM_DELETE_WINDOW", on_closing)
    window.protocol("WM_DELETE_WINDOW", on_closing)
    style = ttk.Style()
    style.configure('Rounded.TButton', roundcorners=25,font="SimHei")  # 设置圆角的大小
    ttk.Button(popup, text="确定", style='Rounded.TButton', command=on_submit).grid(row=len(labels), column=1,
                                                                                    pady=10)
    # 进入主循环，等待用户操作
    root.mainloop()
    root.destroy()
    # 这里正常情况下不会执行，因为mainloop会阻塞，直到窗口关闭

def create_mkpsupport_dir():
    documents_path = os.path.expanduser("~/Documents") # Cross-platform Documents path
    mkpsupport_path = os.path.join(documents_path, "MKPSupport")
    if not os.path.exists(mkpsupport_path):
        os.makedirs(mkpsupport_path)
    return mkpsupport_path

def read_toml_config(file_path):
    para.Enable_ironing = tk.BooleanVar(value=False)
    para.Have_Wiping_Components = tk.BooleanVar(value=False)
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
        para.Custom_Mount_Gcode = toolhead_config['custom_mount_gcode']
        para.Custom_Unmount_Gcode = toolhead_config['custom_unmount_gcode']
        ironing_config = config['ironing']
        para.Enable_ironing.set(ironing_config['enabled'])
        para.Ironing_Speed = ironing_config['speed']
        para.Iron_Extrude_Ratio = ironing_config['extrusion_multiplier']
        wiping_config = config['wiping']
        para.Have_Wiping_Components.set(wiping_config['have_wiping_components'])
        para.Wiping_Gcode= wiping_config['wiping_gcode']
        para.Tower_Base_Layer_Gcode = wiping_config['tower_base_layer_gcode']
        # print(para.Enable_ironing.get())
        # print(para.Have_Wiping_Components.get())



def environment_check():  # 后处理前的操作
    global Output_Filename, GSourceFile , Modify_Config_Flag
    mkpsupport_path=create_mkpsupport_dir()+"\\" + "Mrkcon.toml"
    if os.path.exists(mkpsupport_path):
        ConfigReader = open(mkpsupport_path)
    # 如果没有的话:
    else:
        Create_New_Config = tk.messagebox.askquestion(title='无可用预设', message='当前文件夹下无可用预设。创建新预设？')
        if Create_New_Config == 'yes':
            with open(mkpsupport_path, "w",encoding="utf-8") as ConfigExporter:
                get_preset_values()
                if para.Crash_Flag==True:
                    ConfigExporter.close()
                    os.remove(mkpsupport_path)
                    exit("User cancel")
                if User_Input[10]==False:
                    Enable_ironing_str="false"
                else:
                    Enable_ironing_str="true"
                if User_Input[11]==False:
                    Use_wiper_str="false"
                else:
                    Use_wiper_str="true"
                print("#胶笔配置", file=ConfigExporter)
                print("[toolhead]", file=ConfigExporter)
                print("speed_limit = "+str(User_Input[0])+"  #涂胶速度限制 (mm/s)", file=ConfigExporter)
                print("offset = { x = "+str(User_Input[1])+", y = "+str(User_Input[2])+", z = "+str(User_Input[3])+"}# 笔尖偏移", file=ConfigExporter)
                print("# 自定义工具头获取 G-code", file=ConfigExporter)
                print("custom_mount_gcode = \"\"\"" + "\n"+str(User_Input[4])+"\"\"\"", file=ConfigExporter)
                print("# 自定义工具头收起 G-code", file=ConfigExporter)
                print("custom_unmount_gcode = \"\"\""+ "\n"+str(User_Input[5])+"\"\"\"", file=ConfigExporter)
                print("#熨烫设置", file=ConfigExporter)
                print("[ironing]",file=ConfigExporter)
                print("enabled = "+ Enable_ironing_str,file=ConfigExporter)
                print("speed = " + str(User_Input[6]),file=ConfigExporter)
                print("extrusion_multiplier = "+ str(User_Input[7])+" # 熨烫挤出乘数Ironing extrusion multiplier",file= ConfigExporter)
                print("#擦嘴配置", file=ConfigExporter)
                print("[wiping]", file=ConfigExporter)
                print("have_wiping_components = "+Use_wiper_str+"#使用擦嘴组件Enable wiping components",file=ConfigExporter)
                print("wiping_gcode = \"\"\"" + "\n"+ str(User_Input[8])+"\n"+"\"\"\"",file=ConfigExporter)
                print("tower_base_layer_gcode =  \"\"\""+ "\n"+ str(User_Input[9])+"\n"+"\"\"\"", file=ConfigExporter)
            ConfigExporter.close()
            root1 = tk.Tk()
            root1.title('文件路径')
            center_window(root1)
            def copy_curr_exe_path():
                root1.clipboard_clear()
                root1.clipboard_append( '"' + os.path.abspath(sys.executable) + '"')
                tk.messagebox.showinfo(title='完成', message='路径已复制。软件将自动关闭')
                root1.destroy()
                sys.exit("Data Fetched")
                # root1.destroy()
            custom_font = tkFont.Font(family="SimHei", size=12)
            root1.option_add("*Font", custom_font)
            style = ttk.Style()
            style.configure('Rounded.TButton', roundcorners=25,font=("SimHei",12))  # 设置圆角的大小
            message = '点击“复制”拷贝程序所在的路径，并粘贴入工艺->其他->后处理脚本框中。'
            label = tk.Label(root1, text=message)
            label.pack()
            # 创建一个文本框来显示路径
            path_text = tk.Text(root1, height=1, width=50)
            path_text.insert(tk.END, '"' + os.path.abspath(sys.executable) + '"')
            path_text.pack()
            copy_button = ttk.Button(root1, style='Rounded.TButton',text='复制',command=copy_curr_exe_path)
            # print(para.Path_Copy_Button_Flag)
            copy_button.pack(padx=10, pady=10)
            root1.protocol("WM_DELETE_WINDOW", lambda: root1.destroy())
            root1.mainloop()
        else:
            sys.exit("User cancelled:用户终止")
    # read_toml_config(mkpsupport_path)
    # 读入数据
    try:
       read_toml_config(mkpsupport_path)
    except:
        DeleteConfig=tk.messagebox.askquestion(title='错误', message='您填写的预设参数不合法。需要删除这份预设吗？')
        if DeleteConfig=="yes":
            ConfigReader.close()
            os.remove(mkpsupport_path)
            sys.exit("Illegal Input")
            # ConfigExporter=open(mkpsupport_path, "w", encoding="utf-8")
            # if para.Crash_Flag == True:
            #     ConfigExporter.close()
            #     os.remove(mkpsupport_path)
            #     exit("User cancel")
            # else:
            #     ConfigExporter.close()
            #     exit("Data fetched")
        else:
            sys.exit("Illegal Input")

    #检查是否要求修改配置文件
    if Modify_Config_Flag:
        M01 = tk.messagebox.askquestion(title='提示', message='程序未由切片软件拉起。您想要修改预设吗？')
        if M01!="no":
            with open(mkpsupport_path, "r+", encoding="utf-8") as ConfigExporter:
                modify_preset_values()
                if para.Crash_Flag == True:
                    ConfigExporter.close()
                    # os.remove(mkpsupport_path)
                    exit("User cancel")
                if User_Input[10] == False:
                    Enable_ironing_str = "false"
                else:
                    Enable_ironing_str = "true"
                if User_Input[11] == False:
                    Use_wiper_str = "false"
                else:
                    Use_wiper_str = "true"
                print("#胶笔配置", file=ConfigExporter)
                print("[toolhead]", file=ConfigExporter)
                print("speed_limit = " + str(User_Input[0]) + "  #涂胶速度限制 (mm/s)", file=ConfigExporter)
                print("offset = { x = " + str(User_Input[1]) + ", y = " + str(User_Input[2]) + ", z = " + str(
                    User_Input[3]) + "}# 笔尖偏移", file=ConfigExporter)
                print("# 自定义工具头获取 G-code", file=ConfigExporter)
                print("custom_mount_gcode = \"\"\"" + "\n" + str(User_Input[4][:-1]) + "\"\"\"", file=ConfigExporter)
                print("# 自定义工具头收起 G-code", file=ConfigExporter)
                print("custom_unmount_gcode = \"\"\"" + "\n" + str(User_Input[5][:-1]) + "\"\"\"", file=ConfigExporter)
                print("#熨烫设置", file=ConfigExporter)
                print("[ironing]", file=ConfigExporter)
                print("enabled = " + Enable_ironing_str, file=ConfigExporter)
                print("speed = " + str(User_Input[6]), file=ConfigExporter)
                print("extrusion_multiplier = " + str(User_Input[7]) + " # 熨烫挤出乘数Ironing extrusion multiplier",
                      file=ConfigExporter)
                print("#擦嘴配置", file=ConfigExporter)
                print("[wiping]", file=ConfigExporter)
                print("have_wiping_components = " + Use_wiper_str + "#使用擦嘴组件Enable wiping components",
                      file=ConfigExporter)
                print(
                    "wiping_gcode = \"\"\"" + "\n" + str(User_Input[8][:-1])+ "\"\"\"",
                    file=ConfigExporter)
                print("tower_base_layer_gcode =  \"\"\"" + "\n" + str(
                    User_Input[9][:-1]) + "\"\"\"",
                      file=ConfigExporter)
            ConfigExporter.close()



            root1 = tk.Tk()
            root1.title('文件路径')
            center_window(root1)
            def copy_curr_exe_path():
                root1.clipboard_clear()
                root1.clipboard_append( '"' + os.path.abspath(sys.executable) + '"')
                tk.messagebox.showinfo(title='完成', message='路径已复制。软件将自动关闭')
                root1.destroy()
                sys.exit("Data Fetched")
                # root1.destroy()
            custom_font = tkFont.Font(family="SimHei", size=12)
            root1.option_add("*Font", custom_font)
            style = ttk.Style()
            style.configure('Rounded.TButton', roundcorners=25,font=("SimHei",12))  # 设置圆角的大小
            message = '点击“复制”拷贝程序所在的路径，并粘贴入工艺->其他->后处理脚本框中。'
            label = tk.Label(root1, text=message)
            label.pack()
            # 创建一个文本框来显示路径
            path_text = tk.Text(root1, height=1, width=50)
            path_text.insert(tk.END, '"' + os.path.abspath(sys.executable) + '"')
            path_text.pack()
            copy_button = ttk.Button(root1, style='Rounded.TButton',text='复制',command=copy_curr_exe_path)
            # print(para.Path_Copy_Button_Flag)
            copy_button.pack(padx=10, pady=10)
            root1.protocol("WM_DELETE_WINDOW", lambda: root1.destroy())
            root1.mainloop()
        else:
            sys.exit("Refused")

    Output_Filename = GSourceFile + "_Output.gcode"
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
            else:
                values[key] = 12345
        elif key == 'Z' and Mode!='ironing':
            values[key] = round(float(value) + z_offset, 3)
                
    # 替换原文本中的数值
    for key, value in values.items():
        GCommand = re.sub(rf"{key}\d+\.\d+", f"{key}{value}", GCommand)

    GCommand = re.sub("E12345", "", GCommand)

    if Mode!='ironing':
        if (GCommand.find("E") < GCommand.find(";") and GCommand.find(";") != -1 and GCommand.find("E") != -1) or (
                GCommand.find("E") != -1 and GCommand.find(";") == -1):  # 如果E出现在注释；前面或者没有注释但是有E
            GCommand = GCommand[:GCommand.find("E")]
        # if (GCommand.find("Z") < GCommand.find(";") and GCommand.find(";") != -1 and GCommand.find("Z") != -1) or (
        #         GCommand.find("Z") != -1 and GCommand.find(";") == -1):  # 如果E出现在注释；前面或者没有注释但是有E
        #     GCommand = GCommand[:GCommand.find("Z")]
    return GCommand

def Num_Strip(line):
    Source = re.findall(r"\d+\.?\d*", line)
    Source = list(map(float, Source))
    data = Source
    return data


def main():
    Layer_Flag = False
    Copy_Flag = False
    Act_Flag = False
    InterFace = []
    Current_Layer_Height = 0
    Last_Layer_Height = 0
    First_layer_Flag=True
    Start_Index=0
    End_Index=0
    first_xy_command_in_interface=""
    last_xy_command_in_other_features=""
    First_XY_Command_IN_Flag=False
    Last_XY_Command_FE_Flag=True
    environment_check()
    Layer_Height_Index = {}
    para.Ironing_Speed=para.Ironing_Speed*60
    para.Max_Speed=para.Max_Speed*60
    with open(GSourceFile, 'r', encoding='utf-8') as file:
        content = file.readlines()
    # Output_Filename="output.gcode"
    TempExporter = open(Output_Filename+'.te', "w", encoding="utf-8")
    # print(";Generated by Markpen v3.1")
    for i in range(len(content)):
        CurrGCommand = content[i].strip("\n")
        # if CurrGCommand.find("G1 X") != -1 or CurrGCommand.find("G1 Y") != -1 and Last_XY_Command_FE_Flag:
        #     last_xy_command_in_other_features=CurrGCommand
        if ( CurrGCommand.find("G1 X") != -1 or CurrGCommand.find("G1 Y") != -1 ) and CurrGCommand.find("E") == -1 and Last_XY_Command_FE_Flag:
            last_xy_command_in_other_features=CurrGCommand
        # if i+1<len(content):
        #     NextGCommand = content[i + 1].strip("\n")
        if CurrGCommand.find(";Z:") != -1:
            Last_Layer_Height = Current_Layer_Height
            Current_Layer_Height = Num_Strip(CurrGCommand)[0]
        if CurrGCommand.find(";TYPE:Support interface") != -1:
            Copy_Flag=True
            Start_Index=i
            Last_XY_Command_FE_Flag=False
            # print(";LSTXY:"+last_xy_command_in_other_features)
            # print("start_index:",Start_Index)
        if Copy_Flag==True and CurrGCommand.find(";LAYER_CHANGE") != -1:
            #提前结算
            End_Index=i-1
            InterFace.extend(content[Start_Index:End_Index])
            Start_Index=i
            Act_Flag=True
            # Last_XY_Command_FE_Flag=False
        if CurrGCommand.find(";TYPE:")!=-1 and CurrGCommand.find(";TYPE:Support interface") == -1 and Copy_Flag:#这是另外一种挤出
            Copy_Flag=False
            End_Index=i
            InterFace.extend(content[Start_Index:End_Index])
            Act_Flag=True
            
        if CurrGCommand.find(";LAYER_CHANGE") != -1 and Act_Flag:
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
                print(Process_GCode_Offset(last_xy_command_in_other_features, 0.2, 0, 0.5,'normal').strip("\n"), file=TempExporter)#Inposition
                print("G1 Z" + str(round(Current_Layer_Height, 3)), file=TempExporter)
                print(";Ironing Started", file=TempExporter)
                print("G1 F"+str(para.Ironing_Speed),file=TempExporter)
                for i in range(len(InterFaceIroning)):
                    if InterFaceIroning[i].find("G1 ") != -1 and InterFaceIroning[i].find("G1 E") == -1 and InterFaceIroning[i].find("G1 F") == -1:
                        InterFaceIroning[i]=Process_GCode_Offset(InterFaceIroning[i], 0.2, 0, para.Z_Offset,'ironing')
                        InterFaceIroning[i].strip("\n")
                        print(InterFaceIroning[i].strip("\n"), file=TempExporter)
                print(";Ironing Finished", file=TempExporter)
            # print("G92 E0",file=TempExporter)
            print(";Mounting Toolhead", file=TempExporter)
            print(para.Custom_Mount_Gcode.strip("\n"), file=TempExporter)
            print(";Toolhead Mounted", file=TempExporter)
            print(";Rising Nozzle", file=TempExporter)
            try:
                print("G1 Z" + str(round(Current_Layer_Height+para.Z_Offset+3, 3)), file=TempExporter)#Avoid collision
            except:
                pass
            print(";Glueing Started", file=TempExporter)
            print(";Inposition", file=TempExporter)
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

            print(";Wiping Nozzle", file=TempExporter)
            print(para.Wiping_Gcode.strip("\n"), file=TempExporter)
            print(";Nozzle Wiped", file=TempExporter)
            print(";Move to the next print start position", file=TempExporter)
            print(Physical_Glueing_Point,file=TempExporter)
            print(";Lowering Nozzle", file=TempExporter)
            print("G1 Z" + str(round(Last_Layer_Height, 3)), file=TempExporter)
            # Insert InterfaceGlueing into Layer_Height_Index
            for i in range(len(InterFacePreGlueing)):
                if InterFacePreGlueing[i].find("G1 ") != -1 and InterFacePreGlueing[i].find("G1 E") == -1 and InterFacePreGlueing[i].find("G1 F") == -1:
                    InterFacePreGlueing[i]=Process_GCode_Offset(InterFacePreGlueing[i], para.X_Offset, para.Y_Offset, para.Z_Offset+Last_Layer_Height-Current_Layer_Height,'normal')
                    
            Layer_Height_Index[Current_Layer_Height] = ['','','','']
            Layer_Height_Index[Current_Layer_Height][0]= InterFacePreGlueing.copy()
            Layer_Height_Index[Current_Layer_Height][1]= Last_Layer_Height
            Layer_Height_Index[Current_Layer_Height][2]= Process_GCode_Offset(last_xy_command_in_other_features, para.X_Offset, para.Y_Offset, para.Z_Offset+3,'normal').strip("\n")
            Layer_Height_Index[Current_Layer_Height][3]=Process_GCode_Offset(last_xy_command_in_other_features,0, 0, para.Z_Offset+3,'normal').strip("\n")
            InterFaceGlueing.clear()
            InterFaceIroning.clear()
            InterFacePreGlueing.clear()
            InterFace.clear()
        print(CurrGCommand, file=TempExporter)
        pass
    TempExporter.close()
    #输出的预涂胶代码
    Trigger_Flag=False
    with open(Output_Filename+'.te', 'r', encoding='utf-8') as file:
        content = file.readlines()
    GcodeExporter = open(Output_Filename, "w", encoding="utf-8")
    for i in range(len(content)):
        CurrGCommand = content[i].strip("\n")
        if CurrGCommand.find(";Z:") != -1:
            Current_Layer_Height = Num_Strip(CurrGCommand)[0]
            if Current_Layer_Height in Layer_Height_Index:
                Trigger_Flag=True
        if Trigger_Flag==True and CurrGCommand.find(";TYPE:Support interface") != -1:
            Trigger_Flag=False
            print(";Mounting Toolhead", file=GcodeExporter)
            print(para.Custom_Mount_Gcode.strip("\n"), file=GcodeExporter)
            print(";Toolhead Mounted", file=GcodeExporter)
            print(";Rising Nozzle", file=GcodeExporter)
            print("G1 Z" + str(round(Layer_Height_Index[Current_Layer_Height][1]+para.Z_Offset+3, 3)), file=GcodeExporter)#Avoid collision
            print(";Inposition", file=GcodeExporter)
            print(Layer_Height_Index[Current_Layer_Height][2], file=GcodeExporter)
            print(";Adjusting Nozzle", file=GcodeExporter)
            print("G1 Z" + str(round(Layer_Height_Index[Current_Layer_Height][1]+para.Z_Offset, 3)), file=GcodeExporter)
            print(";Preglueing Started", file=GcodeExporter)
            print("G1 F" + str(para.Max_Speed), file=GcodeExporter)
            for j in range(len(Layer_Height_Index[Current_Layer_Height][0])):
                if Layer_Height_Index[Current_Layer_Height][0][j].find("G1 ") != -1 and Layer_Height_Index[Current_Layer_Height][0][j].find("G1 E") == -1 and Layer_Height_Index[Current_Layer_Height][0][j].find("G1 F") == -1:
                    # Layer_Height_Index[Current_Layer_Height][0][j] = Process_GCode_Offset(Layer_Height_Index[Current_Layer_Height][0][j], para.X_Offset, para.Y_Offset, para.Z_Offset,'normal')
                    print(Layer_Height_Index[Current_Layer_Height][0][j].strip("\n"), file=GcodeExporter)
            print(";Preglueing Finished", file=GcodeExporter)
            print(";Unmounting Toolhead", file=GcodeExporter)
            print(para.Custom_Unmount_Gcode.strip("\n"), file=GcodeExporter)
            print(";Toolhead Unmounted", file=GcodeExporter)

            if para.Have_Wiping_Components.get()!=True and First_layer_Flag==True:
                print(";Tower Base Layer", file=GcodeExporter)
                print(para.Tower_Base_Layer_Gcode.strip("\n"), file=GcodeExporter)
                print(";Tower Base Layer Finished", file=GcodeExporter)
                First_layer_Flag=False
            else:
                print(";Wiping Nozzle", file=GcodeExporter)
                print(para.Wiping_Gcode.strip("\n"), file=GcodeExporter)
                print(";Nozzle Wiped", file=GcodeExporter)
            print(";Move to the next print start position", file=GcodeExporter)
            print(Layer_Height_Index[Current_Layer_Height][3], file=GcodeExporter)
            print(";Lowering Nozzle", file=GcodeExporter)   
            print("G1 Z" + str(round(Current_Layer_Height, 3)), file=GcodeExporter)
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

time.sleep(2)
window.destroy()
window.mainloop()
exit(0)