# coding=utf-8
from CTkMessagebox import CTkMessagebox
import tkinter as tk  # 导入GUI界面函数库
import tkinter.font as tkFont
from tkinter import ttk, scrolledtext
import tkinter.messagebox
import re, os, ctypes, sys
from PIL import Image, ImageTk
import requests
import webbrowser
import chardet
import base64
# from in_png import img as png1
from calibe import Calibe as Calibe_Sing
from calibe import ZOffset as ZOffset_Sing
from tower import Temp_Wiping_Gcode, Temp_Tower_Base_Layer_Gcode
from sys import exit
import toml,argparse
import customtkinter as ctk
from datetime import datetime
from CTkScrollableDropdown import *
# from urllib.parse import urljoin
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

# ctypes.windll.shcore.SetProcessDpiAwareness(1)
# ScaleFactor = ctypes.windll.shcore.GetScaleFactorForDevice(0)/100

def CenterWindowToDisplay(Screen: ctk, width: int, height: int, scale_factor: float = 1.0):
    """Centers the window to the main display/monitor"""
    screen_width = Screen.winfo_screenwidth()
    screen_height = Screen.winfo_screenheight()
    x = int(((screen_width/2) - (width/2)) * scale_factor)
    y = int(((screen_height/2) - (height/1.5)) * scale_factor)
    return f"{width}x{height}+{x}+{y}"

local_version = "Wisteria 2.1"
# local_version = "Cachet"  # 本地版本号

#更新
def check_for_updates():
    global local_version
    url = "https://gitee.com/Jhmodel/MKPSupport/raw/main/UPDATE.md"  
    # url="locale"
    try:
        response = requests.get(url, stream=True, verify=False)
        if response.status_code == 200:
            content = response.text  # 将文件内容加载到内存
            if content.find(local_version) == -1:
                show_update_window(content)
        else:
            print(f"请求失败，状态码：{response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"请求失败，原因：{e}")

def show_update_window(content):
    # 创建主窗口
    update_window= ctk.CTk()  # 使用customtkinter创建窗口
    # update_window = tk.Tk()
    update_window.title("更新提示")
    update_window.geometry("400x300")
    update_window.geometry(CenterWindowToDisplay(update_window, 400, 300, update_window._get_window_scaling()))  # 居中显示窗口
    update_window.resizable(width=False, height=False)
    # 添加标签
    label = ctk.CTkLabel(update_window, text="检测到新版本:", anchor="w",font=("SimHei",15))  # 使用customtkinter的标签
    # label = tk.Label(update_window, text="检测到新版本:", anchor="w")
    label.pack(pady=10)
    # 添加文本框
    text_box = ctk.CTkTextbox(update_window, wrap="word", height=200, width=350)  # 使用customtkinter的文本框
    # text_box = tk.Text(update_window, wrap="word", height=10, width=50)
    text_box.insert("1.0", content)  # 插入更新内容
    # text_box.config(state="disabled")  # 设置为只读
    text_box.pack(padx=10,pady=10)
    text_box.configure(font=("SimHei", 12))  # 设置字体为SimHei，大小为12

    # 添加按钮
    def on_update():
        webbrowser.open("https://gitee.com/Jhmodel/MKPSupport/releases/")
        # update_window.quit()  # 关闭窗口
        update_window.destroy()
        os._exit(0)
    ctk.set_default_color_theme("green")
    button_frame = ctk.CTkFrame(update_window)
    button_frame.pack()
    update_button = ctk.CTkButton(button_frame, text="前往更新", command=on_update,font=("SimHei",15))  # 使用customtkinter的按钮
    update_button.pack()
    #把这个关闭对话框与程序结束exit(0)绑定：
    def on_close():
        try:
            update_window.destroy()
            os._exit(0)  # 直接退出程序，不做任何处理
        except:
            os._exit(0)
    update_window.protocol("WM_DELETE_WINDOW", on_close)  # 绑定关闭事件
    update_window.mainloop()  # 运行主循环



window = ctk.CTk()
window.title('MKPSupport Version '+local_version)
window.geometry("300x160")
window.resizable(width=False, height=False)

mkpimage_path = "in.png"
# 判断是否为exe
if getattr(sys, 'frozen', False):
    mkpexecutable_dir = os.path.dirname(sys.executable)
    mkpinternal_dir = os.path.join(mkpexecutable_dir, "_internal")
    mkpimage_path = os.path.join(mkpinternal_dir, "in.png")
elif __file__:
    mkpexecutable_dir = os.path.dirname(__file__)
    mkpimage_path = os.path.join(mkpexecutable_dir, "in.png")

try:
    image0 = Image.open(mkpimage_path)
except:
    image0 = Image.open("in.png")
image0 = image0.resize((300, 160),Image.Resampling.LANCZOS)
ctk_image = ctk.CTkImage(light_image=image0, size=(300, 160))
label = ctk.CTkLabel(window, image=ctk_image, text="")
label.pack(fill="both", expand=True)  # 满幅显示图片
def on_closing():
    os._exit(0)  # 直接退出程序，不做任何处理
window.protocol("WM_DELETE_WINDOW", on_closing)  # 绑定关闭事件
window.update() 

class para:
    # parameters
    Enable_ironing=False#这是识别是否开启熨烫功能的
    Have_Wiping_Components=None#这是识别是否用内置擦嘴塔的
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
    Update_date = None
    Temp_ZOffset_Calibr=0
    Temp_XOffset_Calibr=0
    Temp_YOffset_Calibr=0
    Nozzle_Switch_Tempature=0#喷嘴切换温度
    L803_Leak_Pervent_Flag=False#L803漏料预防功能开关
    Minor_Nozzle_Diameter_Flag=False#小喷嘴直径开关
    Fan_Speed=0#风扇速度
    New_Preset_Name=""
    Drag_x=0
    Drag_y=0
User_Input = []#存用户输入的参数
Output_Filename=""#输出文件名，最终会被更名

def Invert_Flag(Flag):
    newvalue=not Flag.get()
    Flag.set(newvalue)
    print(Flag.get())

def create_draggable_square_app():
    """创建并返回一个包含可拖动方块的CTk窗口（左下角原点坐标系）"""
    # 初始化窗口
    cltpop = ctk.CTk()
    cltpop.geometry("320x350")  # 增加高度以容纳按钮
    # cltpop.geometry(CenterWindowToDisplay(cltpop, 320, 340, cltpop._get_window_scaling()))  # 居中显示窗口
    cltpop.title("擦料塔位置调整")
    cltpop.focus_force()  # 窗口创建后立即抢占焦点
    # cltpop.attributes('-topmost', True)
    # 配置方块属性
    square_size = 30
    square_fill = "#1f6aa5"
    square_outline = "#144870"
    drag_data = {"x": 0, "y": 0, "item": None}
    # 创建主画布
    def setup_canvas():
        canvas_frame = ctk.CTkFrame(cltpop)
        canvas_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        canvas = tk.Canvas(
            canvas_frame, 
            bg="#f0f0f0",
            highlightthickness=0,
            width=400,
            height=350
        )
        canvas.pack(fill="both", expand=True)
        return canvas
    
    canvas = setup_canvas()
    # 1. 创建一个横向排列的 Frame
    button_frame = ctk.CTkFrame(cltpop)  # 默认方向是横向
    button_frame.pack(pady=10, padx=10, fill="x")
    button_frame.configure(fg_color="transparent")  # 设置背景透明
    # 2. 将坐标标签放在左侧（左对齐）
    coord_label = ctk.CTkLabel(
        button_frame, 
        text="坐标: (0, 0)", 
        font=("Arial", 14)
    )
    coord_label.pack(side="left", padx=5)  # 左对齐，加间距
    def on_confirm():
        """确定按钮回调函数"""
        if square_id:
            x1, _, x2, y2 = canvas.coords(square_id)
            height = canvas.winfo_reqheight()
            # 计算实际坐标（左下角为原点）
            coord_x = x1
            coord_y = height - y2
            # print(f"确定坐标: ({coord_x}, {coord_y})")
            para.Drag_x = coord_x
            para.Drag_y = coord_y
            # print(f"拖动坐标: ({para.Drag_x}, {para.Drag_y})")
            # cltpop.return_value = (coord_x, coord_y)  # 存储返回值
        # cltpop.quit()  # 销毁窗口
        # cltpop.destroy()  # 销毁窗口并返回坐标
        # safe_destroy(cltpop)  # 安全销毁窗口
        cltpop.quit()  # 退出主循环，继续执行后续代码
        cltpop.after(100, cltpop.destroy)
        # return
    # 3. 将确定按钮放在右侧（右对齐）
    confirm_btn = ctk.CTkButton(
        button_frame,  # 注意父容器改为 button_frame
        text="确定", 
        command=on_confirm,
        font=("SimHei", 14),
        height=30
    )
    confirm_btn.pack(side="right", padx=5)  # 右对齐，加间距

    def safe_destroy(window):
        # 取消所有挂起的after事件
        for after_id in window.tk.eval('after info').split():
            window.after_cancel(after_id)
        window.destroy()
    # 创建确定按钮
   

    
    # 绘图函数
    def draw_grid_and_axes():
        """绘制栅格和坐标轴（左下角原点）"""
        width = canvas.winfo_reqwidth()
        height = canvas.winfo_reqheight()
        
        # 原点设在左下角 (0, height)
        origin_x, origin_y = 0, height
        
        # 清除旧内容
        canvas.delete("all")
        
        # 绘制栅格线
        grid_color = "#d9d9d9"
        for x in range(0, width, 20):
            canvas.create_line(x, origin_y, x, 0, fill=grid_color, tags="grid")
        for y in range(origin_y, 0, -20):
            canvas.create_line(0, y, width, y, fill=grid_color, tags="grid")
        
        # 绘制坐标轴
        axis_color = "#333333"
        # X轴 (从左下角向右延伸)
        canvas.create_line(0, origin_y, width, origin_y, 
                        fill=axis_color, width=2, tags="axis")
        # Y轴 (从左下角向上延伸)
        canvas.create_line(0, origin_y, 0, 0, 
                        fill=axis_color, width=2, tags="axis")
        
        # 绘制原点标记
        origin_size = 6
        canvas.create_oval(
            -origin_size, origin_y - origin_size,
            origin_size, origin_y + origin_size,
            fill="red", outline="red", tags="origin"
        )
        
        # 添加坐标轴标签
        canvas.create_text(width - 10, origin_y - 10, text="X", 
                        fill=axis_color, font=("Arial", 10))
        canvas.create_text(10, 10, text="Y", 
                        fill=axis_color, font=("Arial", 10))
    
    def create_square():
        """创建初始方块并返回ID（左下角坐标(6,6)）"""
        height = canvas.winfo_reqheight()
        
        # 方块左下角坐标为(6,6)
        x1 = 6
        y1 = height - 6 - square_size  # 转换为画布坐标系
        x2 = x1 + square_size
        y2 = y1 + square_size
        
        square_id = canvas.create_rectangle(
            x1, y1, x2, y2,
            fill=square_fill,
            outline=square_outline,
            width=2,
            tags="square"
        )
        update_coord_label(x1, y2)
        return square_id
    
    def update_coord_label(x, y):
        """更新坐标标签显示（左下角原点坐标系）"""
        height = canvas.winfo_reqheight()
        # 转换为左下角原点坐标系
        rel_x = x
        rel_y = height - y  # 因为画布的Y轴向下为正
        cx= rel_x
        cy= rel_y
        coord_label.configure(text=f"坐标: ({rel_x:.0f}, {rel_y:.0f})")
    
    # 拖动事件处理
    def on_drag_start(event):
        drag_data["item"] = canvas.find_closest(event.x, event.y)[0]
        drag_data["x"] = event.x
        drag_data["y"] = event.y
    
    def on_drag_motion(event):
        dx = event.x - drag_data["x"]
        dy = event.y - drag_data["y"]
        
        canvas.move(drag_data["item"], dx, dy)
        drag_data["x"] = event.x
        drag_data["y"] = event.y
        
        x1, y1, x2, y2 = canvas.coords(drag_data["item"])
        update_coord_label(x1, y2)
    
    def on_drag_stop(event):
        drag_data["item"] = None
    
    # 初始化绘图和事件绑定
    draw_grid_and_axes()
    square_id = create_square()
    
    canvas.tag_bind("square", "<ButtonPress-1>", on_drag_start)
    canvas.tag_bind("square", "<B1-Motion>", on_drag_motion)
    canvas.tag_bind("square", "<ButtonRelease-1>", on_drag_stop)

    # 存储返回值
    # cltpop.return_value = None
    # cltpop.update()  # 强制刷新窗口
    cltpop.update_idletasks()  # 强制完成布局计算
    cltpop.after(100, lambda: cltpop.focus_force())  # 延迟抢焦点
    cltpop.mainloop()  # 启动主循环
    
    # return cltpop.return_value  # 返回坐标或None

def get_preset_values(Mode):
    popup = ctk.CTkToplevel(window)
    popup.geometry("520x520")
    popup.geometry(CenterWindowToDisplay(popup, 520, 520, popup._get_window_scaling()))
    popup.title("配置向导")
    # 使用CTk的网格布局管理器
    popup.grid_columnconfigure(1, weight=1)
    
    labels = [
        "涂胶速度限制[MM/S]", "X坐标补偿值[MM]", "Y坐标补偿值[MM]", 
        "喷嘴笔尖高度差[MM]", "自定义工具头获取 G-code", "自定义工具头收起 G-code",
        "使用内置擦嘴塔", "擦料塔的起始点", "擦料塔打印速度[MM/S]"
    ]
    entries = []
    
    # para.Enable_ironing = ctk.BooleanVar(value=False)
    # para.Have_Wiping_Components = ctk.BooleanVar(value=True)
    
    def create_right_click_menu(widget):
        """为ScrolledText添加右键菜单"""
        menu = tk.Menu(widget, tearoff=0)
        menu.add_command(label="剪切", font=("SimHei",15),command=lambda: widget.event_generate("<<Cut>>"))
        menu.add_command(label="复制",  font=("SimHei",15),command=lambda: widget.event_generate("<<Copy>>"))
        menu.add_command(label="粘贴",  font=("SimHei",15),command=lambda: widget.event_generate("<<Paste>>"))
        menu.add_command(label="删除",  font=("SimHei",15),command=lambda: widget.delete("sel.first", "sel.last"))
        menu.add_separator()
        menu.add_command(label="全选", font=("SimHei",15), command=lambda: widget.event_generate("<<SelectAll>>"))
        
        def show_menu(event):
            menu.post(event.x_root, event.y_root)
        widget.bind("<Button-3>", show_menu)

    # 创建输入控件
    for i, label in enumerate(labels):
        ctk.CTkLabel(popup, text=label + ":", font=("SimHei",12)).grid(row=i, column=0, padx=10, pady=5, sticky="w")
        
        if label in ["自定义工具头获取 G-code", "自定义工具头收起 G-code"]:
            text_box = ctk.CTkTextbox(popup, width=40, height=79, fg_color=("white","#343638"),border_width=2,corner_radius=9, font=("SimHei",12))
            text_box.grid(row=i, column=1, padx=10, pady=5, sticky="ew")
            create_right_click_menu(text_box)
            entries.append(text_box)
            
        elif label == "使用内置擦嘴塔":
            print("创建窗口时Have_Wiping_Components:", para.Have_Wiping_Components.get())
            checkbox = ctk.CTkCheckBox(
                popup, text="", variable=para.Have_Wiping_Components,
                onvalue=True,  # 选中时的值
                offvalue=False,  # 未选中时的值
             command=lambda: print(para.Have_Wiping_Components.get())
            )
            checkbox.grid(row=i, column=1, padx=10, pady=5, sticky="w")
            entries.append(checkbox)
            
        elif label == "擦料塔的起始点":
            frame = ctk.CTkFrame(popup, fg_color="transparent")
            frame.grid(row=i, column=1, padx=10, pady=5, sticky="w")
            # 添加调整位置按钮
            def adjust_position():
                """调用位置调整窗口并更新输入框"""
                create_draggable_square_app()  # 调用可视化调整函数
                print("拖动坐标:", para.Drag_x, para.Drag_y)
                if para.Drag_x != 0 and para.Drag_y != 0:
                    # print(f"拖动坐标: ({para.Drag_x}, {para.Drag_y})")
                    x= para.Drag_x
                    y= para.Drag_y
                    entry_x.delete(0, "end")
                    entry_x.insert(0, str(round(x)))
                    entry_y.delete(0, "end")
                    entry_y.insert(0, str(round(y)))
                    para.Drag_x = 0  # 重置拖动坐标
                    para.Drag_y = 0
            
            adjust_btn = ctk.CTkButton(
                frame,
                text="调整擦料塔位置",
                command=adjust_position,
                width=80,
                font=("SimHei", 12)
            )
            adjust_btn.pack(side="left", padx=(0, 5))
            
            # X/Y输入框
            ctk.CTkLabel(frame, text="X:").pack(side="left")
            entry_x = ctk.CTkEntry(frame, width=60)
            entry_x.pack(side="left", padx=2)
            entry_x.insert(0, "5")
            
            ctk.CTkLabel(frame, text="Y:").pack(side="left", padx=(5,0))
            entry_y = ctk.CTkEntry(frame, width=60)
            entry_y.pack(side="left", padx=2)
            entry_y.insert(0, "5")
            
            entries.append((entry_x, entry_y))

            
        elif label == "擦料塔打印速度[MM/S]":
            entry_speed = ctk.CTkEntry(popup)
            entry_speed.grid(row=i, column=1, padx=10, pady=5, sticky="ew")
            entry_speed.insert(0, "50")
            entries.append(entry_speed)
            
        else:
            entry = ctk.CTkEntry(popup)
            entry.grid(row=i, column=1, padx=10, pady=5, sticky="ew")
            entries.append(entry)
    
    # 如果是修改模式，填充数据
    if Mode == "Modify":
        # 修改模式，读取配置文件的数据
        for i, label in enumerate(labels):
            if label == "涂胶速度限制[MM/S]":
                entries[i].delete(0, "end")  # CTkEntry清空方式
                entries[i].insert(0, str(para.Max_Speed))
                
            if label == "X坐标补偿值[MM]":
                entries[i].delete(0, "end")
                entries[i].insert(0, str(para.X_Offset))
                
            if label == "Y坐标补偿值[MM]":
                entries[i].delete(0, "end")
                entries[i].insert(0, str(para.Y_Offset))
                
            if label == "喷嘴笔尖高度差[MM]":
                entries[i].delete(0, "end")
                entries[i].insert(0, str(para.Z_Offset))
                
            if label == "自定义工具头获取 G-code":
                entries[i].delete("1.0", "end")  # CTkTextbox清空方式
                entries[i].insert("1.0", para.Custom_Mount_Gcode)
                
            if label == "自定义工具头收起 G-code":
                entries[i].delete("1.0", "end")
                entries[i].insert("1.0", para.Custom_Unmount_Gcode)
                
        # 处理擦料塔坐标和速度
        if "擦料塔的起始点" in labels:
            entry_x.delete(0, "end")
            entry_y.delete(0, "end")
            entry_x.insert(0, str(para.Wiper_x))
            entry_y.insert(0, str(para.Wiper_y))
            
        if "擦料塔打印速度[MM/S]" in labels:
            entry_speed.delete(0, "end")
            entry_speed.insert(0, str(para.Typical_Layer_Speed))

        # 处理复选框状态
        if para.Have_Wiping_Components.get() == False:
            checkbox.deselect()
    button_save_frame = ctk.CTkFrame(popup)
    button_save_frame.grid(row=len(labels), column=0, columnspan=2, pady=10, sticky="ew")
    button_save_frame.configure(fg_color="transparent")  # 设置背景透明
    # 另存按钮
    save_as_btn = ctk.CTkButton(
       button_save_frame, text="另存为", command=lambda: on_save_as(),
        corner_radius=10,font=("SimHei", 15)
    )

    #取消按钮
    cancel_btn = ctk.CTkButton(
        button_save_frame, text="取消", command=popup.destroy,
        corner_radius=10,font=("SimHei", 15)
    )

    # 提交按钮
    submit_btn = ctk.CTkButton(
        button_save_frame, text="确定", command=lambda: on_submit(),
        corner_radius=10,font=("SimHei", 15)
    )
    cancel_btn.pack(side="right", padx=(0, 10))
    submit_btn.pack(side="right", padx=(0, 5))
    save_as_btn.pack(side="right", padx=(0, 5))

    def on_save_as():
        dialog = ctk.CTkInputDialog(title="新建预设", text="请输入新预设的名称:",font=("SimHei",15))
        para.New_Preset_Name = dialog.get_input()
        popup.destroy()  # 关闭弹窗

    def on_submit():
        global User_Input
        User_Input = []  # 确保清空或初始化列表
        for entry in entries:
            if isinstance(entry, ctk.CTkEntry):
                User_Input.append(entry.get())
            elif isinstance(entry, ctk.CTkTextbox):
                try:
                    # CTkTextbox 使用 "1.0" 到 "end-1c" 获取内容（避免末尾多余换行）
                    text_content = entry.get("1.0", "end-1c")
                    User_Input.append(text_content)
                except Exception as e:
                    print(f"CTkTextbox widget error: {str(e)}")
                    User_Input.append("")  # 出现错误时追加空字符串
            elif isinstance(entry, tuple):
                # 如果是擦嘴塔的起始点，获取X和Y坐标
                x_value = entry[0].get()
                y_value = entry[1].get()
                User_Input.append(x_value)
                User_Input.append(y_value)
        popup.destroy()  # 关闭弹窗

    
    def on_closing():
        ct=CTkMessagebox(title="退出", message="您真的要退出吗?", 
                         icon="question", option_1="取消", option_2="退出",fade_in_duration=0.1,bg_color=("white","black"),fg_color=("#e1e6e9","#343638"),border_width=1,font=("SimHei",15),border_color=("#d1d1d1","#3a3a3a"))
        if ct.get() == "退出":
            popup.destroy()
            # window.destroy()
    
    popup.protocol("WM_DELETE_WINDOW", on_closing)
    
    # 等待窗口关闭
    popup.grab_set()
    window.wait_window(popup)
    return User_Input
    
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
    if User_Input == []:
        return  
    print(User_Input)
    para.Max_Speed = round(float(User_Input[0]), 3)
    para.X_Offset = round(float(User_Input[1]), 3)
    para.Y_Offset = round(float(User_Input[2]), 3)
    para.Z_Offset = round(float(User_Input[3]), 3)
    para.Custom_Mount_Gcode = User_Input[4]
    para.Custom_Unmount_Gcode = User_Input[5]
    # para.Ironing_Speed = round(float(User_Input[6]), 3)
    # para.Iron_Extrude_Ratio = round(float(User_Input[7]), 3)
    # para.Have_Wiping_Components.set(User_Input[6])
    # 
    para.Wiper_x = round(float(User_Input[6]), 3)
    para.Wiper_y = round(float(User_Input[7]), 3)
    para.Typical_Layer_Speed = round(float(User_Input[8]), 3)
#这个函数用来从传入的filepath读取配置到para类中的变量
def read_toml_config(file_path):
    para.Have_Wiping_Components = tk.BooleanVar(value=False)
    para.Wiping_Gcode=Temp_Wiping_Gcode.strip().splitlines()
    para.Tower_Base_Layer_Gcode=Temp_Tower_Base_Layer_Gcode.strip().splitlines()
    with open(file_path, 'r', encoding='utf-8') as f:
        config = toml.load(f)
    #在f中查找更新时间注释：
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith("# release_time:"):
                para.Update_date = line
                break
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
        wiping_config = config['wiping']
        para.Have_Wiping_Components.set(wiping_config['have_wiping_components'])
        # if para.Have_Wiping_Components.get()==True:
        para.Wiper_x = wiping_config['wiper_x']
        para.Wiper_y = wiping_config['wiper_y']
        para.Typical_Layer_Speed = wiping_config['wipetower_speed']
#这个函数用来创建一个输入框，目前只是用来输入预设名称
def create_input_dialog(title, prompt):
    dialog = ctk.CTkInputDialog(title="新建预设", text="请输入新预设的名称:",font=("SimHei",15))
    new_preset_name = dialog.get_input()
    if new_preset_name:
        para.Preset_Name = new_preset_name
        mkpsupport_path = os.path.join(create_mkpsupport_dir(), f"{new_preset_name}.toml")
        get_preset_values("Normal")
        write_toml_config(mkpsupport_path)
        # refresh_toml_list()
    # def on_submit():
    #     user_input = entry.get()
    #     if not user_input:
    #         tk.messagebox.showwarning("警告", "输入不能为空！")
    #     else:
    #         para.Preset_Name = user_input
    #         asq.quit()
    # asq = ctk.CTkToplevel(window)  # 使用customtkinter创建顶级窗口
    # asq.geometry("150x90")
    # asq.geometry(CenterWindowToDisplay(asq, 150, 90, asq._get_window_scaling()))
    # asq.title(title)
    # # asq.resizable(0, 0)  # 固定窗口大小
    # label = tk.Label(asq, text=prompt)
    # label.pack(padx=10, pady=5)
    # entry = tk.Entry(asq)
    # entry.pack(padx=10, pady=5)
    # submit_button = ttk.Button(asq, text="确定", command=on_submit, style='Rounded.TButton')
    # submit_button.pack(side='bottom',pady=10)
    # asq.protocol("WM_DELETE_WINDOW",asq.quit)
    # asq.mainloop()
#这个函数用来写入配置到文件名为file_path的文件中    
def write_toml_config(file_path):
    read_dialog_input()
    save_as_flag = False
    if para.New_Preset_Name != "":
        save_as_flag = True
        folder_path = create_mkpsupport_dir()
        New_path=os.path.join(folder_path, para.New_Preset_Name + ".toml")
        para.New_Preset_Name = ""
        file_path = New_path
    with open(file_path, 'w', encoding='utf-8') as f:
        if para.Have_Wiping_Components.get()==False:
            Use_wiper_str="false"
        else:
            Use_wiper_str="true"
        if isinstance(para.Custom_Mount_Gcode, list):
            para.Custom_Mount_Gcode = "\n".join(para.Custom_Mount_Gcode)
        if isinstance(para.Custom_Unmount_Gcode, list):
            para.Custom_Unmount_Gcode = "\n".join(para.Custom_Unmount_Gcode)
        try:
            print(para.Update_date.strip("\n"), file=f)
            para.Update_date = None
        except:
            print("# release_time: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"), file=f)
        print("#胶笔配置", file=f)
        print("[toolhead]", file=f)
        print("speed_limit = " + str(para.Max_Speed) + "  #涂胶速度限制 (mm/s)", file=f)
        print("offset = { x = " + str(para.X_Offset) + ", y = " + str(para.Y_Offset) + ", z = " + str(para.Z_Offset) + "}# 笔尖偏移", file=f)
        print("# 自定义工具头获取 G-code", file=f)
        print("custom_mount_gcode = \"\"\"" + "\n" + para.Custom_Mount_Gcode.strip("\n"), file=f)
        print("\"\"\"", file=f)
        print("# 自定义工具头收起 G-code", file=f)
        print("custom_unmount_gcode = \"\"\"" + "\n" + para.Custom_Unmount_Gcode.strip("\n"), file=f)
        print("\"\"\"", file=f)
        print("#擦嘴配置", file=f)
        print("[wiping]", file=f)
        print("have_wiping_components = "+Use_wiper_str+"#使用内置擦嘴塔Enable wiping components",file=f)
        print("wiper_x = "+str(para.Wiper_x),file=f)
        print("wiper_y = "+str(para.Wiper_y),file=f)
        print("wipetower_speed = " + str(para.Typical_Layer_Speed) + " # 擦嘴塔打印速度Wipe tower print speed", file=f)
    if save_as_flag==True:
        refresh_preset_frame_list()
#这个函数用来创建一个弹窗，让用户点击按钮复制命令到剪贴板
def copy_user_command():
    root1 = ctk.CTk()
    root1.title('文件路径')
    root1.geometry("600x159")
    
    def copy_curr_exe_path():
        root1.clipboard_clear()
        command = f'"{os.path.abspath(sys.executable)}" --Toml "{para.Preset_Name}" --Gcode'
        root1.clipboard_append(command)
        cs=CTkMessagebox(title='完成', message='路径已复制到剪贴板。',option_1="确定", icon='check',fade_in_duration=0.1,bg_color=("white","black"),fg_color=("#e1e6e9","#343638"),border_width=1,font=("SimHei",15),border_color=("#d1d1d1","#3a3a3a"))
        # tk.messagebox.showinfo(title='完成', message='路径已复制。软件将自动关闭')
        if cs.get() == "确定":
            # print("路径已复制到剪贴板。")
            cs.destroy()
            root1.destroy()
            exit(0)
    # 提示信息
    message = '点击“复制”拷贝程序所在的路径，并粘贴入工艺->其他->后处理脚本框中。'
    label = ctk.CTkLabel(root1, text=message, wraplength=550,justify='center', font=("SimHei", 15))
    label.pack(pady=10)
    
    # 创建带滚动条的文本框框架
    frame = ctk.CTkFrame(root1)
    frame.pack(fill='x', padx=10, pady=5)
    
    # 文本框
    path_text = ctk.CTkTextbox(frame, height=30, wrap='none')
    path_text.pack(fill='x', padx=5, pady=5)
    
    # 插入默认文本
    command = f'"{os.path.abspath(sys.executable)}" --Toml "{para.Preset_Name}" --Gcode'
    path_text.insert('1.0', command)
    
    # 复制按钮
    copy_button = ctk.CTkButton(
        root1, 
        text='复制', 
        command=copy_curr_exe_path,
        corner_radius=20,  # 圆角效果
        fg_color="green",  
        hover_color="#3672b0",  # 悬停时深蓝色
        font=("SimHei", 15)  # 设置字体
    )
    copy_button.pack(pady=10)
    
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
def check_validity_interface_set(interface):
    Have_Extrude_Flag=False
    dot_count=0
    for i in interface:
        if i.find(" E") != -1 and i.find(" Z")==-1 and (i.find("X")!=-1 or i.find("Y")!=-1):
            E_index=i.find("E")
            TmpEChk=i[E_index:]
            if TmpEChk.find("-") == -1:
                dot_count+=1
            if dot_count>=1:
                Have_Extrude_Flag=True
                break
    return Have_Extrude_Flag
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
    folder_path = create_mkpsupport_dir()
    toml_files = [f for f in os.listdir(folder_path) if f.endswith('.toml')]
    Have_Toml_Flag = True
    Create_New_Config = 'no'
    if not toml_files:
        Have_Toml_Flag = False
    # 检查是新建还是修改
    if Have_Toml_Flag!=True:
        root = ctk.CTk()
        root.withdraw()  # 隐藏主窗口
        mg=CTkMessagebox(title="无可用预设", message='当前文件夹下无可用预设。创建新预设？',
                        icon="question", option_1="在线获取预设", option_2="确定",option_3="取消",fade_in_duration=0.1,bg_color=("white","black"),fg_color=("#e1e6e9","#343638"),border_width=1,font=("SimHei",15),border_color=("#d1d1d1","#3a3a3a"))
        Create_New_Config = mg.get()  # 获取用户选择
        if Create_New_Config == "确定":
            new_preset_name=""
            create_input_dialog("新建预设", "请输入新预设的名称:")
            new_preset_name = para.Preset_Name
            # get_preset_values("Normal")
            write_toml_config(os.path.join(folder_path, new_preset_name + ".toml"))
        elif Create_New_Config == "在线获取预设":
            def download_presets():
                # 预设文件列表
                preset_files = ["A1.toml", "A1M.toml", "X1.toml"]
                base_url = "https://gitee.com/Jhmodel/MKPSupport/raw/main/Presets/"
                downloaded_files = []
                
                # 创建对话框显示下载进度
                progress_dialog = ctk.CTkToplevel()
                progress_dialog.title("下载预设")
                progress_dialog.geometry("400x200")
                progress_dialog.resizable(False, False)
                
                progress_label = ctk.CTkLabel(
                    progress_dialog, 
                    text="正在下载预设文件...",
                    font=("SimHei", 14)
                )
                progress_label.pack(pady=20)
                
                progress_bar = ctk.CTkProgressBar(
                    progress_dialog,
                    width=400,  # 设置宽度为400像素
                    height=20,  # 也可以适当增加高度
                    corner_radius=10,  # 圆角效果
                    progress_color="#4CAF50",  # 进度条颜色
                    orientation="horizontal"  # 水平方向
                )
                progress_bar.pack(fill='x', padx=20, pady=10)
                progress_bar.set(0)
                
                status_label = ctk.CTkLabel(
                    progress_dialog,
                    text="",
                    font=("SimHei", 12)
                )
                status_label.pack(pady=10)
                
                # 确保目标目录存在
                if not os.path.exists(folder_path):
                    os.makedirs(folder_path)
                
                # 下载每个预设文件
                for i, filename in enumerate(preset_files):
                    try:
                        url = base_url+filename
                        response = requests.get(url, stream=True)
                        response.raise_for_status()
                        
                        filepath = os.path.join(folder_path, filename)
                        with open(filepath, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        
                        downloaded_files.append(filename)
                        status_label.configure(text=f"已下载: {filename}")
                        progress_bar.set((i + 1) / len(preset_files))
                        progress_dialog.update()
                    except Exception as e:
                        status_label.configure(text=f"下载{filename}失败: {str(e)}")
                        progress_dialog.update()
                
                progress_label.configure(text="下载完成!")
                progress_dialog.after(1000, progress_dialog.destroy)
                return downloaded_files
            
            def show_selection_dialog(files):
                selection_dialog = ctk.CTkToplevel()
                selection_dialog.title("选择机型")
                selection_dialog.geometry("400x300")
                selection_dialog.resizable(False, False)
                
                selected_presets = []
                
                def on_confirm():
                    nonlocal selected_presets
                    selected_presets = [file for file, var in zip(files, check_vars) if var.get()]
                    selection_dialog.destroy()

                # 添加标题
                title_label = ctk.CTkLabel(
                    selection_dialog,
                    text="请选择需要保留的机型预设:",
                    font=("SimHei", 14)
                )
                title_label.pack(pady=10)
                
                def get_preset_display_name(filename):
                    name_mapping = {
                        "A1.toml": "A1",
                        "A1M.toml": "A1M",
                        "X1.toml": "X1/P1"
                    }
                    return name_mapping.get(filename, filename.replace('.toml', ''))

                # 创建多选框
                check_vars = []
                for file in files:
                    var = ctk.BooleanVar(value=True)
                    check_vars.append(var)
                    
                    checkbox = ctk.CTkCheckBox(
                        selection_dialog,
                        text=get_preset_display_name(file),
                        variable=var,
                        font=("SimHei", 12)
                    )
                    checkbox.pack(anchor='w', padx=20, pady=5)
                
                # 添加按钮
                button_frame = ctk.CTkFrame(selection_dialog,fg_color="transparent",bg_color="transparent")  # 设置按钮框架背景色为透明
                button_frame.pack(side='bottom', fill='x', pady=10)  # 设置底部按钮框架背景色
                
                confirm_button = ctk.CTkButton(
                    button_frame,
                    text="确定",
                    command=on_confirm,
                    font=("SimHei", 12)
                )
                confirm_button.pack(side='right', padx=10)
                
                cancel_button = ctk.CTkButton(
                    button_frame,
                    text="取消",
                    command=selection_dialog.destroy,
                    font=("SimHei", 12),
                    fg_color="#d9534f",
                    hover_color="#c9302c"
                )
                cancel_button.pack(side='right')
                
                selection_dialog.wait_window()
                return selected_presets
            
            # 下载预设文件
            downloaded_files = download_presets()
            
            if downloaded_files:
                # 显示选择对话框
                selected_files = show_selection_dialog(downloaded_files)
                
                if selected_files:  # 用户点击了确定
                    # 删除未选中的文件
                    for file in downloaded_files:
                        if file not in selected_files:
                            try:
                                os.remove(os.path.join(folder_path, file))
                            except Exception as e:
                                print(f"删除{file}失败:", e)
                    
                    # 刷新列表
                    # refresh_toml_list()
                else:  # 用户点击了取消
                    # 删除所有下载的文件
                    for file in downloaded_files:
                        try:
                            os.remove(os.path.join(folder_path, file))
                        except Exception as e:
                            print(f"删除{file}失败:", e)
        else:
            os._exit(0)

    #创建主窗口
    global selection_dialog,local_version
    selection_dialog = ctk.CTkToplevel(window)
    selection_dialog.title(local_version)
    selection_dialog.geometry(CenterWindowToDisplay(selection_dialog, 550, 400, selection_dialog._get_window_scaling()))
    def on_closing():
        os._exit(0)  # 直接退出程序
    selection_dialog.protocol("WM_DELETE_WINDOW", on_closing)
    ctk.set_default_color_theme("green")

    def refresh_toml_list():
        def on_select(value):
            selected_toml.set(value)
        
        try:
            for widget in scroll_frame.winfo_children():
                if isinstance(widget, ctk.CTkRadioButton):
                    widget.destroy()
        except:
            # 清除现有控件
            for widget in selection_dialog.winfo_children():
                widget.destroy()


        # ------ 新增代码：添加选项卡容器 ------
        tabview = ctk.CTkTabview(selection_dialog,fg_color=("#f1f2f3", "#242424"),bg_color=("#f1f2f3", "#242424"))
        tabview.pack(fill="both", expand=True, padx=10, pady=10)
        bold_font = ctk.CTkFont(
            family="SimHei",  # 设置字体为黑体
            size=13,
            weight="bold"  # 设置加粗
        )
        tabview._segmented_button.configure(
            font=bold_font,  # 设置字体为黑体加粗
        )
        # 添加两个选项卡（第二个选项卡预留空位）
        tabview.add("预设管理")  # 原有功能放在这里
        tabview.add("下载管理")  # 留空，后续由你自行实现
        tabview.add("自动校准")  
        preset_frame = ctk.CTkFrame(tabview.tab("预设管理"),fg_color=("#f1f2f3", "#242424"),bg_color=("#f1f2f3", "#242424"))
        preset_frame.pack(fill="both", expand=True)

        # # 创建主体框架
        # preset_frame = ctk.CTkFrame(selection_dialog,fg_color=("#f1f2f3", "#242424"),bg_color=("#f1f2f3", "#242424"))#("#DB3E39", "#821D1A")
        # preset_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 创建滚动区域框架
        scroll_frame = ctk.CTkScrollableFrame(preset_frame,fg_color=("#f1f2f3", "#242424"),bg_color=("#f1f2f3", "#242424"))
        scroll_frame.pack(fill='both', expand=True)
        
        # 添加单选按钮
        toml_files = [f for f in os.listdir(folder_path) if f.endswith('.toml')]
        radio_buttons = []
        toml_file_paths = []
        for toml_file in toml_files:
            filePath = os.path.join(folder_path, toml_file)
            toml_file_paths.append(filePath)
            radio_button = ctk.CTkRadioButton(
                scroll_frame, 
                text=toml_file, 
                variable=selected_toml, 
                value=filePath,
                corner_radius=6,
                command=lambda v=filePath: on_select(v)
            )
            radio_button.pack(anchor='w', pady=5)
            radio_buttons.append(radio_button)
        
        # 设置默认选择
        if toml_file_paths:
            selected_toml.set(toml_file_paths[0])
            radio_buttons[0].select()
        global refresh_preset_frame_list
        def refresh_preset_frame_list():
            """刷新预设列表的最快实现（适用于少量项目）"""
            # 1. 清空现有单选按钮
            for widget in scroll_frame.winfo_children():
                widget.destroy()  # 直接销毁所有子部件

            # 2. 重新加载文件列表
            toml_files = [f for f in os.listdir(folder_path) if f.endswith('.toml')]
            
            # 3. 重建RadioButton（数量少时很快）
            for toml_file in toml_files:
                filePath = os.path.join(folder_path, toml_file)
                ctk.CTkRadioButton(
                    scroll_frame, 
                    text=toml_file, 
                    variable=selected_toml, 
                    value=filePath,
                    corner_radius=6,
                    command=lambda v=filePath: on_select(v)
                ).pack(anchor='w', pady=5)

            # 4. 默认选中第一个（如果存在）
            if toml_file_paths:
                try:
                    selected_toml.set(toml_file_paths[0])
                    radio_buttons[0].select()
                except:
                    pass

        # ===== 新增代码：黑色超链接（点击变浅灰） =====
        hyperlink_frame = ctk.CTkFrame(preset_frame, fg_color="transparent", bg_color="transparent")
        hyperlink_frame.pack(side='top', fill='x', pady=(0, 10), padx=10)

        # 项目主页超链接
        def on_project_click(event):
            import webbrowser
            webbrowser.open("https://gitee.com/Jhmodel/MKPSupport")  # 替换为实际链接
            # event.widget.configure(text_color="#a0a0a0")  # 点击后变浅灰

        project_link = ctk.CTkLabel(
            hyperlink_frame,
            text="项目主页",
            text_color=("black", "white"),  # 亮色主题黑字，暗色主题白字
            cursor="hand2",
            font=("SimHei", 12, "underline")
        )
        project_link.pack(side='left', padx=(0, 20))
        project_link.bind("<Button-1>", on_project_click)

        # 视频教程超链接
        def on_tutorial_click(event):
            import webbrowser
            webbrowser.open("https://www.bilibili.com/video/BV1V6VKz4ExV")  # 替换为实际链接
            # event.widget.configure(text_color="#a0a0a0")  # 点击后变浅灰

        tutorial_link = ctk.CTkLabel(
            hyperlink_frame,
            text="视频教程",
            text_color=("black", "white"),
            cursor="hand2",
            font=("SimHei", 12, "underline")
        )
        tutorial_link.pack(side='left')
        tutorial_link.bind("<Button-1>", on_tutorial_click)
        # ===== 新增代码结束 =====


        # 创建底部按钮框架
        button_frame = ctk.CTkFrame(preset_frame,fg_color=("#f1f2f3", "#242424"),bg_color=("#f1f2f3", "#242424"))
        button_frame.pack(side='bottom', fill='x', pady=(0, 10), padx=10)
        button_bold_font = ctk.CTkFont(
            family="SimHei",  # 设置字体为黑体
            size=15,
            weight="bold"  # 设置加粗
        )
        # 创建按钮 - 使用grid布局
        confirm_button = ctk.CTkButton(
            button_frame, 
            text="确定", 
            command=on_confirm,
            corner_radius=8,
            font=button_bold_font
        )
        new_button = ctk.CTkButton(
            button_frame, 
            text="新建", 
            command=on_new,
            corner_radius=8,
            font=button_bold_font
        )
        edit_button = ctk.CTkButton(
            button_frame, 
            text="编辑", 
            command=on_edit,
            corner_radius=8,
            font=button_bold_font
        )
        delete_button = ctk.CTkButton(
            button_frame, 
            text="删除", 
            command=on_delete,
            corner_radius=8,
            fg_color="#d9534f",
            hover_color="#c9302c",
            font=button_bold_font
        )
        
        # 将按钮放置在网格中
        confirm_button.grid(row=0, column=0, padx=5, sticky="ew")
        new_button.grid(row=0, column=1, padx=5, sticky="ew")
        edit_button.grid(row=0, column=2, padx=5, sticky="ew")
        delete_button.grid(row=0, column=3, padx=5, sticky="ew")
        
        # 配置网格列权重使按钮均匀分布
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.grid_columnconfigure(2, weight=1)
        button_frame.grid_columnconfigure(3, weight=1)

        download_frame = ctk.CTkFrame(tabview.tab("下载管理"),fg_color=("#f1f2f3", "#242424"),bg_color=("#f1f2f3", "#242424"))
        download_frame.pack(fill="both", expand=False)

        # MKP 分区
        mkp_frame = ctk.CTkFrame(download_frame, fg_color=("#f1f2f3", "#242424"))
        mkp_frame.pack(side="top", fill="both", expand=True, pady=5, padx=10)
        mkp_label = ctk.CTkLabel(mkp_frame, text="MKP预设", font=("SimHei", 14))
        mkp_label.pack(anchor="w", pady=5)

        # BBS 分区
        bbs_frame = ctk.CTkFrame(download_frame, fg_color=("#f1f2f3", "#242424"))
        bbs_frame.pack(side="top", fill="both", expand=True, pady=5, padx=10)
        bbs_label = ctk.CTkLabel(bbs_frame, text="BBS预设", font=("SimHei", 14))
        bbs_label.pack(anchor="w", pady=5)


        # ------------------------- MKP预设功能 -------------------------
        def fetch_mkp_presets():
            """联网拉取MKP预设列表"""
            base_url = "https://gitee.com/Jhmodel/MKPSupport/raw/main/Presets/"
            preset_files = ["A1.toml", "A1M.toml", "X1.toml"]  # 预设文件名列表
            presets = []

            for filename in preset_files:
                try:
                    # 获取预设文件的注释（第一行）
                    url = base_url + filename
                    response = requests.get(url)
                    response.raise_for_status()
                    
                    # 解析注释中的 release_time（格式为 "# release_time: 2025-07-11 10:36:09"）
                    first_line = response.text.split('\n')[0]
                    if "release_time:" in first_line:
                        publish_datetime_str = first_line.split("release_time:")[1].strip()
                        # 转换为 datetime 对象
                        publish_datetime = datetime.strptime(publish_datetime_str, "%Y-%m-%d %H:%M:%S")
                    else:
                        publish_datetime = None  # 标记为未知

                    # 检查本地是否有同名文件
                    local_path = os.path.join(folder_path, filename)
                    local_exists = os.path.exists(local_path)
                    local_datetime = None

                    if local_exists:
                        # 读取本地文件的 release_time
                        with open(local_path, 'r', encoding='utf-8') as f:
                            local_first_line = f.readline()
                            if "release_time:" in local_first_line:
                                local_datetime_str = local_first_line.split("release_time:")[1].strip()
                                local_datetime = datetime.strptime(local_datetime_str, "%Y-%m-%d %H:%M:%S")

                    # 状态标记
                    status = ""
                    button_text = "下载"
                    button_color = "#1E90FF"  # 蓝色
                    if local_exists:
                        if local_datetime and publish_datetime:
                            if publish_datetime > local_datetime:
                                status = "已过时"
                                button_text = "更新"
                                button_color = "#4CAF50"  # 绿色
                            else:
                                status = "最新"
                                button_text = "最新"
                                button_color = ("#A9A9A9","grey") # 灰色
                        else:
                            status = "已过时"
                            button_text = "更新"
                    else:
                        status = "未下载"

                    # 将 datetime 对象转换为字符串用于显示（可选）
                    publish_date_str = publish_datetime.strftime("%Y-%m-%d %H:%M:%S") if publish_datetime else "未知"
                    local_date_str = local_datetime.strftime("%Y-%m-%d %H:%M:%S") if local_datetime else "未知"

                    presets.append({
                        "filename": filename,
                        "publish_date": publish_date_str,  # 显示完整日期时间
                        "status": status,
                        "button_text": button_text,
                        "button_color": button_color,
                        "url": url,
                        "local_path": local_path,
                        "local_date": local_date_str  # 可选：本地文件的日期时间
                    })

                except Exception as e:
                    print(f"获取预设 {filename} 失败: {e}")


            return presets

        def update_mkp_presets():
            """更新MKP预设列表显示"""
            for widget in mkp_frame.winfo_children():
                if widget != mkp_label:
                    widget.destroy()

            presets = fetch_mkp_presets()
            container = ctk.CTkFrame(mkp_frame, height=120, fg_color=("white", "#1A1A1A"))
            container.pack_propagate(False)  # 阻止容器调整大小以适应其内容
            container.pack(fill="x", expand=False, padx=5, pady=0)
            scroll_frame = ctk.CTkScrollableFrame(container, fg_color=("white", "#1A1A1A"))
            scroll_frame.pack(fill="both", expand=True, padx=0, pady=0)  # 在容器内填充
            # scroll_frame = ctk.CTkScrollableFrame(mkp_frame, fg_color=("white", "#1A1A1A"))
            # scroll_frame.pack(fill="x", expand=False, padx=5, pady=0)

            for preset in presets:
                row_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
                row_frame.pack(fill="x", pady=2)

                filename_without_ext = preset['filename'].split('.')[0]  # 分割并取第一部分
                # 预设名称和release_time
                name_label = ctk.CTkLabel(
                    row_frame,
                    text = f"{filename_without_ext} TOML预设 (更新时间: {preset['publish_date']})",
                    # text=f"{preset['filename']} (更新时间: {preset['publish_date']})",
                    font=("SimHei", 12),
                    anchor="w"
                )
                name_label.pack(side="left", padx=5)

                # 状态标签
                status_color = "red" if preset["status"] == "已过时" else (("gray","white") if preset["status"] == "未下载" else ("black","white"))
                status_label = ctk.CTkLabel(
                    row_frame,
                    text=preset["status"],
                    text_color=status_color,
                    font=("SimHei", 12)
                )
                status_label.pack(side="left", padx=5)

                # 下载/更新按钮
                def download_preset(url=preset["url"], local_path=preset["local_path"]):
                    try:
                        response = requests.get(url)
                        response.raise_for_status()

                        # 解码远程文件内容（按行分割）
                        remote_content = response.content.decode('utf-8').split('\n')

                        if os.path.exists(local_path):
                            # 本地文件存在 → 替换第1行，保留第2~5行
                            with open(local_path, 'r', encoding='utf-8') as f:
                                local_lines = []
                                for i in range(5):  # 读取前5行
                                    line = next(f, '').strip('\n')
                                    if i == 0:
                                        # 第1行替换为远程文件的第1行
                                        local_lines.append(remote_content[0])
                                    else:
                                        # 保留本地文件的第2~5行
                                        local_lines.append(line)
                            # 组合：远程第1行 + 本地第2~5行 + 远程第6行及以后
                            new_content = '\n'.join(local_lines) + '\n' + '\n'.join(remote_content[5:])
                        else:
                            # 本地文件不存在 → 直接保存完整远程内容
                            new_content = '\n'.join(remote_content)

                        # 写入文件（二进制模式）
                        with open(local_path, 'wb') as f:
                            f.write(new_content.encode('utf-8'))

                        update_mkp_presets()  # 刷新列表
                        refresh_preset_frame_list()  # 刷新预设列表显示
                    except Exception as e:
                        print(f"下载失败: {e}")

                button_bold_font_mkp_update= ctk.CTkFont(
                    family="SimHei",  # 设置字体为黑体
                    size=13,
                    weight="bold"  # 设置加粗
                )

                button = ctk.CTkButton(
                    row_frame,
                    text=preset["button_text"],
                    fg_color=preset["button_color"],
                    command=download_preset if preset["button_text"] != "最新" else None,
                    state="disabled" if preset["button_text"] == "最新" else "normal",
                    font=button_bold_font_mkp_update,
                    width=60
                )
                button.pack(side="right", padx=5)
        # ------------------------- BBS预设功能 -------------------------      
        def load_bbs_presets():
            """加载BBS预设列表（左侧栏）"""
            bbs_path = os.path.join(os.getenv("APPDATA"), "BambuStudio", "user")
            if not os.path.exists(bbs_path):
                return []

            bbs_folders = [
                f for f in os.listdir(bbs_path) 
                if os.path.isdir(os.path.join(bbs_path, f)) 
                and not f[0].isalpha()  # 排除首字符是字母的情况
            ]

            return bbs_folders

        def update_bbs_presets():
            global right_label,right_frame
            """更新BBS预设列表显示"""
            # 清除整个bbs_frame的内容（除标签外）
            for widget in bbs_frame.winfo_children():
                if widget != bbs_label:
                    widget.destroy()

            # 左侧栏：文件夹列表
            left_frame = ctk.CTkFrame(bbs_frame, fg_color=("#f1f2f3", "#242424"))
            left_frame.pack(side="left", fill="y", padx=5, pady=5)
            right_frame = ctk.CTkFrame(bbs_frame, fg_color=("#f1f2f3", "#242424"))
            right_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)
            # 添加提示标签
            global refresh_bbs_rframe_list
            def refresh_bbs_rframe_list(folder):
                # right_label.configure(text=f"在线检索中")
                bbs_path = os.path.join(os.getenv("APPDATA"), "BambuStudio", "user", folder)
                if not os.path.exists(bbs_path):
                    return
                # right_label.destroy()
                # 创建一个滚动区域框架（如果需要）
                #清除右侧栏的内容
                for widget in right_frame.winfo_children():
                    widget.destroy()
                #如果存在滚动区域，则不再创建新的
                scroll_frame = ctk.CTkScrollableFrame(right_frame, fg_color=("white", "#1A1A1A"))
                scroll_frame.pack(fill="x", expand=True, padx=5, pady=5)
                # 机型列表
                machines = [
                    {"name": "A1 mini", "support_file": "MKPSupport A1 mini.json", "process_file": "MKPProcess A1 mini.json"},
                    {"name": "A1", "support_file": "MKPSupport A1.json", "process_file": "MKPProcess A1.json"},
                    {"name": "X1", "support_file": "MKPSupport X1.json", "process_file": "MKPProcess X1.json"},
                    {"name": "P1", "support_file": "MKPSupport P1S.json", "process_file": "MKPProcess P1S.json"},
                ]

                # 远程文件基础URL
                base_url = "https://gitee.com/Jhmodel/MKPSupport/raw/main/BBS_Presets/"

                for machine in machines:
                    # 为每个机器创建一个单独的框架
                    machine_frame = ctk.CTkFrame(scroll_frame, fg_color=("#f1f2f3", "#242424"))
                    machine_frame.pack(fill="x", pady=5, padx=5)

                    # 显示机器名称（标签）
                    machine_label = ctk.CTkLabel(
                        machine_frame,
                        text=machine["name"],
                        width=100,
                        anchor="w"
                    )
                    machine_label.pack(side="left", padx=5)
                    
                    # 检查本地文件是否存在
                    support_local_path = os.path.join(bbs_path, "machine", machine["support_file"])
                    process_local_path = os.path.join(bbs_path, "process", machine["process_file"])
                    support_exists = os.path.exists(support_local_path)
                    process_exists = os.path.exists(process_local_path)

                    # 检查远程文件是否存在
                    support_remote_url = base_url + machine["support_file"]
                    process_remote_url = base_url + machine["process_file"]
                    support_remote_exists = check_remote_file_exists(support_remote_url)
                    process_remote_exists = check_remote_file_exists(process_remote_url)

                    # 判断按钮状态
                    button_text = "最新"
                    button_color = "gray"
                    if not support_exists or not process_exists:
                        button_text = "下载"
                        button_color = "red"
                    else:
                        # 检查文件内容是否一致
                        support_local_content = None
                        process_local_content = None
                        if support_exists:
                            with open(support_local_path, 'r', encoding='utf-8') as f:
                                support_local_content = f.read()
                        if process_exists:
                            with open(process_local_path, 'r', encoding='utf-8') as f:
                                process_local_content = f.read()
                        support_remote_content = get_remote_file_content(support_remote_url)
                        process_remote_content = get_remote_file_content(process_remote_url)
                        try:
                            # 直接比较 support 文件
                            support_local_lines = support_local_content.splitlines() if support_local_content else []
                            support_remote_lines = support_remote_content.splitlines() if support_remote_content else []
                            process_local_lines = process_local_content.splitlines() if process_local_content else []
                            process_remote_lines = process_remote_content.splitlines() if process_remote_content else []
                            Differ_Flag = False  # 用于标记是否有差异
                            for i, (local_line, remote_line) in enumerate(zip(support_local_lines, support_remote_lines)):
                                if local_line != remote_line and process_local_path.find("X1")==-1 and process_local_path.find("P1")==-1:
                                    Differ_Flag = True
                                    print(f"第{i+1}行不同: 本地='{local_line}', 远程='{remote_line}'")

                            # 检查行数是否不同
                            if len(support_local_lines) != len(support_remote_lines) and process_local_path.find("X1")==-1 and process_local_path.find("P1")==-1:
                                Differ_Flag = True
                                print(f"行数不同: 本地={len(support_local_lines)}, 远程={len(support_remote_lines)}")
                        
                            for i, (local_line, remote_line) in enumerate(zip(process_local_lines, process_remote_lines)):
                                if local_line != remote_line and remote_line.find("请将")==-1:
                                    Differ_Flag = True
                                    print(f"第{i+1}行不同: 本地='{local_line}', 远程='{remote_line}'")
                            
                            if len(process_local_lines) != len(process_remote_lines):
                                Differ_Flag = True
                                print(f"行数不同: 本地={len(process_local_lines)}, 远程={len(process_remote_lines)}")
                            if support_local_path.find("X1")!=-1 and support_local_path.find("P1")!=-1:
                                Differ_Flag = False  # X1和P1的配置文件不进行内容比较
                        except:
                            Differ_Flag = True

                        # print(f"Support Match: {support_match}, Process Match: {process_match}")
                        if Differ_Flag and machine["name"].find("X1")==-1 and machine["name"].find("P1")==-1:
                            button_text = "更新"
                            button_color = "green"

                    # 创建状态按钮
                    state_button = ctk.CTkButton(
                        machine_frame,
                        text=button_text,
                        font=("SimHei", 12),
                        fg_color=button_color,
                        width=80,
                        command=lambda f=folder, m=machine, a=button_text: handle_machine_action(f, m, a)
                    )
                    state_button.pack(side="right", padx=5)
                right_label.destroy()
            right_label = ctk.CTkLabel(right_frame, text="点击选择用户后，右侧栏会显示内容",font=("SimHei", 14))
            right_label.pack(expand=True)
            folders = load_bbs_presets()
            def refresh_right_label():
                try:
                    right_label.configure(text="在线检索中")
                except:
                    pass
            for folder in folders:
                folder_button = ctk.CTkButton(
                    left_frame,
                    text=folder,
                    # command=lambda f=folder: refresh_bbs_rframe_list(f),
                    command = lambda f=folder: (
                        refresh_right_label,  # 先更新标签文字
                        refresh_bbs_rframe_list(f)                # 再执行刷新操作
                    ),
                    width=120,
                    font=("SimHei", 12)
                )
                folder_button.pack(pady=2)


        def check_remote_file_exists(url):
            """检查远程文件是否存在"""
            try:
                response = requests.head(url)
                return response.status_code == 200
            except:
                return False

        def get_remote_file_content(url):
            """获取远程文件内容"""
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    return response.content.decode('utf-8')
                return None
            except:
                return None

        def compare_files(local_content, remote_content):
            """比较本地文件和远程文件内容是否一致"""
            # if local_content is None or remote_content is None:
            #     return False
            return local_content.strip() == remote_content.strip()

        def handle_machine_action(folder, machine, action):
            """处理机器配置文件的下载或更新操作"""
            # 基础路径
            bbs_path = os.path.join(os.getenv("APPDATA"), "BambuStudio", "user", folder)
            remote_base_url = "https://gitee.com/Jhmodel/MKPSupport/raw/main/BBS_Presets/"
            
            try:
                if action == "下载":
                    # 确保目录存在
                    os.makedirs(os.path.join(bbs_path, "machine"), exist_ok=True)
                    os.makedirs(os.path.join(bbs_path, "process"), exist_ok=True)
                    
                    # 下载支持文件
                    support_url = remote_base_url + machine["support_file"]
                    support_content = requests.get(support_url).content
                    with open(os.path.join(bbs_path, "machine", machine["support_file"]), "wb") as f:
                        f.write(support_content)
                    
                    # 下载流程文件
                    process_url = remote_base_url + machine["process_file"]
                    process_content = requests.get(process_url).content
                    with open(os.path.join(bbs_path, "process", machine["process_file"]), "wb") as f:
                        f.write(process_content)
                    
                    print(f"✅ 已下载 {machine['name']} 的配置文件")
                
                elif action == "更新":
                    # 更新支持文件
                    support_url = remote_base_url + machine["support_file"]
                    support_content = requests.get(support_url).content
                    with open(os.path.join(bbs_path, "machine", machine["support_file"]), "wb") as f:
                        f.write(support_content)
                    
                    # 更新流程文件
                    process_url = remote_base_url + machine["process_file"]
                    process_content = requests.get(process_url).content
                    with open(os.path.join(bbs_path, "process", machine["process_file"]), "wb") as f:
                        f.write(process_content)
                    
                    print(f"🔄 已更新 {machine['name']} 的配置文件")
                
                elif action == "最新":
                    print(f"ℹ️ {machine['name']} 的配置文件已是最新，无需操作")
                
                # 操作完成后刷新右侧面板
                
            
            except requests.exceptions.RequestException as e:
                print(f"❌ 网络错误: {e}")
            except IOError as e:
                print(f"❌ 文件操作错误: {e}")
            except Exception as e:
                print(f"❌ 未知错误: {e}")

            refresh_bbs_rframe_list(folder)



        # 初始化显示
        update_mkp_presets()
        update_bbs_presets()
        #calibr_dir
        CALIBR_DIR = os.path.join(os.path.join(os.path.expanduser("~/Documents"), "MKPSupport"), "Data", "Calibr")
        GITEE_URL = "https://gitee.com/Jhmodel/MKPSupport/raw/main/Calibr"
        FILES = {
            "ZOffset Calibration.3mf": "喷嘴笔尖高度差校准",
            "Precise Calibration.3mf": "XY偏移值校准",
            "LShape Calibration.3mf": "L形精密度校准"
        }

        # ------------------------- 自动校准标签页 -------------------------
        calibr_preset = ctk.CTkFrame(tabview.tab("自动校准"), fg_color=("#f1f2f3", "#242424"), bg_color=("#f1f2f3", "#242424"))
        calibr_preset.pack(fill="both", expand=True, padx=10, pady=10)
        cali_button_font = ctk.CTkFont(
            family="SimHei",  # 设置字体为黑体
            size=14
        )
        # ------------------------- 喷嘴笔尖高度差校准分区 -------------------------
        # 创建容器
        z_container = ctk.CTkFrame(calibr_preset, height=100,fg_color=("#f1f2f3", "#242424"),border_width=1 )  # 固定高度容器
        z_container.pack(fill="x", expand=False, padx=0, pady=(0, 10))
        z_frame = ctk.CTkFrame(z_container,fg_color=("#f1f2f3", "#242424"))
        z_frame.pack(fill="both", expand=True, padx=10,pady=5)

        # 标题和保存选项的父容器
        title_save_frame = ctk.CTkFrame(z_frame, fg_color="transparent")
        title_save_frame.pack(fill="x", expand=True, pady=5)

        # 标题靠左
        ctk.CTkLabel(title_save_frame, text="喷嘴笔尖高度差校准", font=("SimHei", 14)).pack(side="left")

        # 保存选项靠右
        save_frame = ctk.CTkFrame(title_save_frame, fg_color="transparent")
        save_frame.pack(side="right")

        # 1. 定义 MKPSupport 文件夹路径
        documents_path = os.path.expanduser("~/Documents")  # 跨平台 Documents 路径
        mkpsupport_path = os.path.join(documents_path, "MKPSupport")
        # 2. 扫描 .toml 文件并提取文件名（不带扩展名）
        def get_toml_presets():
            if not os.path.exists(mkpsupport_path):
                return ["MKP预设"]  # 默认值（如果文件夹不存在）
            
            toml_files = []
            for file in os.listdir(mkpsupport_path):
                if file.endswith(".toml"):
                    toml_files.append(os.path.splitext(file)[0])  # 去掉扩展名
            
            return toml_files if toml_files else ["MKP预设"]  # 若无文件，返回默认值

        ctk.CTkLabel(save_frame, text="保存到:",font=cali_button_font).pack(side="left")

        # 使用扫描到的 .toml 文件名作为选项
        z_save_option = ctk.CTkOptionMenu(
            save_frame, 
            values=get_toml_presets(),  # 动态加载选项
            dropdown_fg_color=("#f1f2f3", "#242424"),  # 下拉菜单背景色
            # dropdown_corner_radius=6
        )
        z_save_option.pack(side="left", padx=5)
        CTkScrollableDropdown(z_save_option, values=get_toml_presets(),fg_color=("#ebebed", "#1a1a1a"),frame_corner_radius=16,frame_border_width=1,frame_border_color=("#d1d1d1", "#3a3a3a"))
        # 按钮和文件检查
        filepath = os.path.join(CALIBR_DIR, "ZOffset Calibration.3mf")
        if os.path.exists(filepath):
            z_button_text = "开始校准"
            z_button_color = "green"
        else:
            z_button_text = "下载"
            z_button_color = "#1E90FF"
        button_outer_frame = ctk.CTkFrame(z_frame, fg_color="transparent")
        button_outer_frame.pack(fill="x", expand=True, pady=5,anchor="center")
        button_frame = ctk.CTkFrame(button_outer_frame, fg_color="transparent")
        button_frame.pack(anchor="center")

        z_button = ctk.CTkButton(button_frame,font=cali_button_font, text=z_button_text,fg_color=z_button_color, command=lambda: check_or_download("ZOffset Calibration.3mf", z_button))
        z_button.pack(pady=5,side="left", padx=5)
        # 保存按钮

        ZSave=ctk.CTkButton(button_frame,font=cali_button_font, text="保存", command=lambda: save_z_offset())
        ZSave.pack(pady=5, side="left", padx=5)
        ZSave.configure(state="disabled",fg_color="grey")  # 初始状态禁用
        # ------------------------- XY偏移值校准分区 -------------------------

        # 创建 XY 偏移值校准容器
        xy_container = ctk.CTkFrame(calibr_preset, height=100, fg_color=("#f1f2f3", "#242424"), border_width=1)
        xy_container.pack(fill="x", expand=False, padx=0, pady=(0, 10))
        xy_frame = ctk.CTkFrame(xy_container, fg_color=("#f1f2f3", "#242424"))
        xy_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # 标题和保存选项的父容器
        title_save_frame = ctk.CTkFrame(xy_frame, fg_color="transparent")
        title_save_frame.pack(fill="x", expand=True, pady=5)

        # 标题靠左
        ctk.CTkLabel(title_save_frame, text="XY偏移值校准", font=("SimHei", 14)).pack(side="left")

        # 保存选项靠右
        save_frame = ctk.CTkFrame(title_save_frame, fg_color="transparent")
        save_frame.pack(side="right")

        # 扫描 .toml 文件并提取文件名（不带扩展名）
        def get_toml_presets():
            documents_path = os.path.expanduser("~/Documents")  # 跨平台 Documents 路径
            mkpsupport_path = os.path.join(documents_path, "MKPSupport")
            
            if not os.path.exists(mkpsupport_path):
                return ["MKP预设"]  # 默认值（如果文件夹不存在）
            
            toml_files = []
            for file in os.listdir(mkpsupport_path):
                if file.endswith(".toml"):
                    toml_files.append(os.path.splitext(file)[0])  # 去掉扩展名
            
            return toml_files if toml_files else ["MKP预设"]  # 若无文件，返回默认值

        # 保存到选项
        ctk.CTkLabel(save_frame, text="保存到:",font=cali_button_font).pack(side="left")
        xy_save_option = ctk.CTkOptionMenu(
            save_frame,
            values=get_toml_presets(),  # 动态加载选项
            dropdown_fg_color=("#f1f2f3", "#242424")  # 下拉菜单背景色
        )
        xy_save_option.pack(side="left", padx=5)
        CTkScrollableDropdown(
            xy_save_option,
            values=get_toml_presets(),
            fg_color=("#ebebed", "#1a1a1a"),
            frame_corner_radius=16,
            frame_border_width=1,
            frame_border_color=("#d1d1d1", "#3a3a3a")
        )

        # 检查文件状态并设置按钮
        filepath = os.path.join(CALIBR_DIR, "Precise Calibration.3mf")
        if os.path.exists(filepath):
            xy_button_text = "开始校准"
            xy_button_color = "green"
        else:
            xy_button_text = "下载"
            xy_button_color = "#1E90FF"
        
        # 按钮外层容器（用于居中）
        button_outer_frame = ctk.CTkFrame(xy_frame, fg_color="transparent")
        button_outer_frame.pack(fill="x", expand=True, pady=5, anchor="center")

        # 按钮内层容器（用于并排靠拢）
        button_frame = ctk.CTkFrame(button_outer_frame, fg_color="transparent")
        button_frame.pack(anchor="center")

        # 检查文件状态并设置按钮
        filepath = os.path.join(CALIBR_DIR, "Precise Calibration.3mf")
        if os.path.exists(filepath):
            xy_button_text = "开始校准"
            xy_button_color = "green"
        else:
            xy_button_text = "下载"
            xy_button_color = "#1E90FF"

        xy_button = ctk.CTkButton(
            button_frame,
            text=xy_button_text,
            fg_color=xy_button_color,
            command=lambda: check_or_download("Precise Calibration.3mf", xy_button),
            font=cali_button_font
        )
        xy_button.pack(pady=5, side="left", padx=5)

        # 保存按钮
        XYSave=ctk.CTkButton(
            button_frame,
            text="保存",
            command=lambda: save_xy_offset(),
            font=cali_button_font
        )
        XYSave.pack(pady=5, side="left", padx=5)
        XYSave.configure(state="disabled", fg_color="grey")  # 初始状态禁用
        # ------------------------- L形精密度校准分区 -------------------------
        # 创建容器
        l_container = ctk.CTkFrame(calibr_preset, height=100, fg_color=("#f1f2f3", "#242424"), border_width=1)
        l_container.pack(fill="x", expand=False, padx=0, pady=(0, 10))
        l_frame = ctk.CTkFrame(l_container, fg_color=("#f1f2f3", "#242424"))
        l_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # 标题和保存选项的父容器（仅保留标题）
        title_frame = ctk.CTkFrame(l_frame, fg_color="transparent")
        title_frame.pack(fill="x", expand=True, pady=5)

        # 标题靠左
        ctk.CTkLabel(title_frame, text="L形精密度校准", font=("SimHei", 14)).pack(side="left")

        # 按钮和文件检查
        filepath = os.path.join(CALIBR_DIR, "LShape Calibration.3mf")
        if os.path.exists(filepath):
            l_button_text = "开始校准"
            l_button_color = "green"
        else:
            l_button_text = "下载"
            l_button_color = "#1E90FF"

        l_button = ctk.CTkButton(
            title_frame,
            text=l_button_text,
            fg_color=l_button_color,
            command=lambda: check_or_download("LShape Calibration.3mf", l_button),
            font=cali_button_font
        )
        l_button.pack(pady=5,side="right", padx=5)


        # ------------------------- 功能函数（使用 ctk 对话框） -------------------------
        def check_or_download(filename, button):
            """检查文件是否存在，否则下载"""
            filepath = os.path.join(CALIBR_DIR, filename)
            if not os.path.exists(CALIBR_DIR):
                os.makedirs(CALIBR_DIR, exist_ok=True)

            if os.path.exists(filepath):
                button.configure(text="开始校准", fg_color="green")
                #启动filename对应的3mf
                os.startfile(filepath)
                show_calibration_prompt(filename)

            else:
                button.configure(text="下载", fg_color="red")
                # if ask_yesno_dialog("确认", f"下载 {filename}？"):
                download_file(filename, button)
                # show_calibration_prompt(filename)

        def download_file(filename, button):
            """从Gitee下载文件"""
            try:
                response = requests.get(f"{GITEE_URL}/{filename}")
                response.raise_for_status()
                with open(os.path.join(CALIBR_DIR, filename), "wb") as f:
                    f.write(response.content)
                button.configure(text="开始校准", fg_color="green")
                # show_calibration_prompt(filename)
            except Exception as e:
                pass
                # show_error_dialog("错误", f"下载失败: {e}")



        def show_calibration_prompt(filename):
            dialog = ctk.CTkToplevel()
            dialog.title("校准")
            dialog.geometry("1200x600")
            # dialog.resizable(False, False)
            # dialog.geometry()
            dialog.geometry(CenterWindowToDisplay(dialog, 700, 500, dialog._get_window_scaling()))
            # selection_dialog.geometry(CenterWindowToDisplay(selection_dialog, 550, 400, selection_dialog._get_window_scaling()))
            mkpexecutable_dir = os.path.dirname(sys.executable)
            mkpinternal_dir = os.path.join(mkpexecutable_dir, "resources")
            dialog.attributes("-topmost", True)  # 确保对话框在最上层
            
            def continue_function():
                popup = ctk.CTkToplevel(dialog)
                
                popup.title("继续校准")
                popup.geometry("450x60")
                popup.geometry(CenterWindowToDisplay(popup, 450, 230, popup._get_window_scaling()))
                # popup.attributes("-topmost", True)  # 确保弹窗在最上层
                # dialog.attributes("-topmost", False)  # 取消强制置顶
                # dialog.lower()  # 移动到最后一层

                # label_observation = ctk.CTkLabel(
                #     popup,
                #     text="您观察到，涂胶最合适的平面是",
                #     font=("SimHei", 14)
                # )
                # label_observation.pack(pady=(20, 10))

                # 第二行：连贯的下拉菜单
                frame_selection = ctk.CTkFrame(popup, fg_color="transparent")
                frame_selection.pack()

                # 左侧/右侧选择
                label_side = ctk.CTkLabel(
                    frame_selection,
                    text="涂胶最合适的平面是",
                    font=("SimHei", 14)
                )
                label_side.pack(side="left", padx=(0, 5),pady=20)                
                side_var = ctk.StringVar(value="左侧")
                side_menu = ctk.CTkOptionMenu(
                    frame_selection,
                    values=["左侧", "右侧"],
                    variable=side_var,
                    font=("SimHei", 14),
                    width=80
                )
                
                side_menu.pack(side="left", padx=(0, 5))
                CTkScrollableDropdown(side_menu, values=["左侧", "右侧"],fg_color=("#ebebed", "#1a1a1a"),frame_corner_radius=16,frame_border_width=1,frame_border_color=("#d1d1d1", "#3a3a3a"))
                # 第几个平面选择
                label_plane = ctk.CTkLabel(
                    frame_selection,
                    text="小数点后为",
                    font=("SimHei", 14)
                )
                label_plane.pack(side="left", padx=(0, 5))
                plane_var = ctk.StringVar(value="1")
                plane_menu = ctk.CTkOptionMenu(
                    frame_selection,
                    values=[str(i) for i in range(1,6)],  # 0到5
                    variable=plane_var,
                    font=("SimHei", 14),
                    width=60
                )
                plane_menu.pack(side="left", padx=(0, 5))
                CTkScrollableDropdown(plane_menu, values=[str(i) for i in range(1,6)],fg_color=("#ebebed", "#1a1a1a"),frame_corner_radius=16,frame_border_width=1,frame_border_color=("#d1d1d1", "#3a3a3a"))

                

                label_unit = ctk.CTkLabel(
                    frame_selection,
                    text="的平面",
                    font=("SimHei", 14)
                )
                label_unit.pack(side="left")

                # 确定按钮
                def confirm_selection():
                    try:
                        side = side_var.get()
                        plane = plane_var.get()
                    except:
                        tk.messagebox.showinfo("错误", "side_var或plane_var未正确设置")
                    # tk.messagebox.showinfo("错误", "请选择左侧或右侧，并选择平面")
                    print(f"选择的平面：{side}第{plane}个平面")
                    if side == "左侧":
                        result = float(plane) * 0.1  # 正数
                    elif side == "右侧":
                        result = float(plane) * -0.1  # 负数
                    else:
                        result = float(plane) * 0.1  # 正数
                        # result = 0  # 默认值（可选）
                    print(f"计算结果：{result}")
                    # return result  # 返回数字变量
                    para.Temp_ZOffset_Calibr= result
                    # 关闭弹窗和对话框
                    ZSave.configure(state="normal",fg_color="green")  # 启用保存按钮
                    popup.withdraw()  # 隐藏弹窗
                    popup.destroy()  # 关闭弹窗
                    dialog.destroy()  # 关闭原始对话框
                bottom_frame = ctk.CTkFrame(popup, fg_color="transparent",height=30)
                bottom_frame.pack(fill="x", expand=True, pady=10)  # 添加底部框架

                confirm_button = ctk.CTkButton(
                    bottom_frame,
                    text="确定",
                    command=lambda:confirm_selection(),
                    font=("SimHei", 14),
                    width=100
                )
                confirm_button.pack(pady=20)
                dialog.withdraw()  # 隐藏原始对话框
                # 添加提示信息
                # popup.attributes("-topmost", True)  # 确保弹窗在最上层
                # popup.lift()  # 确保弹窗在最上层
                # popup.lift()  # 确保弹窗在最上层

            def xy_continue_function():
                popup = ctk.CTkToplevel(dialog)
                
                popup.title("继续校准")
                popup.geometry("450x400")
                popup.geometry(CenterWindowToDisplay(popup, 450,270, popup._get_window_scaling()))
                # popup.attributes("-topmost", True)  # 确保弹窗在最上层
                # dialog.attributes("-topmost", False)  # 取消强制置顶
                # dialog.lower()  # 移动到最后一层

                label_observation = ctk.CTkLabel(
                    popup,
                    text="与笔尖运动轨迹最重合的横线是中央0线",
                    font=("SimHei", 14)
                )
                label_observation.pack(pady=(20, 10))

                # 第二行：连贯的下拉菜单
                frame_selection = ctk.CTkFrame(popup, fg_color="transparent")
                frame_selection.pack()

                side_var_y = ctk.StringVar(value="本身")
                # side_var_y = ctk.StringVar(value="上方")
                side_menu_y = ctk.CTkOptionMenu(
                    frame_selection,
                    values=["上方", "下方","本身"],
                    variable=side_var_y,
                    font=("SimHei", 14),
                    width=80
                )
                side_menu_y.pack(side="left", padx=(0, 5))
                CTkScrollableDropdown(side_menu_y, values=["上方", "下方","本身"], fg_color=("#ebebed", "#1a1a1a"), frame_corner_radius=16, frame_border_width=1, frame_border_color=("#d1d1d1", "#3a3a3a"))
                def update_visibility(*_):
                    if side_var_y.get() == "本身":
                        label_plane_y.pack_forget()    # 隐藏
                        plane_menu_y.pack_forget()
                        label_unit_y.pack_forget()     # 新增的隐藏
                    else:
                        # 按顺序重新显示控件（保证布局一致）
                        label_plane_y.pack(side="left", padx=(0, 5))
                        plane_menu_y.pack(side="left", padx=(0, 5))
                        label_unit_y.pack(side="left", padx=(0, 5))  # 新增的显示
                side_var_y.trace_add("write", update_visibility)
                # 第几个平面选择
                label_plane_y = ctk.CTkLabel(
                    frame_selection,
                    text="第",
                    font=("SimHei", 14)
                )
                # label_plane_y.pack(side="left", padx=(0, 5))

                plane_var_y = ctk.StringVar(value="1")
                plane_menu_y = ctk.CTkOptionMenu(
                    frame_selection,
                    values=[str(i) for i in range(1, 6)],  # 1到5
                    variable=plane_var_y,
                    font=("SimHei", 14),
                    width=60
                )
                # plane_menu_y.pack(side="left", padx=(0, 5))
                CTkScrollableDropdown(plane_menu_y, values=[str(i) for i in range(1, 6)], fg_color=("#ebebed", "#1a1a1a"), frame_corner_radius=16, frame_border_width=1, frame_border_color=("#d1d1d1", "#3a3a3a"))

                label_unit_y = ctk.CTkLabel(
                    frame_selection,
                    text="根线",
                    font=("SimHei", 14)
                )
                # label_unit_y.pack(side="left")

                
                label_observation1 = ctk.CTkLabel(
                    popup,
                    text="与笔尖运动轨迹最重合的纵线是中央0线",
                    font=("SimHei", 14)
                )
                label_observation1.pack(pady=(20, 10))
                frame_selection1 = ctk.CTkFrame(popup, fg_color="transparent")
                frame_selection1.pack()
                side_var_x = ctk.StringVar(value="本身")
                # side_var_x = ctk.StringVar(value="左侧")
                side_menu_x = ctk.CTkOptionMenu(
                    frame_selection1,
                    values=["左侧", "右侧", "本身"],  # 添加"本身"选项
                    variable=side_var_x,
                    font=("SimHei", 14),
                    width=80
                )
                side_menu_x.pack(side="left", padx=(0, 5))
                CTkScrollableDropdown(side_menu_x, values=["左侧", "右侧", "本身"], fg_color=("#ebebed", "#1a1a1a"), frame_corner_radius=16, frame_border_width=1, frame_border_color=("#d1d1d1", "#3a3a3a"))
                
                
                def update_visibility_x(*_):
                    if side_var_x.get() == "本身":
                        label_plane_x.pack_forget()    # 隐藏   
                        plane_menu_x.pack_forget()
                        label_unit_x.pack_forget()     # 新增的隐藏
                    else:
                        # 按顺序重新显示控件（保证布局一致）
                        label_plane_x.pack(side="left", padx=(0, 5))
                        plane_menu_x.pack(side="left", padx=(0, 5))
                        label_unit_x.pack(side="left", padx=(0, 5))
                side_var_x.trace_add("write", update_visibility_x)  # 添加监听器
                # 第几个平面选择
                label_plane_x = ctk.CTkLabel(
                    frame_selection1,
                    text="第",
                    font=("SimHei", 14)
                )
                # label_plane_x.pack(side="left", padx=(0, 5))

                plane_var_x = ctk.StringVar(value="1")
                plane_menu_x = ctk.CTkOptionMenu(
                    frame_selection1,
                    values=[str(i) for i in range(1, 6)],  # 1到5
                    variable=plane_var_x,
                    font=("SimHei", 14),
                    width=60
                )
                # plane_menu_x.pack(side="left", padx=(0, 5))
                CTkScrollableDropdown(plane_menu_x, values=[str(i) for i in range(1, 6)], fg_color=("#ebebed", "#1a1a1a"), frame_corner_radius=16, frame_border_width=1, frame_border_color=("#d1d1d1", "#3a3a3a"))

                label_unit_x = ctk.CTkLabel(
                    frame_selection1,
                    text="根线",
                    font=("SimHei", 14)
                )
                # label_unit_x.pack(side="left")

                # 确定按钮
                def confirm_selection():
                    # Get values for _x and _y variants
                    side_x = side_var_x.get()
                    plane_x = plane_var_x.get()
                    side_y = side_var_y.get()  # Assuming you have a `side_var_y` defined elsewhere
                    plane_y = plane_var_y.get()  # Assuming you have a `plane_var_y` defined elsewhere

                    # Print selections
                    print(f"X方向选择的平面：{side_x}第{plane_x}个平面")
                    print(f"Y方向选择的平面：{side_y}第{plane_y}个平面")

                    # Calculate results for X and Y
                    if side_x == "左侧":
                        result_x = float(plane_x) * -0.2  # Positive for left (X)
                    elif side_x == "右侧":
                        result_x = float(plane_x) * 0.2  # Negative for right (X)
                    else:
                        result_x = 0  # Default (optional)

                    if side_y == "上方":
                        result_y = float(plane_y) * 0.2  # Positive for top (Y)
                    elif side_y == "下方":
                        result_y = float(plane_y) * -0.2  # Negative for bottom (Y)
                    else:
                        result_y = 0  # Default (optional)

                    # Print results
                    print(f"X方向计算结果：{result_x}")
                    print(f"Y方向计算结果：{result_y}")

                    # return result  # 返回数字变量
                    para.Temp_XOffset_Calibr= result_x
                    para.Temp_YOffset_Calibr= result_y
                    # 关闭弹窗和对话框
                    XYSave.configure(state="normal",fg_color="green")  # 启用保存按钮
                    popup.withdraw()  # 隐藏弹窗
                    popup.destroy()  # 关闭弹窗
                    dialog.destroy()  # 关闭原始对话框
                bottom_frame = ctk.CTkFrame(popup, fg_color="transparent",height=30)
                bottom_frame.pack(fill="x", expand=True, pady=10)  # 添加底部框架

                confirm_button = ctk.CTkButton(
                    bottom_frame,
                    text="确定",
                    command=lambda:confirm_selection(),
                    font=("SimHei", 14),
                    width=100
                )
                confirm_button.pack(pady=20)
                dialog.withdraw()  # 隐藏原始对话框
                # 添加提示信息
                # popup.attributes("-topmost", True)  # 确保弹窗在最上层
                # popup.lift()  # 确保弹窗在最上层
                # popup.lift()  # 确保弹窗在最上层
                
            def show_calibration_message():
                 # 创建一个顶层窗口作为弹窗
                popup = ctk.CTkToplevel(dialog)
                popup.title("校准完成")
                popup.geometry("300x200")
                popup.geometry(CenterWindowToDisplay(popup, 300, 200, popup._get_window_scaling()))
                popup.attributes("-topmost", True)  # 确保弹窗在最上层
                # 添加提示信息
                label = ctk.CTkLabel(popup, text="您的喷嘴笔尖高度差已经校准")
                label.pack(pady=40)
                # 添加关闭按钮
                button_frame = ctk.CTkFrame(popup, fg_color="transparent")
                button_frame.pack(pady=10)
                dialog.withdraw()  # 隐藏原始对话框
                def close_dialog():
                    popup.withdraw()  # 隐藏弹窗
                    popup.destroy()
                    dialog.destroy()
                close_button = ctk.CTkButton(button_frame, text="确定", command=lambda:close_dialog())
                close_button.pack(pady=10)

            def show_calibration_message_xy():
                 # 创建一个顶层窗口作为弹窗
                popup = ctk.CTkToplevel(dialog)
                popup.title("校准完成")
                popup.geometry("300x200")
                popup.geometry(CenterWindowToDisplay(popup, 300, 200, popup._get_window_scaling()))
                popup.attributes("-topmost", True)  # 确保弹窗在最上层
                # 添加提示信息
                label = ctk.CTkLabel(popup, text="您的XY偏移值已经校准")
                label.pack(pady=40)
                # 添加关闭按钮
                button_frame = ctk.CTkFrame(popup, fg_color="transparent")
                button_frame.pack(pady=10)
                dialog.withdraw()  # 隐藏原始对话框
                def close_dialog():
                    popup.withdraw()  # 隐藏弹窗
                    popup.destroy()
                    dialog.destroy()
                close_button = ctk.CTkButton(button_frame, text="确定", command=lambda:close_dialog())
                close_button.pack(pady=10)
               
                # dialog.destroy()  # 关闭原始对话框
            if filename == "ZOffset Calibration.3mf":
                dialog.title("喷嘴笔尖高度差校准")
                # 主框架
                frame = ctk.CTkFrame(dialog)
                frame.pack(fill="both", expand=True, padx=20, pady=20)
                mkpimage_path = os.path.join(mkpinternal_dir, "z_calibr.png")
                # 显示图片
                # if os.path.exists(mkpimage_path):
                image = ctk.CTkImage(light_image=Image.open(mkpimage_path), dark_image=Image.open(mkpimage_path),size=(640, 320))
                image_label = ctk.CTkLabel(frame, image=image, text="")
                image_label.pack(pady=10)
                #询问label
                prompt_label = ctk.CTkLabel(frame, text="数字0所对应的平面在涂胶时是否出现未涂胶,涂胶过多,或涂胶时笔尖摇晃的问题?")
                prompt_label.pack(pady=10)
                button_frame = ctk.CTkFrame(frame,fg_color="transparent")
                button_frame.pack(pady=10)
                # "存在"按钮
                exist_button = ctk.CTkButton(
                    button_frame,
                    text="存在",
                    command=continue_function
                )
                exist_button.pack(pady=10,side="right", padx=5)

                # "不存在"按钮
                not_exist_button = ctk.CTkButton(
                    button_frame,
                    text="不存在",
                    command=show_calibration_message
                )
                not_exist_button.pack(pady=10, side="right", padx=5)
              
            elif filename == "Precise Calibration.3mf":
                dialog.title("XY偏移值校准")
                # 主框架
                frame = ctk.CTkFrame(dialog)
                frame.pack(fill="both", expand=True, padx=20, pady=20)
                mkpimage_path = os.path.join(mkpinternal_dir, "xy_calibr.png")
                # 显示图片
                # if os.path.exists(mkpimage_path):
                image = ctk.CTkImage(light_image=Image.open(mkpimage_path), dark_image=Image.open(mkpimage_path),size=(640, 320))
                image_label = ctk.CTkLabel(frame, image=image, text="")
                image_label.pack(pady=10)
                #询问label
                prompt_label = ctk.CTkLabel(frame, text="涂胶时,笔尖的移动轨迹完全重合的横线或纵线是否是中央0线?")
                prompt_label.pack(pady=10)
                button_frame = ctk.CTkFrame(frame,fg_color="transparent")
                button_frame.pack(pady=10)
                # "存在"按钮
                exist_button = ctk.CTkButton(
                    button_frame,
                    text="否",
                    command=xy_continue_function
                )
                exist_button.pack(pady=10,side="right", padx=5)

                # "不存在"按钮
                not_exist_button = ctk.CTkButton(
                    button_frame,
                    text="是",
                    command=show_calibration_message_xy
                )
                not_exist_button.pack(pady=10, side="right", padx=5)
                pass
                # prompt = f"您观察到与笔尖完美重合的横线是中央0横线的{xy_h_dir.get()}第{xy_h_plane.get()}根线；\n"
                # prompt += f"与笔尖完美重合的纵线是中央0纵线的{xy_v_dir.get()}第{xy_v_plane.get()}根线。"
            elif filename == "LShape Calibration.3mf":
                # dialog.title("喷嘴笔尖高度差校准")
                dialog.title("L形精密度校准")
                # 主框架
                frame = ctk.CTkFrame(dialog)
                frame.pack(fill="both", expand=True, padx=20, pady=20)
                mkpimage_path = os.path.join(mkpinternal_dir, "lshape.png")
                # 显示图片
                # if os.path.exists(mkpimage_path):
                image = ctk.CTkImage(light_image=Image.open(mkpimage_path), dark_image=Image.open(mkpimage_path),size=(640, 320))
                image_label = ctk.CTkLabel(frame, image=image, text="")
                image_label.pack(pady=10)
                #询问label
                prompt_label = ctk.CTkLabel(frame, text="请检查涂胶过程中笔尖的机械稳定性。如发现异常振动或位移，需确认装配部件是否存在配合不良。")
                prompt_label.pack(pady=10)
                button_frame = ctk.CTkFrame(frame,fg_color="transparent")
                button_frame.pack(pady=10)
                # "存在"按钮
                exist_button = ctk.CTkButton(
                    button_frame,
                    text="好的",
                    command=dialog.destroy  # 直接关闭对话框
                )
                exist_button.pack(pady=10,side="right", padx=5)

                pass
            # show_info_dialog("校准提示", prompt)

        def show_info_dialog(title, message):
            """自定义信息弹窗"""
            # 创建弹窗
            dialog = ctk.CTkToplevel()
            dialog.title(title)  # 设置标题
            dialog.geometry("400x200")  # 设置弹窗大小
            dialog.resizable(False, False)  # 禁止调整大小
            dialog.geometry(CenterWindowToDisplay(dialog, 400, 200, dialog._get_window_scaling()))
            # 弹窗内容
            label = ctk.CTkLabel(
                dialog,
                text=message,
                font=("SimHei", 14),
                wraplength=380  # 自动换行宽度
            )
            label.pack(pady=20, padx=20)

            # 关闭按钮
            button = ctk.CTkButton(
                dialog,
                text="确定",
                command=dialog.destroy  # 关闭弹窗
            )
            button.pack(pady=10)

            # 使弹窗模态（阻止用户操作主窗口）
            dialog.grab_set()

        def save_z_offset():
            #读取当前被选中的toml文件
            z_save_option_value = z_save_option.get()+".toml"
            documents_path = os.path.expanduser("~/Documents")  # 跨平台 Documents 路径
            mkpsupport_path = os.path.join(documents_path, "MKPSupport")
            z_save_option_value = os.path.join(mkpsupport_path, z_save_option_value)
            #读取配置文件
            read_toml_config(z_save_option_value)
            Temp_Obsolete_ZOffset=para.Z_Offset
            para.Z_Offset=para.Z_Offset + para.Temp_ZOffset_Calibr
            #写入配置文件
            write_toml_config(z_save_option_value)
            para.Temp_ZOffset_Calibr = 0  # 重置临时偏移值
            show_info_dialog("结果", f"喷嘴笔尖高度差校准结果已保存到 {z_save_option.get()}.toml\n\n原偏移值为: {Temp_Obsolete_ZOffset:.2f}mm\n\n新Z偏移值为: {para.Z_Offset:.2f}mm")
            ZSave.configure(state="disabled",fg_color="grey")  # 禁用保存按钮

        def save_xy_offset():
            # Read the currently selected TOML file
            xy_save_option_value = xy_save_option.get() + ".toml"
            documents_path = os.path.expanduser("~/Documents")  # Cross-platform Documents path
            mkpsupport_path = os.path.join(documents_path, "MKPSupport")
            xy_save_option_value = os.path.join(mkpsupport_path, xy_save_option_value)

            # Read the configuration file
            read_toml_config(xy_save_option_value)
            Temp_Obsolete_XOffset = para.X_Offset
            Temp_Obsolete_YOffset = para.Y_Offset
            # Update X and Y offsets with their temporary calibration values
            para.X_Offset = para.X_Offset + para.Temp_XOffset_Calibr
            para.Y_Offset = para.Y_Offset + para.Temp_YOffset_Calibr

            # Write the updated configuration back to the file
            write_toml_config(xy_save_option_value)

            # Reset temporary calibration values
            para.Temp_XOffset_Calibr = 0
            para.Temp_YOffset_Calibr = 0

            # Show confirmation message
            show_info_dialog(
                "结果",
                f"XY 轴偏移校准结果已保存到 {xy_save_option.get() + '.toml'}\n\n"
                f"原 X 偏移值为: {Temp_Obsolete_XOffset:.2f}mm, Y 偏移值为: {Temp_Obsolete_YOffset:.2f}mm\n\n"
                f"新 X 偏移值为: {para.X_Offset:.2f}mm, Y 偏移值为: {para.Y_Offset:.2f}mm"
            )

            # Disable the save button
            XYSave.configure(state="disabled", fg_color="grey")



    selected_toml = ctk.StringVar()
    
    def on_confirm():
        para.Preset_Name = selected_toml.get()
        copy_user_command()
        selection_dialog.destroy()
    
    def on_delete():
        selected_file = selected_toml.get()
        if selected_file:
            confirm =CTkMessagebox(title="确认删除", message=f"确定要删除预设: {os.path.basename(selected_file)}吗?",
                        icon="question", option_1="取消", option_2="确定",fade_in_duration=0.1,bg_color=("white","black"),fg_color=("#e1e6e9","#343638"),border_width=1,font=("SimHei",15),border_color=("#d1d1d1","#3a3a3a"))
            # 只有当用户点击"确定删除"时才执行删除
            if confirm.get() == "确定":
                os.remove(selected_file)
                refresh_preset_frame_list()  # 刷新列表

    
                


    
    def on_edit():
        selected_file = selected_toml.get()
        read_toml_config(selected_file)
        get_preset_values("Modify")
        write_toml_config(selected_file)
    
    def on_new():
        dialog = ctk.CTkInputDialog(title="新建预设", text="请输入新预设的名称:",font=("SimHei",15))
        new_preset_name = dialog.get_input()
        if new_preset_name:
            para.Preset_Name = new_preset_name
            mkpsupport_path = os.path.join(create_mkpsupport_dir(), f"{new_preset_name}.toml")
            get_preset_values("Normal")
            write_toml_config(mkpsupport_path)
            refresh_toml_list()
    
    refresh_toml_list()
    selection_dialog.mainloop()

#完全废弃的函数
def environment_check():
    pass

#这个函数用来删除interface末尾的WIPE，是从最末尾往前查的。它会查找最靠近结尾的;WIPE_START,记录其索引，然后删除从它到结尾的所有行
def delete_wipe(interface):
    Start_Index=0
    End_Index=0
    Follow_Flag=False
    #检查end_index是否在后部
    for i in range(len(interface)-1,-1,-1):
        if interface[i].find("; WIPE_END") != -1:
            End_Index=i
            break
        if i<len(interface)-15:
            break

    #检查这是否足够保险：从end_index开始往后查找，看看含有G1 X或者G1 Y且含有E的行（即挤出行）是否存在
    for i in range(End_Index,len(interface)):
        if (interface[i].find("G1 X") != -1 or interface[i].find("G1 Y") != -1) and interface[i].find("E") != -1:
            Follow_Flag=True
            
            # tk.messagebox.showwarning(title='警报', message="Gcode中有挤出行:"+interface[i])
            break

    if End_Index!=0 and Follow_Flag==False:
        for i in range(len(interface)-1,-1,-1):
            if interface[i].find("; WIPE_START") != -1:
                Start_Index=i
                break
        #切割interface，只保留start_index之前的行
        interface=interface[:Start_Index]
        #在末尾添加一个跳Z标记
        interface.append(";ZJUMP_START")
    else:
        #如果最后一行是一个既含有（G1 X或者G1 Y）又含有F,且不含有E的行，那么把它删去
        if (interface[-1].find("G1 X") != -1 or interface[-1].find("G1 Y") != -1 ) and interface[-1].find("F") != -1 and interface[-1].find("E") == -1:
            interface=interface[:-1]#这一行肯定是空驶，删掉
        #在末尾添加一个跳Z标记
        interface.append(";ZJUMP_START")

    #接下来查找interface中是否还有;WIPE_END，在每一个;WIPE_END之前都添加一个;ZJUMP_START
    for i in range(len(interface)-1,-1,-1):
        if interface[i].find("; WIPE_END") != -1:
            interface.insert(i+1,";ZJUMP_START")
            break
    return interface


def main():
    check_for_updates()
    Layer_Flag = False#不再使用了
    Copy_Flag = False#指示当前的gcode是否应当拷贝
    AMS_Flag = False#指示当前的gcode是否是AMS
    # FR_AMS_Flag = False#是否是第一个AMS
    KE_AMS_Flag = False#延迟关闭
    MachineType_Main = "MKP" 
    Read_MachineType_Flag = True
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
        os._exit(0)
        # exit("Manager Exit")
    # tk.messagebox.showinfo(title='警报', message="GSourceFile:"+GSourceFile)
    # tk.messagebox.showinfo(title='警报', message="TomlName:"+TomlName)
    read_toml_config(TomlName)
    environment_check()
    Layer_Height_Index = {}#存储接触面的数据，回头在第二次循环还需要用
    para.Ironing_Speed=para.Ironing_Speed*60#换算
    para.Max_Speed=para.Max_Speed*60
    with open(GSourceFile, 'r', encoding='utf-8') as file:
        content = file.readlines()

    #检查用户是否指示使用L803指令
    if para.Custom_Mount_Gcode.find("L803") != -1 and para.Custom_Mount_Gcode.find(";L803") == -1:
        #用户指定降温
        para.L803_Leak_Pervent_Flag = True

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
            # para.Typical_Layer_Speed = Num_Strip(CurrGCommand)[0]
            # para.Typical_Layer_Speed=para.Typical_Layer_Speed*0.6
            Diameter_Count+=1
        if CurrGCommand.find("; retraction_length = ") != -1:
            para.Retract_Length = Num_Strip(CurrGCommand)[0]
            Diameter_Count+=1
        if CurrGCommand.find("; nozzle_temperature = ") != -1:
            para.Nozzle_Switch_Tempature = Num_Strip(CurrGCommand)[0]
            Diameter_Count+=1
        if CurrGCommand.find("; nozzle_diameter = ") != -1:
            Temp_Nozzle_frisk = Num_Strip(CurrGCommand)[0]
            if Temp_Nozzle_frisk<=0.3 and Temp_Nozzle_frisk>=0.15:
                para.Minor_Nozzle_Diameter_Flag = True
        if Diameter_Count==9:
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
        
        #读取风扇速度
        if CurrGCommand.find("M106 S") != -1:
            para.Fan_Speed = Num_Strip(CurrGCommand)[1]
        if CurrGCommand.find("M106 P1 S") != -1:
            para.Fan_Speed = Num_Strip(CurrGCommand)[2]

        #延迟一条指令关闭AMS_Flag
        if KE_AMS_Flag==True:
            KE_AMS_Flag=False
            AMS_Flag=False

        #判断机型
        if Read_MachineType_Flag and CurrGCommand.find(";===== machine: A1") != -1 and CurrGCommand.find("mini") == -1:
            MachineType_Main = "A1"
            Read_MachineType_Flag=False
        if Read_MachineType_Flag and CurrGCommand.find(";===== machine: X1") != -1:
            MachineType_Main = "X1"
            Read_MachineType_Flag=False
        if Read_MachineType_Flag and CurrGCommand.find(";===== machine: A1 mini") != -1:
            MachineType_Main = "A1mini"
            Read_MachineType_Flag=False
        if Read_MachineType_Flag and CurrGCommand.find(";===== machine: P1") != -1:
            MachineType_Main = "P1"
            Read_MachineType_Flag=False

        if (MachineType_Main == "X1" or MachineType_Main == "P1") and CurrGCommand.find("M620 S")!=-1 and CurrGCommand.find("; switch material if AMS exist")==-1 and CurrGCommand.find("; change_filament_gcode")==-1:
            AMS_Flag=True
            print(";AMS Found.The AMS code will be ignored", file=TempExporter)
        if (MachineType_Main == "X1" or MachineType_Main == "P1") and CurrGCommand.find("M621 S") != -1 and AMS_Flag==True:
            # AMS_Flag=False
            KE_AMS_Flag=True
        if (MachineType_Main == "A1" or MachineType_Main == "A1mini") and CurrGCommand.find("M1007 S0") != -1 and CurrGCommand.find("; switch material if AMS exist")==-1 and CurrGCommand.find("; change_filament_gcode")==-1:
            AMS_Flag=True
            print(";AMS Found.The AMS code will be ignored", file=TempExporter)
        if (MachineType_Main == "A1" or MachineType_Main == "A1mini") and CurrGCommand.find("M1007 S1") != -1 and AMS_Flag==True:
            # AMS_Flag=False
            KE_AMS_Flag=True            

        if CurrGCommand.find("; FEATURE: Support interface") != -1:
            Copy_Flag=True
            Start_Index=i
            Last_XY_Command_FE_Flag=False
            # print(";LSTXY:"+last_xy_command_in_other_features)
            # print("start_index:",Start_Index)
        if Copy_Flag==True and CurrGCommand.find("; CHANGE_LAYER") != -1:
            #提前结算
            End_Index=i-1
            InterFace.extend(delete_wipe(content[Start_Index:End_Index]))
            Start_Index=i
            Temp_InterFace_Frisk = []
            Temp_InterFace_Frisk.extend(InterFace)
            if check_validity_interface_set(Temp_InterFace_Frisk) == True:
                Act_Flag=True
                Temp_InterFace_Frisk.clear()
            else:
                InterFace.clear()
        if CurrGCommand.find("; FEATURE:")!=-1 and CurrGCommand.find("; FEATURE: Support interface") == -1 and Copy_Flag:#这是另外一种挤出
            Copy_Flag=False
            End_Index=i-1
            for i in range(Start_Index, End_Index): 
                if content[i].find("M620 S") != -1:
                    End_Index=i-1
                    break
            InterFace.extend(delete_wipe(content[Start_Index:End_Index]))
            Temp_InterFace_Frisk = []
            Temp_InterFace_Frisk.extend(InterFace)
            if check_validity_interface_set(Temp_InterFace_Frisk) == True:
                Act_Flag=True
                Temp_InterFace_Frisk.clear()
            else:
                InterFace.clear()
        if CurrGCommand.find("; layer num/total_layer_count") != -1 and Act_Flag:
            Last_XY_Command_FE_Flag=True
            Act_Flag=False
            # print(len(InterFace))
            InterFaceIroning = []
            InterFaceGlueing = []
            InterFacePreGlueing = []#预涂胶部分
            InterFacePreGlueing.extend(InterFace)
            InterFaceIroning.extend(InterFace)
            InterFaceGlueing.extend(InterFace)
            
            # print("G92 E0",file=TempExporter)
            print(";Rising Nozzle a little", file=TempExporter)
            print("G1 Z" + str(round(Current_Layer_Height+0.4, 3)), file=TempExporter)#Avoid collision
            if para.L803_Leak_Pervent_Flag==True:
                print(";Pervent Leakage", file=TempExporter)
                print("M104 S140", file=TempExporter)
            print(";Move to Waiting_point", file=TempExporter)
            if MachineType_Main == "X1" or MachineType_Main == "P1":
                print("G1 X30 Y212 F" + str(para.Travel_Speed*60), file=TempExporter) #Move to Waiting Point
            elif MachineType_Main == "A1":
                print("G1 X252 F" + str(para.Travel_Speed*60), file=TempExporter)#Move to Waiting Point
            elif MachineType_Main == "A1mini":
                print("G1 X160 F" + str(para.Travel_Speed*60), file=TempExporter)#Move to Waiting Point
            print(";Mounting Toolhead", file=TempExporter)
            # print(para.Custom_Mount_Gcode.strip("\n"), file=TempExporter)
            #把para.Custom_Mount_Gcode.strip("\n")按行写入
            for line in para.Custom_Mount_Gcode.strip("\n").split("\n"):
                if line.strip().find("L801")==-1:
                    print(line.strip(), file=TempExporter)
                else:
                    print("G1 Z"+str(round(Current_Layer_Height+para.Z_Offset+3, 3))+";L801", file=TempExporter)#Avoid collision
            print(";Toolhead Mounted", file=TempExporter)
            print(";Glueing Started", file=TempExporter)
            print(";Inposition", file=TempExporter)
            print("G1 F" + str(para.Travel_Speed*60), file=TempExporter) 
            print(Process_GCode_Offset(last_xy_command_in_other_features, para.X_Offset, para.Y_Offset, para.Z_Offset+3,'normal').strip("\n"), file=TempExporter)#Inposition
            print("G1 Z" + str(round(Last_Layer_Height+para.Z_Offset, 3)), file=TempExporter)#Adjust
            print("G1 F"+str(para.Max_Speed),file=TempExporter)
            First_XY_Command_IN_Flag=True
            if para.Minor_Nozzle_Diameter_Flag==True:
                #隔一个删除一个以G1 X或者G1 Y开头的行
                for i in range(len(InterFaceGlueing)-1, -1, -1):
                    if InterFaceGlueing[i].find("G1 X") != -1 or InterFaceIroning[i].find("G1 Y") != -1:
                        if i%2==0:
                            InterFaceGlueing.pop(i)
            for i in range(len(InterFaceGlueing)):
                # print("G4 P100", file=TempExporter)
                if InterFaceGlueing[i].find("G1 ") != -1 and InterFaceGlueing[i].find("G1 E") == -1 and InterFaceGlueing[i].find("G1 F") == -1:
                    if InterFaceGlueing[i].find("G1 X") != -1 or InterFaceGlueing[i].find("G1 Y") != -1:
                        Physical_Glueing_Point=Process_GCode_Offset(InterFaceGlueing[i], 0, 0, para.Z_Offset+3,'normal')
                        if First_XY_Command_IN_Flag==True:
                            first_xy_command_in_interface=Physical_Glueing_Point
                            # print(";First XY Command:"+first_xy_command_in_interface)
                            First_XY_Command_IN_Flag=False
                    InterFaceGlueing[i]=Process_GCode_Offset(InterFaceGlueing[i], para.X_Offset, para.Y_Offset, para.Z_Offset,'normal')
                    print(InterFaceGlueing[i].strip("\n"),file=TempExporter)
                elif InterFaceGlueing[i].find(";ZJUMP_START") != -1:
                    #从i开始，检查往后的i+1，i+2，i+3行等等谁含有G1 X 或者G1 Y,记录这一个数值
                    NextStartIndex=i+1
                    if i+1<len(InterFaceGlueing):
                        for j in range(i+1, len(InterFaceGlueing)):
                            if InterFaceGlueing[j].find("G1 X") != -1 or InterFaceGlueing[j].find("G1 Y") != -1:
                                NextStartIndex=j
                                break
                        print("G1 Z" + str(round(Current_Layer_Height+para.Z_Offset+3, 3)), file=TempExporter)#Avoid spoiling
                        TempJumpZ=Process_GCode_Offset(InterFaceGlueing[NextStartIndex], para.X_Offset, para.Y_Offset , para.Z_Offset+3,'normal')
                        print(TempJumpZ.strip("\n"),file=TempExporter)
                        print("G1 Z"+ str(round(Last_Layer_Height+para.Z_Offset, 3)), file=TempExporter)#Adjust

            print(";Glueing Finished", file=TempExporter)
            print("G1 Z" + str(round(Current_Layer_Height+para.Z_Offset+3, 3)), file=TempExporter)#Avoid collision
            print(";Unmounting Toolhead", file=TempExporter)
            #同上处理，strip\n后按行写入，检l801
            for line in para.Custom_Unmount_Gcode.strip("\n").split("\n"):
                if line.strip().find("M106 S[AUTO]") != -1:
                    print("M106 S" + str(para.Fan_Speed), file=TempExporter)
                elif line.strip().find("M106 P1 S[AUTO]") != -1:
                    print("M106 P1 S" + str(para.Fan_Speed), file=TempExporter)
                elif line.strip().find("L802")==-1:
                    print(line.strip(), file=TempExporter)
                else:
                    print("G1 F" + str(para.Travel_Speed*60), file=TempExporter) #Move to Wiping Point
                    #TowerGCTemp = Process_GCode_Offset(para.Wiping_Gcode[j], para.Wiper_x-5, para.Wiper_y-5, 0,'tower')
                    TowerGCMove=Process_GCode_Offset("G1 X20 Y10.19", para.Wiper_x-5, para.Wiper_y-5, 0,'tower')
                    print(TowerGCMove+ " ;L802", file=TempExporter)#Avoid collision
                    print("G1 Z"+str(round(Current_Layer_Height+0.4, 3))+";L802", file=TempExporter)#Avoid collision
                    if para.L803_Leak_Pervent_Flag==True:
                        print("M109 S" + str(para.Nozzle_Switch_Tempature), file=TempExporter)
            print(";Toolhead Unmounted", file=TempExporter)
            # print(";Move to the next print start position", file=TempExporter)
            print("G1 F" + str(para.Travel_Speed*60), file=TempExporter) 
            # print(Physical_Glueing_Point,file=TempExporter)
            # print(";Lowering Nozzle", file=TempExporter)
            # print("G1 Z" + str(round(Last_Layer_Height, 3)), file=TempExporter)
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
        
        if AMS_Flag==True:
            pass
        else :
            print(CurrGCommand, file=TempExporter)

    TempExporter.close()

    #输出的预涂胶代码
    Trigger_Flag=False
    Tower_Flag=True
    FirstLayer_Tower_Height=0
    First_layer_Tower_Flag=True
    First_layer_Flag=True
    Last_Layer_Height=0
    try:
        Last_Key=max(Layer_Height_Index.keys())
    except:
        Last_Key=0
    # print("Last Key:",Last_Key)
    Output_Filename = GSourceFile + "_Output.gcode"
    with open(Output_Filename+'.te', 'r', encoding='utf-8') as file:
        content = file.readlines()
    GcodeExporter = open(Output_Filename, "w", encoding="utf-8")
    CutNozzle_Wrap_Detect=False
    Pen_Wipe_Flag=True
    for i in range(len(content)):
        LastGCommand = CurrGCommand
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
            # print("G1 Z" + str(round(para.First_Layer_Height, 3) )+ ";TowerBase Z", file=GcodeExporter)#Adjust z height
            para.Tower_Extrude_Ratio = round(para.First_Layer_Height/ 0.2, 3)
            print("G1 F" + str(para.Travel_Speed*60), file=GcodeExporter) 
            for j in range(len(para.Tower_Base_Layer_Gcode)):
                if para.Tower_Base_Layer_Gcode[j].find("EXTRUDER_REFILL")!=-1:
                    print("G92 E0",file=GcodeExporter)
                    print("G1 E"+str(para.Retract_Length),file=GcodeExporter)
                    print("G92 E0",file=GcodeExporter)
                elif para.Tower_Base_Layer_Gcode[j].find("NOZZLE_HEIGHT_ADJUST") != -1:
                    print("G1 Z" + str(round(para.First_Layer_Height, 3) )+";Tower Z", file=GcodeExporter)
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

        
        #输出后续塔代码
        if CurrGCommand.find("; update layer progress") != -1 and para.Have_Wiping_Components.get()==True and Tower_Flag==True and First_layer_Tower_Flag==False:
            Tower_Flag=False
            print("G1 F" + str(para.Travel_Speed*60), file=GcodeExporter)
            # print("G1 Z"+ str(round(Current_Layer_Height, 3))+";Tower Z", file=GcodeExporter)
            para.Tower_Extrude_Ratio=round((Current_Layer_Height-Last_Layer_Height) / 0.2,3)
            if para.Tower_Extrude_Ratio<0 or para.Tower_Extrude_Ratio==0:
                para.Tower_Extrude_Ratio=round(para.Typical_Layer_Height / 0.2, 3)
            for j in range(len(para.Wiping_Gcode)):
                # if para.Wiping_Gcode[j].find("G1 ") != -1 and para.Wiping_Gcode[j].find("G1 E") == -1 and para.Wiping_Gcode[j].find("G1 F") == -1:
                if para.Wiping_Gcode[j].find("G1 F9600") != -1:#替换为用户自己切片的外墙速度
                    print("G1 F" + str(para.Typical_Layer_Speed*60), file=GcodeExporter)
                elif para.Wiping_Gcode[j].find("TOWER_ZP_ST") != -1:
                    print(";JL begin", file=GcodeExporter)
                    print("G1 Z"+ str(round(Current_Layer_Height+0.5, 3)), file=GcodeExporter)
                elif para.Wiping_Gcode[j].find("NOZZLE_HEIGHT_ADJUST") != -1:
                    print("G1 Z"+ str(round(Current_Layer_Height, 3))+";Tower Z", file=GcodeExporter)
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
        if LastGCommand.find("; Z_HEIGHT:")!= -1 and para.Have_Wiping_Components.get()==True and Pen_Wipe_Flag==True and Num_Strip(LastGCommand)[0]>para.First_Layer_Height :
            #输出首层的笔芯擦拭
            Pen_Wipe_Flag=False
            Pen_Wipe="""
            G1 F9600
            G1 X31.254 Y8.746
            G1 X31.254 Y31.254
            G1 X8.746 Y31.254
            G1 X8.746 Y8.746 
            G1 X8.369 Y8.369 F30000
            G1 F9600
            G1 X8.369 Y31.631 
            G1 X31.631 Y31.631
            G1 X31.631 Y8.369 
            G1 X8.369 Y8.369 
            G1 X7.992 Y7.992 F30000
            G1 F9600
            G1 X32.008 Y7.992 
            G1 X32.008 Y32.008 
            G1 X7.992 Y32.008 
            G1 X7.992 Y7.992 
            G1 X7.615 Y7.615 F30000
            G1 F9600
            G1 X31.254 Y8.746
            G1 X31.254 Y31.254
            G1 X8.746 Y31.254
            G1 X8.746 Y8.746 
            G1 X8.369 Y8.369 F30000
            G1 F9600
            G1 X8.369 Y31.631 
            G1 X31.631 Y31.631
            G1 X31.631 Y8.369 
            G1 X8.369 Y8.369 
            G1 X7.992 Y7.992 F30000
            G1 F9600
            G1 X32.008 Y7.992 
            G1 X32.008 Y32.008 
            G1 X7.992 Y32.008 
            G1 X7.992 Y7.992 
            G1 X7.615 Y7.615 F30000
            """
            #挂胶箱
            # print("; CHANGE_LAYER", file=GcodeExporter)
            print(";Rising Nozzle a little", file=GcodeExporter)
            print("G1 Z" + str(round(para.First_Layer_Height+0.4, 3)), file=GcodeExporter)#Avoid collision
            if para.L803_Leak_Pervent_Flag==True:
                print(";Pervent Leakage", file=GcodeExporter)
                print("M104 S140", file=GcodeExporter)
            print(";Move to Waiting_point", file=GcodeExporter)
            if MachineType_Main == "X1" or MachineType_Main == "P1":
                print("G1 X30 Y212 F" + str(para.Travel_Speed*60), file=GcodeExporter) #Move to Waiting Point
            elif MachineType_Main == "A1":
                print("G1 X252 F" + str(para.Travel_Speed*60), file=GcodeExporter)#Move to Waiting Point
            elif MachineType_Main == "A1mini":
                print("G1 X160 F" + str(para.Travel_Speed*60), file=GcodeExporter)#Move to Waiting Point
            print(";Mounting Toolhead", file=GcodeExporter)
            # print(para.Custom_Mount_Gcode.strip("\n"), file=GcodeExporter)
            #把para.Custom_Mount_Gcode.strip("\n")按行写入
            for line in para.Custom_Mount_Gcode.strip("\n").split("\n"):
                if line.strip().find("L801")==-1:
                    print(line.strip(), file=GcodeExporter)
                else:
                    print("G1 Z"+str(round(para.First_Layer_Height+para.Z_Offset+3, 3))+";L801", file=GcodeExporter)#Avoid collision
            print(";Toolhead Mounted", file=GcodeExporter)
            print(";Glueing Started", file=GcodeExporter)
            print(";Inposition", file=GcodeExporter)
            print("G1 F" + str(para.Travel_Speed*60), file=GcodeExporter) 
            #去擦料塔附近
            print(Process_GCode_Offset("G1 X31.254 Y8.746", para.X_Offset+ para.Wiper_x-5, para.Y_Offset+ para.Wiper_y-5, para.Z_Offset+3,'normal').strip("\n"), file=GcodeExporter)#Inposition
            print("G1 Z" + str(round(para.First_Layer_Height+para.Z_Offset, 3)), file=GcodeExporter)#Adjust
            print("G1 F"+str(para.Max_Speed),file=GcodeExporter)
            #输出笔芯擦拭代码
            for j in range(len(Pen_Wipe.strip("\n").split("\n"))):
                if Pen_Wipe.strip("\n").split("\n")[j].find("G1 ") != -1 and Pen_Wipe.strip("\n").split("\n")[j].find("G1 F") == -1:
                    TowerGCTemp = Process_GCode_Offset(Pen_Wipe.strip("\n").split("\n")[j], para.X_Offset+para.Wiper_x-5, para.Y_Offset+para.Wiper_y-5, 0,'normal')
                    print(TowerGCTemp.strip("\n"), file=GcodeExporter)
                elif Pen_Wipe.strip("\n").split("\n")[j].find("G1 F9600") != -1:
                    print("G1 F" + str(min(para.Max_Speed*0.5,40*60)), file=GcodeExporter)
                else:
                    print(Pen_Wipe.strip("\n").split("\n")[j], file=GcodeExporter)
            print("G1 Z" + str(round(para.First_Layer_Height+para.Z_Offset+2, 3)), file=GcodeExporter)#Avoid collision
            print(";Unmounting Toolhead", file=GcodeExporter)
            #同上处理，strip\n后按行写入，检l801
            for line in para.Custom_Unmount_Gcode.strip("\n").split("\n"):
                if line.strip().find("M106 S[AUTO]") != -1:
                    print("M106 S" + str(para.Fan_Speed), file=GcodeExporter)
                elif line.strip().find("M106 P1 S[AUTO]") != -1:
                    print("M106 P1 S" + str(para.Fan_Speed), file=GcodeExporter)
                elif line.strip().find("L802")==-1 and line.strip().find("G4")==-1:
                    print(line.strip(), file=GcodeExporter)
                elif line.strip().find("L802")!=-1:
                    #TowerGCTemp = Process_GCode_Offset(para.Wiping_Gcode[j], para.Wiper_x-5, para.Wiper_y-5, 0,'tower')
                    TowerGCMove=Process_GCode_Offset("G1 X20 Y10.19", para.Wiper_x-5, para.Wiper_y-5, 0,'tower')
                    print(TowerGCMove+ " ;L802", file=GcodeExporter)#Avoid collision
                    print("G1 Z"+str(round(para.First_Layer_Height+0.4, 3))+";L802", file=GcodeExporter)#Avoid collision
                    if para.L803_Leak_Pervent_Flag==True:
                        print("M109 S" + str(para.Nozzle_Switch_Tempature), file=GcodeExporter)
            print(";Toolhead Unmounted", file=GcodeExporter)
            # print(";Move to the next print start position", file=GcodeExporter)
            # print("G1 F" + str(para.Travel_Speed*30), file=GcodeExporter) 
            #做完之后稍微挤出一点到外圈
            Extra_Wipe = """
            G1 X33.14 Y6.86
            G1 F9600
            G1 X33.14 Y6.86 E.95507
            G1 X33.14 Y33.14 E.95507
            G1 X6.86 Y33.14 E.95507
            G1 X6.86 Y6.86 E.95507
            G1 X6.86 Y5.9
            EXTRUDER_RETRACT
            """
            #继续输出塔代码（Extra_Wipe）
            para.Tower_Extrude_Ratio = round(para.First_Layer_Height/ 0.2, 3)
            print("G1 F" + str(para.Travel_Speed*30), file=GcodeExporter) 
            print(Process_GCode_Offset("G1 X33.14 Y6.86", para.Wiper_x-5, para.Wiper_y-5, 0,'tower').strip("\n"), file=GcodeExporter) #Inposition
            print("G1 Z" + str(round(para.First_Layer_Height, 3)), file=GcodeExporter) #Avoid collision
            for j in range(len(Extra_Wipe.strip("\n").split("\n"))):
                if Extra_Wipe.strip("\n").split("\n")[j].find("EXTRUDER_RETRACT") != -1:
                    print("G92 E0", file=GcodeExporter)
                    print("G1 E-"+str(para.Retract_Length), file=GcodeExporter)
                    print("G92 E0", file=GcodeExporter)
                elif Extra_Wipe.strip("\n").split("\n")[j].find("G1 ") != -1 and Extra_Wipe.strip("\n").split("\n")[j].find("G1 E") == -1 and Extra_Wipe.strip("\n").split("\n")[j].find("G1 F") == -1:
                    TowerGCTemp = Process_GCode_Offset(Extra_Wipe.strip("\n").split("\n")[j], para.Wiper_x-5, para.Wiper_y-5, 0,'tower')
                    print(TowerGCTemp.strip("\n"), file=GcodeExporter)
                elif Extra_Wipe.strip("\n").split("\n")[j].find("G1 F9600") != -1:
                    print("G1 F" + str(para.First_Layer_Speed*60), file=GcodeExporter)
            print("G1 F" + str(para.Travel_Speed*30), file=GcodeExporter)

    GcodeExporter.close()

    #输出偏移校准测试
    #倒序查找;Precise Calibration或者;Rough Calibration或者;ZOffset Calibration
    Mode=""
    def show_info_dialog(title, message):
        """自定义信息弹窗"""
        # 创建弹窗
        dialog = ctk.CTkToplevel()
        dialog.title(title)  # 设置标题
        dialog.geometry("400x200")  # 设置弹窗大小
        dialog.resizable(False, False)  # 禁止调整大小
        dialog.geometry(CenterWindowToDisplay(dialog, 400, 200, dialog._get_window_scaling()))
        # 弹窗内容
        label = ctk.CTkLabel(
            dialog,
            text=message,
            font=("SimHei", 14),
            wraplength=380  # 自动换行宽度
        )
        label.pack(pady=20, padx=20)

        # 关闭按钮
        button = ctk.CTkButton(
            dialog,
            text="确定",
            command=dialog.destroy  # 关闭弹窗
        )
        button.pack(pady=10)
        # 使弹窗模态（阻止用户操作主窗口）
        dialog.grab_set()
    for i in range(len(content)):
        if content[i].find("Precise Calibration") != -1:
            Mode="Precise"
            break
        if content[i].find("Rough Calibration") != -1:
            Mode="Rough"
            break
        if content[i].find("ZOffset Calibration") != -1:
            Mode="ZOffset"
            break
        if content[i].find("LShape Repetition") != -1:
            Mode="Repetition"
            break
    if Mode=="Rough" or Mode=="Precise" :
        # show_info_dialog(
        #     title="提示",
        #     message="正在输出XY偏移校准测试"+"\n"+"测试过程中如需中止请取消打印，请勿暂停"
        # )
        tk.messagebox.showinfo(title='提示', message="正在输出XY偏移校准测试"+"\n\n"+"测试过程中如需中止请取消打印，请勿暂停")
        with open(GSourceFile, 'r', encoding='utf-8') as file:
            calibe = file.readlines()
        # os.remove(Output_Filename)
        CaliGcodeExporter = open(Output_Filename, "w", encoding="utf-8")
        MachineType = ""
        for i in range(len(calibe)):
            if calibe[i].find(";===== machine: A1 =======") != -1:
                MachineType = "A1"
                break
            if calibe[i].find(";===== machine: X1 ====") != -1:
                MachineType = "X1"
                break
            if calibe[i].find(";===== machine: P1") != -1:
                MachineType = "P1/P1S"
                break
            if calibe[i].find(";===== machine: A1 mini ============") != -1:
                MachineType = "A1mini"
                break
        #输出文件
        for i in range(len(calibe)):
            print(calibe[i].strip("\n"), file=CaliGcodeExporter)
            if calibe[i].find("; filament end gcode") != -1 and calibe[i].find("=") == -1 and Mode!="ZOffset":
                #输出偏移校准
                #挂载胶箱
                print("G1 X100 Y100 Z10 F3000", file=CaliGcodeExporter)
                print(";Rising nozzle to avoid collision", file=CaliGcodeExporter)
                print("G1 Z" + str(round(para.First_Layer_Height+para.Z_Offset+3, 3)), file=CaliGcodeExporter)
                print(";Mounting Toolhead", file=CaliGcodeExporter)
                print(para.Custom_Mount_Gcode.strip("\n"), file=CaliGcodeExporter)
                print(";Toolhead Mounted", file=CaliGcodeExporter)

                if MachineType=="A1mini" or MachineType=="A1":
                    print(Calibe_Sing, file=CaliGcodeExporter)#唱歌

                #横线部分：
                if MachineType=="X1" or MachineType=="P1/P1S":
                    Y_Cali_Line_DefaultX=104.530
                    Y_Cali_Line_DefaultX_End=114.530
                    Y_Cali_Line_DefaultY=112.830
                elif MachineType!="A1mini":
                    Y_Cali_Line_DefaultX=104.530
                    Y_Cali_Line_DefaultX_End=114.530
                    Y_Cali_Line_DefaultY=114.830
                else:
                    Y_Cali_Line_DefaultX=66.523
                    Y_Cali_Line_DefaultX_End=76.523
                    Y_Cali_Line_DefaultY=76.830

                #空驶累加计数器
                Offset_Accumulate=0
                #偏移指定器
                Cali_Accumulate=0
                if Mode=="Precise":
                    Cali_Accumulate=-1.0
                elif Mode=="Rough":
                    Cali_Accumulate=-2.5
               
                
                #Y校准运行次数
                Y_Line=11

                #运行十次：
                for i in range(Y_Line):
                    #空驶到指定位置的调速F
                    print("G1 F" + str(para.Travel_Speed*60), file=CaliGcodeExporter)
                    #G1 X到指定位,Y渐增
                    OriginCaliLine="G1 X" + str(round(Y_Cali_Line_DefaultX, 3)) + " Y" + str(round(Y_Cali_Line_DefaultY+Offset_Accumulate, 3))#指定原值
                    print(Process_GCode_Offset(OriginCaliLine, para.X_Offset, para.Y_Offset+Cali_Accumulate,para.Z_Offset,'normal').strip("\n"), file=CaliGcodeExporter)#进行偏移
                    print("G1 Z" + str(round(para.First_Layer_Height+para.Z_Offset, 3)), file=CaliGcodeExporter)#Adjust Z
                    #开始校准的调速F
                    if para.Max_Speed>10:
                        print("G1 F300", file=CaliGcodeExporter)
                    else:
                        print("G1 F" + str(para.Max_Speed*60), file=CaliGcodeExporter)
                    #G1 X渐增
                    OriginCaliLine="G1 X" + str(round(Y_Cali_Line_DefaultX_End, 3)) + " Y" + str(round(Y_Cali_Line_DefaultY+Offset_Accumulate, 3))
                    print(Process_GCode_Offset(OriginCaliLine, para.X_Offset, para.Y_Offset+Cali_Accumulate,para.Z_Offset,'normal').strip("\n"), file=CaliGcodeExporter)#进行偏移
                    Offset_Accumulate+=4
                    if Mode=="Precise":
                        Cali_Accumulate+=0.2
                    elif Mode=="Rough":
                        Cali_Accumulate+=0.5
                    #抬升Z
                    print("G1 Z" + str(round(para.First_Layer_Height+para.Z_Offset+3, 3)), file=CaliGcodeExporter)

                #纵线部分：
                if MachineType!="A1mini":
                    X_Cali_Line_DefaultY=104.830
                    X_Cali_Line_DefaultY_End=114.830
                    X_Cali_Line_DefaultX=114.523
                else:
                    X_Cali_Line_DefaultY=66.830
                    X_Cali_Line_DefaultY_End=76.830
                    X_Cali_Line_DefaultX=76.523

                #空驶累加计数器
                Offset_Accumulate=0
                #偏移指定器
                Cali_Accumulate=0
                if Mode=="Precise":
                    Cali_Accumulate=-1.0
                elif Mode=="Rough":
                    Cali_Accumulate=-2.5
                #运行十次：
                for i in range(11):
                    #空驶到指定位置的调速F
                    print("G1 F" + str(para.Travel_Speed*60), file=CaliGcodeExporter)
                    #空驶到指定位置
                    #G1 Y到指定位,X渐增
                    OriginCaliLine="G1 X" + str(round(X_Cali_Line_DefaultX+Offset_Accumulate, 3)) + " Y" + str(round(X_Cali_Line_DefaultY, 3))#指定原值
                    print(Process_GCode_Offset(OriginCaliLine, para.X_Offset+Cali_Accumulate, para.Y_Offset,para.Z_Offset,'normal').strip("\n"), file=CaliGcodeExporter)#进行偏移
                    print("G1 Z" + str(round(para.First_Layer_Height+para.Z_Offset, 3)), file=CaliGcodeExporter)#Adjust Z
                    #开始校准的调速F
                    if para.Max_Speed>10:
                        print("G1 F300", file=CaliGcodeExporter)
                    else:
                        print("G1 F" + str(para.Max_Speed*60), file=CaliGcodeExporter)
                    #G1 X渐增
                    OriginCaliLine="G1 X" + str(round(X_Cali_Line_DefaultX+Offset_Accumulate, 3)) + " Y" + str(round(X_Cali_Line_DefaultY_End, 3))
                    print(Process_GCode_Offset(OriginCaliLine, para.X_Offset+Cali_Accumulate, para.Y_Offset,para.Z_Offset,'normal').strip("\n"), file=CaliGcodeExporter)#进行偏移
                    Offset_Accumulate+=4
                    if Mode=="Precise":
                        Cali_Accumulate+=0.2
                    elif Mode=="Rough":
                        Cali_Accumulate+=0.5
                    #抬升Z 
                    print("G1 Z" + str(round(para.First_Layer_Height+para.Z_Offset+3, 3)), file=CaliGcodeExporter)

                #卸载胶箱
                print(";Unmounting Toolhead", file=CaliGcodeExporter)
                print(para.Custom_Unmount_Gcode.strip("\n"), file=CaliGcodeExporter)
                print(";Toolhead Unmounted", file=CaliGcodeExporter)

                print("G1 X100 Y100 Z100", file=CaliGcodeExporter)#空驶

                if MachineType=="A1mini" or MachineType=="A1":
                    print(Calibe_Sing, file=CaliGcodeExporter)#唱歌

                #补全结束
                print(calibe[i].strip("\n"), file=CaliGcodeExporter)
        CaliGcodeExporter.close()
    elif Mode=="ZOffset":
        # show_info_dialog(
        #     title="提示",
        #     message="正在输出Z偏移校准测试"+"\n"+"测试过程中如需中止请取消打印，请勿暂停"
        # )
        tk.messagebox.showinfo(title='提示', message="正在输出Z偏移校准测试"+"\n\n"+"测试过程中如需中止请取消打印，请勿暂停")
        with open(GSourceFile, 'r', encoding='utf-8') as file:
            calibe = file.readlines()
        # os.remove(Output_Filename)
        CaliGcodeExporter = open(Output_Filename, "w", encoding="utf-8")
        MachineType = ""
        for i in range(len(calibe)):
            if calibe[i].find(";===== machine: A1 =======") != -1:
                MachineType = "A1"
                break
            if calibe[i].find(";===== machine: X1 ====") != -1:
                MachineType = "X1"
                break
            if calibe[i].find(";===== machine: P1") != -1:
                MachineType = "P1/P1S"
                break
            if calibe[i].find(";===== machine: A1 mini ============") != -1:
                MachineType = "A1mini"
                break
        #输出文件
        for i in range(len(calibe)):
            print(calibe[i].strip("\n"), file=CaliGcodeExporter)
            if calibe[i].find("; filament end gcode") != -1 and calibe[i].find("=") == -1:
                #输出偏移校准
                #挂载胶箱
                print("G1 X100 Y100 Z10 F3000", file=CaliGcodeExporter)
                print(";Rising nozzle to avoid collision", file=CaliGcodeExporter)
                print("G1 Z" + str(round(para.First_Layer_Height+para.Z_Offset+3, 3)), file=CaliGcodeExporter)
                print(";Mounting Toolhead", file=CaliGcodeExporter)
                print(para.Custom_Mount_Gcode.strip("\n"), file=CaliGcodeExporter)
                print(";Toolhead Mounted", file=CaliGcodeExporter)

                if MachineType=="A1mini" or MachineType=="A1":
                    print(Calibe_Sing, file=CaliGcodeExporter)#唱歌

                #横线部分：
                if MachineType!="A1mini":
                    FR_Calibe_X_Start=68.210
                    FR_Calibe_Y_Start=126.373
                else:
                    FR_Calibe_X_Start=30.210
                    FR_Calibe_Y_Start=88.373

                #空驶累加计数器
                Offset_Accumulate=0
                #Z变换计数器
                if Mode=="ZMicro":
                    Z_Accumulate=0.25
                elif Mode=="ZOffset":
                    Z_Accumulate=0.5

                #运行十次：
                for i in range(11):
                    #空驶到指定位置的调速F
                    print("G1 F" + str(para.Travel_Speed*60), file=CaliGcodeExporter)
                    #移动到每一个的开始点：x+11,Y不变
                    OriginCaliLine="G1 X" + str(round(FR_Calibe_X_Start+Offset_Accumulate, 3)) + " Y" + str(round(FR_Calibe_Y_Start, 3))
                    #开始校准的调速F
                    print("G1 F" + str(para.Max_Speed*60), file=CaliGcodeExporter)
                    print("G1 Z" + str(round(0.4+para.Z_Offset+Z_Accumulate, 3)), file=CaliGcodeExporter)#Adjust Z to cer
                    #做一个列表，把ZOffset_Sing按行化成列表
                    ZOffset_Sing_SP=ZOffset_Sing.split("\n")
                    for j in range(len(ZOffset_Sing_SP)):
                        print(Process_GCode_Offset(ZOffset_Sing_SP[j], para.X_Offset+Offset_Accumulate+FR_Calibe_X_Start, para.Y_Offset+FR_Calibe_Y_Start,0,'normal').strip("\n"), file=CaliGcodeExporter)#进行偏移
                    if Mode=="ZMicro":
                        Z_Accumulate-=0.05
                    elif Mode=="ZOffset":
                        Z_Accumulate-=0.1
                    Offset_Accumulate+=11
                    print("G1 Z" + str(round(para.Z_Offset+30, 3)), file=CaliGcodeExporter)                    #抬升Z
                    print("G4 P10000", file=CaliGcodeExporter)
                
                #卸载胶箱
                print(";Unmounting Toolhead", file=CaliGcodeExporter)
                print(para.Custom_Unmount_Gcode.strip("\n"), file=CaliGcodeExporter)
                print(";Toolhead Unmounted", file=CaliGcodeExporter)

                print("G1 X100 Y100 Z100", file=CaliGcodeExporter)#空驶

                if MachineType=="A1mini" or MachineType=="A1":
                    print(Calibe_Sing, file=CaliGcodeExporter)#唱歌

                #补全结束
                print(calibe[i].strip("\n"), file=CaliGcodeExporter)
        CaliGcodeExporter.close()
    elif Mode=="Repetition":
        tk.messagebox.showinfo(title='提示', message="正在输出精密度测试"+"\n\n"+"测试过程中如需中止请取消打印，请勿暂停")
        with open(GSourceFile, 'r', encoding='utf-8') as file:
            calibe = file.readlines()
        # os.remove(Output_Filename)
        CaliGcodeExporter = open(Output_Filename, "w", encoding="utf-8")
        MachineType = ""
        for i in range(len(calibe)):
            if calibe[i].find(";===== machine: A1 =======") != -1:
                MachineType = "A1"
                break
            if calibe[i].find(";===== machine: X1 ====") != -1:
                MachineType = "X1"
                break
            if calibe[i].find(";===== machine: P1") != -1:
                MachineType = "P1/P1S"
                break
            if calibe[i].find(";===== machine: A1 mini ============") != -1:
                MachineType = "A1mini"
                break
        #输出文件
        if MachineType=="A1mini":
            #逐行读取resource文件夹下的A1miniL.gcode到变量LShape_Code
            LShape_Code = []
            mkpexecutable_dir = os.path.dirname(sys.executable)
            mkpinternal_dir = os.path.join(mkpexecutable_dir, "resources")
            with open(os.path.join(mkpinternal_dir, "A1miniL.gcode"), 'r', encoding='utf-8') as file:
                LShape_Code = file.readlines()
        else:
            #逐行读取resource文件夹下的A1X1P1L.gcode到变量LShape_Code
            LShape_Code = []
            mkpexecutable_dir = os.path.dirname(sys.executable)
            mkpinternal_dir = os.path.join(mkpexecutable_dir, "resources")
            with open(os.path.join(mkpinternal_dir, "A1X1P1L.gcode"), 'r', encoding='utf-8') as file:
                LShape_Code = file.readlines()
        for i in range(len(calibe)):
            print(calibe[i].strip("\n"), file=CaliGcodeExporter)
            if calibe[i].find("; filament end gcode") != -1 and calibe[i].find("=") == -1:
                #输出偏移校准
                #挂载胶箱
                print("G1 X100 Y100 Z10 F3000", file=CaliGcodeExporter)
                print(";Rising nozzle to avoid collision", file=CaliGcodeExporter)
                print("G1 Z" + str(round(para.First_Layer_Height+para.Z_Offset+3, 3)), file=CaliGcodeExporter)
                print(";Mounting Toolhead", file=CaliGcodeExporter)
                print(para.Custom_Mount_Gcode.strip("\n"), file=CaliGcodeExporter)
                print(";Toolhead Mounted", file=CaliGcodeExporter)
                print("G1 Z"+ str(round(para.First_Layer_Height+para.Z_Offset, 3)), file=CaliGcodeExporter)#Adjust Z
                if MachineType=="A1mini" or MachineType=="A1":
                    print(Calibe_Sing, file=CaliGcodeExporter)#唱歌

                #将LShape_Code中的每一行做偏移后输出
                print(";LShape Repetition Calibration", file=CaliGcodeExporter)
                print("G1 F" + str(para.Max_Speed*60), file=CaliGcodeExporter)
                for j in range(len(LShape_Code)):
                    if LShape_Code[j].find("G1 ") != -1 and LShape_Code[j].find("G1 E") == -1 and LShape_Code[j].find("G1 F") == -1:
                        # print(LShape_Code[j])
                        if MachineType=="A1mini" or MachineType=="A1":
                            LShape_Code[j]=Process_GCode_Offset(LShape_Code[j], para.X_Offset, para.Y_Offset, para.Z_Offset,'normal')
                        else:
                            LShape_Code[j]=Process_GCode_Offset(LShape_Code[j], para.X_Offset, para.Y_Offset-2, para.Z_Offset,'normal')
                        print(LShape_Code[j].strip("\n"), file=CaliGcodeExporter)
                #卸载胶箱
                print(";Unmounting Toolhead", file=CaliGcodeExporter)
                print(para.Custom_Unmount_Gcode.strip("\n"), file=CaliGcodeExporter)
                print(";Toolhead Unmounted", file=CaliGcodeExporter)

                print("G1 X100 Y100 Z100", file=CaliGcodeExporter)#空驶

                if MachineType=="A1mini" or MachineType=="A1":
                    print(Calibe_Sing, file=CaliGcodeExporter)#唱歌

                #补全结束
                print(calibe[i].strip("\n"), file=CaliGcodeExporter)
        CaliGcodeExporter.close()
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