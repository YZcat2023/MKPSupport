# coding=utf-8
from CTkMessagebox import CTkMessagebox
from tkinter import BooleanVar as Tk_BooleanVar
from tkinter import Menu as Tk_Menu
from tkinter import Canvas as Tk_Canvas
import re, os, ctypes, sys
from PIL import Image
import requests
import webbrowser
from calibe import Calibe as Calibe_Sing
from calibe import ZOffset as ZOffset_Sing
from tower import Temp_Wiping_Gcode, Temp_Tower_Base_Layer_Gcode
from sys import exit 
import toml,argparse
import customtkinter as ctk
from datetime import datetime
from CTkScrollableDropdown import *
from CTkToolTip import *
from shapely.geometry import Polygon
import numpy as np
from scipy.spatial import ConvexHull

#check the language setting
def should_use_english():
    """检测系统是否为简体中文，若不是则返回True（应使用英语）"""
    try:
        kernel32 = ctypes.windll.kernel32
        # 获取系统语言ID (LCID)
        lang_id = kernel32.GetUserDefaultUILanguage()
        
        # 简体中文的LCID是 0x0804 (十进制2052)
        # 如果不是0x0804，就判定为使用英语
        return lang_id != 0x0804
        
    except Exception:
        # 如果检测失败，保守起见使用英语
        return True
if should_use_english():
    lang_setting = "EN"
    lang_setting = "CN"
else:
    lang_setting = "CN"

GSourceFile = ""
TomlName=""
Modify_Config_Flag=False
CCkcheck_flag = True# 检查调试标志，默认为False
CCkcheck_flag = False
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
ScaleFactor = ctypes.windll.shcore.GetScaleFactorForDevice(0)/100

def CenterWindowToDisplay(Screen: ctk, width: int, height: int, scale_factor: float = 1.0):
    """Centers the window to the main display/monitor"""
    screen_width = Screen.winfo_screenwidth()
    screen_height = Screen.winfo_screenheight()
    x = int(((screen_width/2) - (width/2)) * scale_factor)
    y = int(((screen_height/2) - (height/1.5)) * scale_factor)
    return f"{width}x{height}+{x}+{y}"

local_version = "Wisteria 6.4.2"

class MKPMessagebox:
    @staticmethod
    def show_info(title, message, buttons=None):
        msg_box = ctk.CTk()
        msg_box.title(title)
        if title =="Warning" or title=="警告" or title=="警报":
            msg_box.attributes("-topmost", True)
            print("警告对话框已置顶")
            #绑定窗口关闭事件到程序退出
            def on_closing():
                os._exit(0)
            msg_box.protocol("WM_DELETE_WINDOW", on_closing)
        msg_box.iconbitmap(mkpicon_path)
        # msg_box.geometry("400x200")
        ctk.set_appearance_mode("Dark")
        msg_box.attributes("-alpha",0.93)
        
        if message!="路径已复制到剪贴板。":
            msg_box.geometry(CenterWindowToDisplay(msg_box, 400, 120, msg_box._get_window_scaling()))
        else:
            msg_box.geometry(CenterWindowToDisplay(msg_box, 400,90, msg_box._get_window_scaling()))
        msg_box.resizable(width=False, height=False)
        # 设置按钮结果变量
        msg_box.result = None
        
        def safe_destroy():
            # 先退出mainloop，再销毁窗口
            msg_box.quit()
            try:
                msg_box.destroy()
            except:
                pass
        
        def on_button_click(button_text):
            msg_box.result = button_text
            # 延迟一小段时间再销毁，避免动画冲突
            msg_box.after(10, safe_destroy)
        
        label = ctk.CTkLabel(msg_box, text=message, wraplength=350, font=("SimHei", 15))
        if lang_setting=="EN":
            label.configure(font=("Segoe UI", 14))
        label.pack(pady=20)
        
        # 处理按钮参数
        if buttons is None:
            buttons = ["确定"]
        elif isinstance(buttons, str):
            buttons = [buttons]
        
        # 特殊处理：如果消息是"路径已复制到剪贴板。"，则不创建按钮且600ms后自动消失
        if message == "路径已复制到剪贴板。" or message == "The path has been copied to the clipboard.":
            # 不创建任何按钮
            # 600ms后自动关闭
            msg_box.after(600, safe_destroy)
        else:
            # 创建按钮框架
            button_frame = ctk.CTkFrame(msg_box)
            button_frame.pack(pady=10, side="bottom")
            
            # 创建按钮
            for i, button_text in enumerate(buttons):
                button = ctk.CTkButton(
                    button_frame, 
                    text=button_text, 
                    command=lambda btn_text=button_text: on_button_click(btn_text),
                    font=("SimHei", 12)
                )
                if lang_setting=="EN":
                    button.configure(font=("Segoe UI", 12,"bold"))
                button.pack(side="left", padx=5)
        
        msg_box.mainloop()
        return msg_box.result

#更新
def check_for_updates():
    global local_version
    url = "https://gitee.com/Jhmodel/MKPSupport/raw/main/UPDATE.md"  
    # url="locale"
    change_log_url = "https://gitee.com/Jhmodel/MKPSupport/raw/main/changelog.md"
    change_log_path=os.path.join(os.path.join(os.path.expanduser("~/Documents"), "MKPSupport"), "Data", "changelog.md")
    local_change_log = ""
    #查找本地的mkp_config.toml文件
    config_path = os.path.join(os.path.join(os.path.expanduser("~/Documents"), "MKPSupport"), "Data","mkp_config.toml")
    program_auto_update = False
    config_auto_update = False

    if os.path.exists(config_path):
        #尝试检查mkp_config.toml文件是否有设置自动更新
        config = toml.load(config_path)
        #检查是否有自动更新设置，如果有的话，program和config都是怎么设置的，如果都是为真，那就说明用户同意两个的自动更新
        auto_update = config.get("auto_update", {})
        # 读取program_auto_update，如果不存在则默认为True
        program_auto_update = auto_update.get("program")
        if program_auto_update is None:
            program_auto_update = True

        # 读取config_auto_update，如果不存在则默认为False
        config_auto_update = auto_update.get("config")
        if config_auto_update is None:
            config_auto_update = False
        # print(f"用户选择了程序自动更新：{program_auto_update}，配置文件自动更新：{config_auto_update}")
    #本体更新通知
    try:
        response = requests.get(url, stream=True, verify=False)
        if response.status_code == 200:
            content = response.text  # 将文件内容加载到内存
            if content.find(local_version) == -1 and local_version.find("Alpha") == -1:
                #如果读取toml表明用户愿意自动更新程序，那么不再显示更新窗口
                if not program_auto_update:
                    show_update_window(content)
                elif program_auto_update:
                    #启动updater.exe，参数传入本程序接收到的参数：sys.argv
                    #os.system传入start的是本程序所在目录的updater.exe
                    current_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
                    updater_path = os.path.join(current_dir, "updater.exe")
                    #参数：TomlName  GSourceFile 
                    # 执行
                    result = ctypes.windll.shell32.ShellExecuteW(
                        None,      # 父窗口句柄
                        "open",    # 操作
                        updater_path,  # 可执行文件路径
                        f'--Toml {TomlName} --Gcode {GSourceFile}',  # 参数
                        None,      # 工作目录
                        0          # 0 = 隐藏窗口（相当于 start /b）
                    )
                    exit(0)
                    

            #如果本地是5.7但是远端是5.7.1这种小版本更新，也想要提示，通过检验小数点是否在从远端版本号的末尾出现，不只是5.7，也可能是其他的。首先要检查与远端文本重合的位置后面是空格还是小数点，是小数点就说明有小版本更新
            elif content.find(local_version) != -1:
                pos = content.find(local_version) + len(local_version)
                if pos < len(content) and content[pos] == '.':
                    show_update_window(content)
        else:
            print(f"请求失败，状态码：{response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"请求失败，原因：{e}")

    #如果本地没有更新日志文件，就创建一个空的
    if not os.path.exists(change_log_path):
        os.makedirs(os.path.dirname(change_log_path), exist_ok=True)
        with open(change_log_path, "w", encoding="utf-8") as f:
            f.write("")
    #如果有，就读取
    else:
        with open(change_log_path, "r", encoding="utf-8") as f:
            local_change_log = f.read()
        # print("Local Change Log:", local_change_log)    
        
    #与远程的对比，如果远程有新的内容（新的内容永远加在旧的内容的后面），就在show_change_log显示新的内容（不显示旧的内容），然后把本地的changelog更新
    try:
        response = requests.get(change_log_url, stream=True, verify=False)
        if response.status_code == 200:
            content = response.text  # 将文件内容加载到内存
            # print("Remote Change Log:", content)
            #检本地行数==远程行数？
            if content.count("\n") != local_change_log.count("\n"):#不等，说明远程有新东西
                print("远程有"+str(content.count("\n"))+"行新内容")
                print("本地内容行数："+str(local_change_log.count("\n")))
            # if local_change_log.find(content) == -1:#没有，说明远程有新东西
               #写入本地
                with open(change_log_path, "w", encoding="utf-8", newline='\n') as f:
                    f.write(content)
                # show_change_log(content.replace(local_change_log, ""))

        else:
            print(f"请求失败，状态码：{response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"请求失败，原因：{e}")

def show_update_window(content):
    # 创建主窗口
    ctk.set_appearance_mode("Dark")
    update_window= ctk.CTk()  # 使用customtkinter创建窗口
    # update_window = tk.Tk()
    window.attributes('-topmost', False)
    window.withdraw()  # 隐藏主窗口
    # MKPMessagebox.show_info("版本信息","当前MKPSupport版本："+local_version+"\n\n正在检查更新，请稍候...")
    # result = MKPMessagebox.show_info("提示", "操作成功", "确定")
    # print(result)
    update_window.attributes("-alpha",0.93)
    update_window.title("更新提示")
    update_window.geometry("400x300")
    update_window.geometry(CenterWindowToDisplay(update_window, 400, 300, update_window._get_window_scaling()))  # 居中显示窗口
    # update_window.resizable(width=False, height=False)
    update_window.maxsize(400,300)
    update_window.minsize(400,300)
    update_window.iconbitmap(mkpicon_path)
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
        webbrowser.open("https://gitee.com/Jhmodel/MKPSupport/releases/download/gp_update/Bambu_Only_MKPSupport_Setup.exe")
        # update_window.quit()  # 关闭窗口
        update_window.destroy()
        os._exit(0)
    ctk.set_default_color_theme("green")
    button_frame = ctk.CTkFrame(update_window,fg_color="transparent")
    button_frame.pack()
    update_button = ctk.CTkButton(button_frame, text="前往更新", command=on_update,font=("SimHei",15))  # 使用customtkinter的按钮
    update_button.pack(side="left", padx=5)  # 靠左排列
    continue_button = ctk.CTkButton(button_frame, text="稍后再说", command=lambda:on_pass(),font=("SimHei",15))  # 使用customtkinter的按钮
    continue_button.pack(side="left", padx=5)  # 靠左排列
    #把这个关闭对话框与程序结束exit(0)绑定：
    def on_close():

        update_window.withdraw()
        update_window.quit()
        update_window.destroy()
    def on_pass():
        try:
            update_window.quit()
            update_window.after(100, update_window.destroy)
        except:
            update_window.withdraw()
            pass
    update_window.protocol("WM_DELETE_WINDOW", on_close)  # 绑定关闭事件
    # update_window.attributes('-topmost', True)
    update_window.mainloop()  # 运行主循环

def show_change_log(content):
    # 创建主窗口
    update_window= ctk.CTk()  # 使用customtkinter创建窗口
    # update_window = tk.Tk()
    update_window.title("Changelog")
    update_window.geometry("400x300")
    update_window.geometry(CenterWindowToDisplay(update_window, 400, 300, update_window._get_window_scaling()))  # 居中显示窗口
    update_window.resizable(width=False, height=False)
    # 添加标签
    label = ctk.CTkLabel(update_window, text="MKP更新日志(仅作参考，以最新说明为准)", anchor="w",font=("SimHei",15))  # 使用customtkinter的标签
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
        # update_window.quit()  # 关闭窗口
        try:
            update_window.quit()
            # update_window.after(100, update_window.destroy)
        except:
            pass
        # update_window.destroy()
    ctk.set_default_color_theme("green")
    button_frame = ctk.CTkFrame(update_window)
    button_frame.pack()
    update_button = ctk.CTkButton(button_frame, text="好的", command=on_update,font=("SimHei",15))  # 使用customtkinter的按钮
    update_button.pack()
    #把这个关闭对话框与程序结束exit(0)绑定：
    def on_close():
        try:
            update_window.quit()
            # update_window.after(100, update_window.destroy)
        except:
            pass
            # os._exit(0)
    # update_window.protocol("WM_DELETE_WINDOW", on_close)  # 绑定关闭事件
    update_window.mainloop()  # 运行主循环

window = ctk.CTk()
window.title('MKPSupport Version '+local_version)
window.overrideredirect(True)
#window置于最前
window.attributes('-topmost', True)
window.geometry(CenterWindowToDisplay(window, 400,299, window._get_window_scaling()))  # 居中显示窗口
window.resizable(width=False, height=False)
mkpexecutable_dir = os.path.dirname(sys.executable)
mkpinternal_dir = os.path.join(mkpexecutable_dir, "_internal")
mkpimage_path = os.path.join(mkpinternal_dir, "in.png")
mkpres_dir = os.path.join(mkpexecutable_dir, "resources")
mkpicon_path = os.path.join(mkpres_dir, "MKP.ico")
window.iconbitmap(False, mkpicon_path)
try:
    original_image = Image.open(mkpimage_path)
except:
    original_image = Image.open("in.png")
# image0 = image0.resize((400, 299),Image.Resampling.LANCZOS)
# ctk_image = ctk.CTkImage(light_image=image0, size=(400, 299))

ctk_image = ctk.CTkImage(
    light_image=original_image,
    size=(400, 299)  # 只在这里指定显示尺寸
)
# label = ctk.CTkLabel(window, image=ctk_image, text="")
# label.pack(fill="both", expand=True)  # 满幅显示图片
# #需要在这个图片的上面再显示一行文字

# 在图片上添加文字标签
loading_ribbon=""
if Modify_Config_Flag==True:
    loading_ribbon="\n\n\n\n\n\n\n正在加载预设管理器..."
    if lang_setting=="EN":
        loading_ribbon="\n\n\n\n\n\n\nLoading Preset Manager..."
else:
    #在后处理Gcode
    loading_ribbon="\n\n\n\n\n\n\n正在分析Gcode文件..."
    if lang_setting=="EN":
        loading_ribbon="\n\n\n\n\n\n\nAnalyzing Gcode File..."
text_label_loading = ctk.CTkLabel(
    window, 
    text=loading_ribbon,
    image=ctk_image,
    font=("SimHei", 14),
    text_color="white",
    bg_color="transparent"
)
text_label_loading.place(relx=0.5, rely=0.5, anchor="center")  # 水平居中，垂直位置在10%处

def on_closing():
    os._exit(0)  # 直接退出程序，不做任何处理
window.protocol("WM_DELETE_WINDOW", on_closing)  # 绑定关闭事件
window.update() 

class para:
    # parameters
    Switch_Tower_Type=2  # 擦料塔类型开关，1为慢线，2为快线
    Remove_wrap_detect_flag = False  # 去除环绕检测标志
    Enable_ironing=False#这是识别是否开启熨烫功能的
    Ironing_Removal_Flag=False
    Use_Wiping_Towers=None#这是识别是否用内置擦嘴塔的
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
    WipeTower_Print_Speed=0#典型打印速度（取值来自外墙）
    Retract_Length=0#回抽长度
    Update_date = None
    Temp_ZOffset_Calibr=0.0
    Temp_XOffset_Calibr=0.0
    Temp_YOffset_Calibr=0.0
    Nozzle_Switch_Tempature=0#喷嘴切换温度
    L803_Leak_Pervent_Flag=False#L803漏料预防功能开关
    Minor_Nozzle_Diameter_Flag=False#小喷嘴直径开关
    Fan_Speed=0#风扇速度
    New_Preset_Name=""
    Drag_x=0
    Drag_y=0
    Wait_for_Drying_Command=""#等待干燥时间
    Extra_Tower_Height=0#额外擦料塔高度
    Remove_G3_Flag = False#擦料塔G3命令删除开关
    MKPRetract=0#回抽长度
    Nozzle_Cooling_Flag=None#喷嘴降温开关
    Part_Drying_Speed=0#局部干燥速度
    Small_Feature_Factor=1#小特征因子
    Filament_Type="PETG"
    Slicer="BambuStudio"
    Silicone_Wipe_Flag=False#硅胶擦嘴开关
    First_Pen_Revitalization_Flag=True
    Iron_apply_Flag=False#熨烫应用开关,现在已经被Interface_ironing_Flag代替
    Interface_ironing_Flag=False#界面熨烫开关,检测到; enable_support_ironing = 1就开启
    User_Dry_Time=0#用户自定义干燥时间
    right_text_var=None
    progress_calc=0
    Force_Thick_Bridge_Flag=None#强制厚桥开关
    current_selected_preset="P1"#当前选中的预设
    Support_Extrusion_Multiplier=1.0#支撑结构密度比例
    Unsafe_Close_Flag=True#不安全关闭标志
    Allow_Proceed_Flag=False#允许继续标志
    mail="Standby"
    first_layer_wipetower_collision_check_flag=True
    Machine_Max_X=999#机器最大X坐标
    Machine_Max_Y=999#机器最大Y坐标
    Machine_Min_X=-999#机器最小X坐标
    Machine_Min_Y=-999#机器最小Y坐标
    Move_Walls_Height=0
    Allow_Temp_Export_Flag=True#允许导出临时文件标志
    Avoid_Wall_Export_Flag=False#避免外墙导出标志
    More_Extrude_Flag=False#更多挤出开关
    Add_Wall_Collision_Line_Flag=False#
    Append_Support_Flag=False
    Refill_Extrude_Command=""
    Use_Disk_Wipe_Flag=True
    Support_Layer=0
    Wall_Print_Speed=0
    Wipe_remove_flag=0
    Last_Feature=""
    Need_to_append_silent_Wall_Flag=False
    Speed_Smooth_Sum=0
    Support_Interface_Speed=0
    Tree_Support_Flag=False#是否开启树状支撑结构
    is_first_Z_Calibration_Flag=True#是否是第一次校准Z轴
    is_first_XY_Calibration_Flag=True#是否是第一次校准XY轴
User_Input = []#存用户输入的参数
Output_Filename=""#输出文件名，最终会被更名

Temp_Wiping_Gcode = """
;Tower_Layer_Gcode
EXTRUDER_REFILL
G1 X20 Y10.19
NOZZLE_HEIGHT_ADJUST
G1 F9600
G1 X20 Y20 E.25658
G1 X29.81 Y20 E.25658
G1 E-.21 F5400
;WIPE_START
G1 F9600
G1 X28.81 Y20 E-.09
;WIPE_END
G1 X23.71 Y25.679 F30000
G1 X20 Y29.81
G1 E.3 F5400
G1 F9600
G1 X20 Y20 E.25658
G1 X10.19 Y20 E.25658
G1 E-.21 F5400
;WIPE_START
G1 F9600
G1 X11.19 Y20 E-.09
;WIPE_END
G1 X17.943 Y23.556 F30000
G1 X29.8 Y29.8
G1 X29.8 Y29.398
G1 E.3 F5400
G1 F9600
;START_HERE
G1 X10.602 Y29.398 E.60441
G1 X10.602 Y10.602 E.60441
G1 X29.398 Y10.602 E.60441
G1 X29.398 Y29.338 E.60248
G1 X29.79 Y29.79
G1 X10.21 Y29.79 E.58322
G1 X10.21 Y10.21 E.58322
G1 X29.79 Y10.21 E.58322
G1 X29.79 Y29.73 E.58143
;END_HERE
G92 E0
G1 E-.21 F5400
;WIPE_START
G1 F9600
G1 X28.8 Y29.762 E-.1
;WIPE_END
EXTRUDER_RETRACT
G1 X28.7 Y29.76
TOWER_ZP_ST
;Tower_Layer_Gcode Finished
""" 

Temp_Tower_Base_Layer_Gcode = """
;Tower_Base_Layer_Gcode
G1 X19.681 Y20.319
NOZZLE_HEIGHT_ADJUST
EXTRUDER_REFILL
G1 F9600
G1 X19.681 Y20.319 E.02318
G1 X20.319 Y20.319 E.02318
G1 X20.319 Y19.681 E.02318
G1 X19.681 Y19.681 E.02318
G1 X19.304 Y19.304 F30000
G1 F9600
G1 X20.696 Y19.304 E.05059
G1 X20.696 Y20.696 E.05059
G1 X19.304 Y20.696 E.05059
G1 X19.304 Y19.304 E.05059
G1 X18.927 Y18.927 F30000
G1 F9600
G1 X21.073 Y18.927 E.078
G1 X21.073 Y21.073 E.078
G1 X18.927 Y21.073 E.078
G1 X18.927 Y18.927 E.078
G1 X18.55 Y18.55 F30000
G1 F9600
G1 X18.55 Y21.45 E.1054
G1 X21.45 Y21.45 E.1054
G1 X21.45 Y18.55 E.1054
G1 X18.55 Y18.55 E.1054
G1 X18.173 Y18.173 F30000
G1 F9600
G1 X18.173 Y21.827 E.13281
G1 X21.827 Y21.827 E.13281
G1 X21.827 Y18.173 E.13281
G1 X18.173 Y18.173 E.13281
G1 X17.796 Y17.796 F30000
G1 F9600
G1 X22.204 Y17.796 E.16022
G1 X22.204 Y22.204 E.16022
G1 X17.796 Y22.204 E.16022
G1 X17.796 Y17.796 E.16022
G1 X17.419 Y17.419 F30000
G1 F9600
G1 X22.581 Y17.419 E.18763
G1 X22.581 Y22.581 E.18763
G1 X17.419 Y22.581 E.18763
G1 X17.419 Y17.419 E.18763
G1 X17.042 Y17.042 F30000
G1 F9600
G1 X22.958 Y17.042 E.21504
G1 X22.958 Y22.958 E.21504
G1 X17.042 Y22.958 E.21504
G1 X17.042 Y17.042 E.21504
G1 X16.664 Y16.664 F30000
G1 F9600
G1 X16.664 Y23.336 E.24245
G1 X23.336 Y23.336 E.24245
G1 X23.336 Y16.664 E.24245
G1 X16.664 Y16.664 E.24245
G1 X16.287 Y16.287 F30000
G1 F9600
G1 X16.287 Y23.713 E.26986
G1 X23.713 Y23.713 E.26986
G1 X23.713 Y16.287 E.26986
G1 X16.287 Y16.287 E.26986
G1 X15.91 Y15.91 F30000
G1 F9600
G1 X24.09 Y15.91 E.29726
G1 X24.09 Y24.09 E.29726
G1 X15.91 Y24.09 E.29726
G1 X15.91 Y15.91 E.29726
G1 X15.533 Y15.533 F30000
G1 F9600
G1 X15.533 Y24.467 E.32467
G1 X24.467 Y24.467 E.32467
G1 X24.467 Y15.533 E.32467
G1 X15.533 Y15.533 E.32467
G1 X15.156 Y15.156 F30000
G1 F9600
G1 X15.156 Y24.844 E.35208
G1 X24.844 Y24.844 E.35208
G1 X24.844 Y15.156 E.35208
G1 X15.156 Y15.156 E.35208
G1 X14.779 Y14.779 F30000
G1 F9600
G1 X25.221 Y14.779 E.37949
G1 X25.221 Y25.221 E.37949
G1 X14.779 Y25.221 E.37949
G1 X14.779 Y14.779 E.37949
G1 X14.402 Y14.402 F30000
G1 F9600
G1 X14.402 Y25.598 E.4069
G1 X25.598 Y25.598 E.4069
G1 X25.598 Y14.402 E.4069
G1 X14.402 Y14.402 E.4069
G1 X14.025 Y14.025 F30000
G1 F9600
G1 X14.025 Y25.975 E.43431
G1 X25.975 Y25.975 E.43431
G1 X25.975 Y14.025 E.43431
G1 X14.025 Y14.025 E.43431
G1 X13.648 Y13.648 F30000
G1 F9600
G1 X26.352 Y13.648 E.46172
G1 X26.352 Y26.352 E.46172
G1 X13.648 Y26.352 E.46172
G1 X13.648 Y13.648 E.46172
G1 X13.271 Y13.271 F30000
G1 F9600
G1 X13.271 Y26.729 E.48913
G1 X26.729 Y26.729 E.48913
G1 X26.729 Y13.271 E.48913
G1 X13.271 Y13.271 E.48913
G1 X12.894 Y12.894 F30000
G1 F9600
G1 X12.894 Y27.106 E.51653
G1 X27.106 Y27.106 E.51653
G1 X27.106 Y12.894 E.51653
G1 X12.894 Y12.894 E.51653
G1 X12.517 Y12.517 F30000
G1 F9600
G1 X12.517 Y27.483 E.54394
G1 X27.483 Y27.483 E.54394
G1 X27.483 Y12.517 E.54394
G1 X12.517 Y12.517 E.54394
G1 X12.14 Y12.14 F30000
G1 F9600
G1 X12.14 Y27.86 E.57135
G1 X27.86 Y27.86 E.57135
G1 X27.86 Y12.14 E.57135
G1 X12.14 Y12.14 E.57135
G1 X11.762 Y11.762 F30000
G1 F9600
G1 X28.238 Y11.762 E.59876
G1 X28.238 Y28.238 E.59876
G1 X11.762 Y28.238 E.59876
G1 X11.762 Y11.762 E.59876
G1 X11.385 Y11.385 F30000
G1 F9600
G1 X28.615 Y11.385 E.62617
G1 X28.615 Y28.615 E.62617
G1 X11.385 Y28.615 E.62617
G1 X11.385 Y11.385 E.62617
G1 X11.008 Y11.008 F30000
G1 F9600
G1 X28.992 Y11.008 E.65358
G1 X28.992 Y28.992 E.65358
G1 X11.008 Y28.992 E.65358
G1 X11.008 Y11.008 E.65358
G1 X10.631 Y10.631 F30000
G1 F9600
G1 X29.369 Y10.631 E.68099
G1 X29.369 Y29.369 E.68099
G1 X10.631 Y29.369 E.68099
G1 X10.631 Y10.631 E.68099
G1 X10.254 Y10.254 F30000
G1 F9600
G1 X29.746 Y10.254 E.70839
G1 X29.746 Y29.746 E.70839
G1 X10.254 Y29.746 E.70839
G1 X10.254 Y10.254 E.70839
G1 X9.877 Y9.877 F30000
G1 F9600
G1 X30.123 Y9.877 E.7358
G1 X30.123 Y30.123 E.7358
G1 X9.877 Y30.123 E.7358
G1 X9.877 Y9.877 E.7358
G1 X9.5 Y9.5 F30000
G1 F9600
G1 X9.5 Y30.5 E.76321
G1 X30.5 Y30.5 E.76321
G1 X30.5 Y9.5 E.76321
G1 X9.5 Y9.5 E.76321
G1 X9.123 Y9.123 F30000
G1 F9600
G1 X9.123 Y30.877 E.79062
G1 X30.877 Y30.877 E.79062
G1 X30.877 Y9.123 E.79062
G1 X9.123 Y9.123 E.79062
G1 X8.746 Y8.746 F30000
G1 F9600
G1 X31.254 Y8.746 E.81803
G1 X31.254 Y31.254 E.81803
G1 X8.746 Y31.254 E.81803
G1 X8.746 Y8.746 E.81803
G1 X8.369 Y8.369 F30000
G1 F9600
G1 X8.369 Y31.631 E.84544
G1 X31.631 Y31.631 E.84544
G1 X31.631 Y8.369 E.84544
G1 X8.369 Y8.369 E.84544
G1 X7.992 Y7.992 F30000
G1 F9600
G1 X32.008 Y7.992 E.87285
G1 X32.008 Y32.008 E.87285
G1 X7.992 Y32.008 E.87285
G1 X7.992 Y7.992 E.87285
G1 X7.615 Y7.615 F30000
G1 F9600
G1 X7.615 Y32.385 E.90025
G1 X32.385 Y32.385 E.90025
G1 X32.385 Y7.615 E.90025
G1 X7.615 Y7.615 E.90025
G1 X7.238 Y7.238 F30000
G1 F9600
G1 X32.762 Y7.238 E.92766
G1 X32.762 Y32.762 E.92766
G1 X7.238 Y32.762 E.92766
G1 X7.238 Y7.238 E.92766
G1 X6.86 Y6.86 F30000
G1 F9600
G1 X33.14 Y6.86 E.95507
G1 X33.14 Y33.14 E.95507
G1 X6.86 Y33.14 E.95507
G1 X6.86 Y6.86 E.95507
G1 X6.86 Y5.9 F30000
EXTRUDER_RETRACT
;Tower Base Layer Finished
"""


def Invert_Flag(Flag):
    newvalue=not Flag.get()
    Flag.set(newvalue)
    print(Flag.get())

def create_draggable_square_app(x,y):
    """创建并返回一个包含可拖动方块的CTk窗口（左下角原点坐标系）"""
    # 初始化窗口
    cltpop = ctk.CTk()
    cltpop.geometry("320x350")  # 增加高度以容纳按钮
    # cltpop.geometry(CenterWindowToDisplay(cltpop, 320, 340, cltpop._get_window_scaling()))  # 居中显示窗口
    cltpop.title("擦料塔位置调整")
    if lang_setting=="EN":
        cltpop.title("Wipe Tower Position Adjustment")
    cltpop.after(11,lambda:cltpop.iconbitmap(mkpicon_path))
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
        
        canvas = Tk_Canvas(
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
        text="X: 0, Y: 0", 
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
    if lang_setting=="EN":
        confirm_btn.configure(text="Confirm",font=("Segoe UI", 14))
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
        #设置背景色为金黄
        canvas.configure(bg="#DAA520")
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
        x1 = x
        y1 = height - y - square_size  # 转换为画布坐标系
        x2 = x1 + square_size
        y2 = y1 + square_size
        
        square_id = canvas.create_rectangle(
            x1, y1, x2, y2,
            fill=square_fill,
            outline=square_outline,
            width=2,
            tags="square"
        )
        #设置初始方块的颜色为白色
        canvas.itemconfig(square_id, fill="white")
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
        # coord_label.configure(text=f"x: ({rel_x:.0f}, {rel_y:.0f})")
        coord_label.configure(text=f"X: {cx:.0f}, Y: {cy:.0f}")
        if cx<90 and cy<90:
            #显然在左下角
            message_loc="打印板的左下角，X轴向右，Y轴向上。"
            if lang_setting=="EN":
                message_loc="the bottom-left corner of the print bed, with X axis to the right and Y axis upwards."
        # elif X>200 and Y<90:
        elif cx>200 and cy<90:
            #显然在右下角
            message_loc="打印板的右下角，X轴向左，Y轴向上。"
            if lang_setting=="EN":
                message_loc="the bottom-right corner of the print bed, with X axis to the left and Y axis upwards."
        # elif X<90 and Y>200:
        elif cx<90 and cy>200:
            #显然在左上角
            message_loc="打印板的左上角，X轴向右，Y轴向下。"
            if lang_setting=="EN":
                message_loc="the top-left corner of the print bed, with X axis to the right and Y axis downwards."
        # elif X>200 and Y>200:
        elif cx>200 and cy>200:
            #显然在右上角
            message_loc="打印板的右上角，X轴向左，Y轴向下。"
            if lang_setting=="EN":
                message_loc="the top-right corner of the print bed, with X axis to the left and Y axis downwards."
        else:
            message_loc="打印板的X:"+str(int(cx))+"，Y:"+str(int(cy))+"位置。请注意避让打印模型。"
            if lang_setting=="EN":
                message_loc="the position X:"+str(int(cx))+", Y:"+str(int(cy))+" on the print bed. Please be careful to avoid the printed model."
        
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
    # popup.resizable(False, False)
    popup.geometry(CenterWindowToDisplay(popup, 569, 660, popup._get_window_scaling()))
    popup.maxsize(600, 690)
    popup.minsize(569, 660)
    popup.attributes("-alpha",0.93)
    popup.title("配置向导")
    popup.after(201, lambda: popup.iconbitmap(mkpicon_path))
    # 使用CTk的网格布局管理器
    popup.grid_columnconfigure(1, weight=1)
    # 保存初始大小
    original_width = 569
    original_height = 650

    def on_configure(event):
        """窗口配置发生变化时触发"""
        if event.widget == popup:
            current_width = popup.winfo_width()
            current_height = popup.winfo_height()
            
            # 如果大小改变了，恢复原大小
            if (current_width != original_width or 
                current_height != original_height):
                # 使用after避免递归
                popup.after(30, lambda: popup.geometry(f"{original_width}x{original_height}"))
    # popup.bind("<Configure>", on_configure)
           
    labels = [
        "涂胶速度限制[MM/S]", "X坐标补偿值[MM]", "Y坐标补偿值[MM]", 
        "喷嘴笔尖高度差[MM]", "自定义工具头获取 G-code", "自定义工具头收起 G-code",
        "使用擦嘴塔而非棒棒糖擦拭", "擦料塔的起始点", "擦料塔打印速度[MM/S]","强制厚桥开关(仅BambuStudio)","涂胶期间是否降温","额外干燥时间[秒]","支撑体挤出倍率"
    ]
    entries = []
    
    # para.Enable_ironing = cTk_BooleanVar(value=False)
    # para.Have_Wiping_Components = cTk_BooleanVar(value=True)
    
    def create_right_click_menu(widget):
        """为ScrolledText添加右键菜单"""
        menu = Tk_Menu(widget, tearoff=0)
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
        # ctk.CTkLabel(popup, text=label + ":", font=("SimHei",12)).grid(row=i, column=0, padx=10, pady=5, sticky="w")
        label_item = ctk.CTkLabel(popup, text=label + ":", font=("SimHei",12))
        label_item.grid(row=i, column=0, padx=10, pady=5, sticky="w")

        
        if label in ["自定义工具头获取 G-code", "自定义工具头收起 G-code"]:
            text_box = ctk.CTkTextbox(popup, width=40, height=79, fg_color=("white","#343638"),border_width=2,corner_radius=9, font=("SimHei",12))
            text_box.grid(row=i, column=1, padx=10, pady=5, sticky="ew")
            # create_right_click_menu(text_box)
            entries.append(text_box)
            if lang_setting!="EN":
                tooltip_1 = CTkToolTip(label_item, message="\n自定义工具头获取 G-code与自定义工具头收起 G-code分别负责弹出与收起笔尖。\n\n如果您的笔尖不能正常升降，请微调其中的指令。\n", font=("SimHei",12))
            else:
                tooltip_1 = CTkToolTip(label_item, message="\nCustom Toolhead Deploy G-code and Custom Toolhead Stow G-code are responsible for deploying and stowing the pen tip respectively.\n\nIf your pen tip does not lift or lower properly, please fine-tune the commands in these fields.\n",wraplength=350, font=("Segoe UI",12))
        elif label == "使用擦嘴塔而非棒棒糖擦拭":
            print("创建窗口时Have_Wiping_Components:", para.Use_Wiping_Towers.get())
            checkbox = ctk.CTkCheckBox(
                popup, text="", variable=para.Use_Wiping_Towers,
                onvalue=True,  # 选中时的值
                offvalue=False,  # 未选中时的值
             command=lambda: print(para.Use_Wiping_Towers.get())
            )
            checkbox.grid(row=i, column=1, padx=10, pady=5, sticky="w")
            entries.append(checkbox)
            if lang_setting!="EN":
                tooltip_2= CTkToolTip(label_item, message="\nMKP需要擦除涂胶期间渗出的残丝。如果不启用，自动在支撑结构上形成若干棒棒糖状的结构用于清洁喷嘴。否则，程序将在擦嘴过程中打印一个擦料塔。\n\n如果您不喜欢擦嘴塔，请不要勾选\n", font=("SimHei",12))
            else:
                tooltip_2= CTkToolTip(label_item, message="\nMKP needs to wipe off the residual strings that ooze out during the gluing process. If you do not check this option, mkp will form a few barbwire-like structures on the support structure to clean the nozzle. Otherwise, a wipe tower will be printed during the wipe process.\n\nIf you do not like the wipe tower, do not check this option.\n", wraplength=350, font=("Segoe UI",12))
            # tooltip_2= CTkToolTip(label_item, message="\nMKP需要擦除涂胶期间渗出的残丝。启用后，程序将在擦嘴过程中打印一个擦料塔。\n\n如果您不喜欢擦嘴塔，可以升级为硅胶擦嘴组件以方便的刮去残丝\n", font=("SimHei",12))
        elif label == "涂胶期间是否降温":
            print("创建窗口时Nozzle_Cooling_Flag:", para.Nozzle_Cooling_Flag.get())
            checkbox_cool = ctk.CTkCheckBox(
                popup, text="", variable=para.Nozzle_Cooling_Flag,
                onvalue=True,  # 选中时的值
                offvalue=False,  # 未选中时的值
             command=lambda: print(para.Nozzle_Cooling_Flag.get())
            )
            checkbox_cool.grid(row=i, column=1, padx=10, pady=5, sticky="w")
            entries.append(checkbox_cool)
            if lang_setting!="EN":
                tooltip_3= CTkToolTip(label_item, message="\n启用后，涂胶过程中喷嘴温度将降低至设定值（默认170℃），以减少涂胶时的渗出。\n\n请确保指定的耗材不会因为快速降温和升温而堵头\n", font=("SimHei",12))
            # tooltip_3= CTkToolTip(label_item, message="\n启用后，涂胶过程中喷嘴温度将降低至设定值（默认170℃），以减少涂胶时的渗出。\n\n请确保指定的耗材不会因为快速降温和升温而堵头\n", font=("SimHei",12))
            else:
                tooltip_3= CTkToolTip(label_item, message="\nWhen enabled, the nozzle temperature will be lowered to the set value (default 170℃) during the gluing process to reduce oozing during gluing.\n\nPlease ensure that the specified material will not clog due to rapid cooling and heating.\n",wraplength=550, font=("Segoe UI",12))
        
        elif label == "最小化涂胶区域":
            print("创建窗口时Enable_ironing:", para.Iron_apply_Flag.get())
            checkbox_iron = ctk.CTkCheckBox(
                popup, text="", variable=para.Iron_apply_Flag,
                onvalue=True,  # 选中时的值
                offvalue=False,  # 未选中时的值
             command=lambda: print(para.Iron_apply_Flag.get())
            )
            checkbox_iron.grid(row=i, column=1, padx=10, pady=5, sticky="w")
            entries.append(checkbox_iron)
            if lang_setting!="EN":
                tooltip_4= CTkToolTip(label_item, message="\n启用后，程序将在涂胶时以接触面熨烫范围为准，从而减少涂胶时间。\n\n仅在使用OrcaSlicer且开启支撑面熨烫功能时有效\n", font=("SimHei",12))
            else:
                tooltip_4= CTkToolTip(label_item, message="\nWhen enabled, the program will use the ironing range of the contact surface as the standard during gluing, thereby reducing gluing time.\n\nOnly effective when using OrcaSlicer with the support surface ironing function enabled.\n",wraplength=550, font=("Segoe UI",12))
        elif label == "强制厚桥开关(仅BambuStudio)":
            print("创建窗口时Force_Thick_Bridge_Flag:", para.Force_Thick_Bridge_Flag.get())
            checkbox_thick = ctk.CTkCheckBox(
                popup, text="", variable=para.Force_Thick_Bridge_Flag,
                onvalue=True,  # 选中时的值
                offvalue=False,  # 未选中时的值
             command=lambda: print(para.Force_Thick_Bridge_Flag.get())
            )
            checkbox_thick.grid(row=i, column=1, padx=10, pady=5, sticky="w")
            entries.append(checkbox_thick)
            if lang_setting!="EN":
                tooltip_10= CTkToolTip(label_item, message="\n启用后，程序将会把支撑过渡层调整为厚桥，从而改善低层高下，支撑桥接质量差的问题。\n\n仅在使用BambuStudio时有效\n", font=("SimHei",12))
            else:
                tooltip_10= CTkToolTip(label_item, message="\nWhen enabled, the program will adjust the support transition layer to a thick bridge, thereby improving the problem of poor support bridging quality under low layer heights.\n\nOnly effective when using BambuStudio.\n",wraplength=550, font=("Segoe UI",12))
        elif label == "擦料塔的起始点":
            frame = ctk.CTkFrame(popup, fg_color="transparent")
            frame.grid(row=i, column=1, padx=10, pady=5, sticky="w")
            # 添加调整位置按钮
            def adjust_position():
                """调用位置调整窗口并更新输入框"""
                #从输入框获取初始坐标
                x = float(entry_x.get())
                y = float(entry_y.get())
                create_draggable_square_app(x,y)  # 调用可视化调整函数
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
                text="调整位置",
                command=adjust_position,
                width=80,
                font=("SimHei", 12)
            )
            if lang_setting=="EN":
                adjust_btn.configure(text="Adjust",font=("Segoe UI", 12))
            adjust_btn.pack(side="left", padx=(0, 5))
            
            # X/Y输入框
            ctk.CTkLabel(frame, text="X:").pack(side="left")
            entry_x = ctk.CTkEntry(frame, width=40)
            entry_x.pack(side="left", padx=2)
            entry_x.insert(0, "5")
            
            ctk.CTkLabel(frame, text="Y:").pack(side="left", padx=(5,0))
            entry_y = ctk.CTkEntry(frame, width=40)
            entry_y.pack(side="left", padx=2)
            entry_y.insert(0, "5")
            
            entries.append((entry_x, entry_y))
            # tooltip_5= CTkToolTip(label_item, message="\n点击按钮弹出擦料塔位置调整窗口，拖动方块至合适位置后点击确定即可。\n\n建议将擦料塔放置在打印区域边缘且远离模型的位置，以免影响打印质量。\n", font=("SimHei",12))
            if lang_setting=="EN":
                tooltip_5= CTkToolTip(label_item, message="\nClick the button to pop up the wipe tower position adjustment window. Drag the square to the appropriate position and click Confirm.\n\nIt is recommended to place the wipe tower at the edge of the printing area and away from the model to avoid affecting print quality.\n",wraplength=550, font=("Segoe UI",12))
            else:
                tooltip_5= CTkToolTip(label_item, message="\n点击按钮弹出擦料塔位置调整窗口，拖动方块至合适位置后点击确定即可。\n\n建议将擦料塔放置在打印区域边缘且远离模型的位置，以免影响打印质量。\n", font=("SimHei",12))
        elif label == "擦料塔打印速度[MM/S]":
            entry_speed = ctk.CTkEntry(popup)
            entry_speed.grid(row=i, column=1, padx=10, pady=5, sticky="ew")
            entry_speed.insert(0, "50")
            entries.append(entry_speed)
            # tooltip_6= CTkToolTip(label_item, message="\n设置擦料塔打印速度，建议保持默认。\n\n对于TPU等最大体积速度很小的耗材，需要手动限制速度\n", font=("SimHei",12))
            if lang_setting!="EN":
                tooltip_6= CTkToolTip(label_item, message="\n设置擦料塔打印速度，建议保持默认。\n\n对于TPU等最大体积速度很小的耗材，需要手动限制速度\n", font=("SimHei",12))
            else:
                tooltip_6= CTkToolTip(label_item, message="\nSet the wipe tower printing speed, it is recommended to keep the default.\n\nFor materials such as TPU with a small maximum volumetric speed, manual speed limitation is required.\n",wraplength=550, font=("Segoe UI",12))
        elif label == "额外干燥时间[秒]":
            entry = ctk.CTkEntry(popup)
            entry.grid(row=i, column=1, padx=10, pady=5, sticky="ew")
            entry.insert(0, "0")
            entries.append(entry)
            if lang_setting!="EN":
                tooltip_7= CTkToolTip(label_item, message="\n设置涂胶完成后，等待的额外干燥时间（秒）。\n\n对于某些阻滞不良的笔芯，可以适当增加干燥时间以防止胶液尚未干透影响打印质量。\n", font=("SimHei",12))
            else:
                tooltip_7= CTkToolTip(label_item, message="\nSet the additional drying time (seconds) after gluing is completed.\n\nFor some pen refills with poor blockage, you can appropriately increase the drying time to prevent the glue from not being fully dried and affecting print quality.\n",wraplength=550, font=("Segoe UI",12))
            # tooltip_7= CTkToolTip(label_item, message="\n设置涂胶完成后，等待的额外干燥时间（秒）。\n\n对于某些阻滞不良的笔芯，可以适当增加干燥时间以防止胶液尚未干透影响打印质量。\n", font=("SimHei",12))
        
        elif label == "支撑体挤出倍率":
            entry = ctk.CTkEntry(popup)
            entry.grid(row=i, column=1, padx=10, pady=5, sticky="ew")
            entry.insert(0, "1.0")
            entries.append(entry)
            if lang_setting!="EN":
                tooltip_8= CTkToolTip(label_item, message="\n设置支撑体挤出倍率。\n\n可以适当调整该数值以减小支撑体硬度。\n", font=("SimHei",12))
            else:
                tooltip_8= CTkToolTip(label_item, message="\nSet the extrusion multiplier for the support structure.\n\nYou can appropriately adjust this value to reduce the hardness of the support structure.\n",wraplength=550, font=("Segoe UI",12))

            
        else:
            entry = ctk.CTkEntry(popup)
            entry.grid(row=i, column=1, padx=10, pady=5, sticky="ew")
            entries.append(entry)
            if label == "涂胶速度限制[MM/S]":
                if lang_setting!="EN":
                    tooltip_8= CTkToolTip(label_item, message="\n设置涂胶速度的上限，单位为MM/S。\n\n如果发现涂胶过程中出现断续现象，可以适当降低该数值以改善涂胶连续性。\n\n如果胶液过多，可以适当提高该数值以减少渗出。\n", font=("SimHei",12))
                else:
                    tooltip_8= CTkToolTip(label_item, message="\nSet the upper limit of the gluing speed, in MM/S.\n\nIf you find that there are intermittent phenomena during the gluing process, you can appropriately reduce this value to improve the continuity of the gluing.\n\nIf there is too much glue, you can appropriately increase this value to reduce oozing.\n",wraplength=550, font=("Segoe UI",12))
            elif label == "X坐标补偿值[MM]":
                if lang_setting!="EN":
                    tooltip_9= CTkToolTip(label_item, message="\n设置X轴方向的坐标补偿值，单位为MM。\n\n如果发现涂胶位置与预期位置存在偏差，可以通过调整该数值进行补偿。\n\n正值表示向右补偿，负值表示向左补偿。(参考坐标：正对机器，右手边为X正方向)\n", font=("SimHei",12))
                else:
                    tooltip_9= CTkToolTip(label_item, message="\nSet the coordinate compensation value in the X-axis direction, in MM.\n\nIf you find that the gluing position deviates from the expected position, you can adjust this value for compensation.\n\nA positive value indicates compensation to the right, and a negative value indicates compensation to the left. (Reference coordinates: facing the machine, the right hand side is the positive X direction)\n",wraplength=550, font=("Segoe UI",12))
                # tooltip_9= CTkToolTip(label_item, message="\n设置X轴方向的坐标补偿值，单位为MM。\n\n如果发现涂胶位置与预期位置存在偏差，可以通过调整该数值进行补偿。\n\n正值表示向右补偿，负值表示向左补偿。(参考坐标：正对机器，右手边为X正方向)\n", font=("SimHei",12))
            elif label == "Y坐标补偿值[MM]":
                if lang_setting!="EN":
                    tooltip_10= CTkToolTip(label_item, message="\n设置Y轴方向的坐标补偿值，单位为MM。\n\n如果发现涂胶位置与预期位置存在偏差，可以通过调整该数值进行补偿。\n\n正值表示向上补偿，负值表示向下补偿。(参考坐标：正对机器，远离观察者的方向为Y正方向)\n", font=("SimHei",12))
                else:
                    tooltip_10= CTkToolTip(label_item, message="\nSet the coordinate compensation value in the Y-axis direction, in MM.\n\nIf you find that the gluing position deviates from the expected position, you can adjust this value for compensation.\n\nA positive value indicates upward compensation, and a negative value indicates downward compensation. (Reference coordinates: facing the machine, the direction away from the observer is the positive Y direction)\n",wraplength=550, font=("Segoe UI",12))

                # tooltip_10= CTkToolTip(label_item, message="\n设置Y轴方向的坐标补偿值，单位为MM。\n\n如果发现涂胶位置与预期位置存在偏差，可以通过调整该数值进行补偿。\n\n正值表示向上补偿，负值表示向下补偿。(参考坐标：正对机器，远离观察者的方向为Y正方向)\n", font=("SimHei",12))
            elif label == "喷嘴笔尖高度差[MM]":
                if lang_setting!="EN":
                    tooltip_11= CTkToolTip(label_item, message="\n设置喷嘴笔尖相对于默认高度的高度差，单位为MM。\n\n如果发现涂胶笔尖过高(接触不到）或过低(严重受压），可以通过调整该数值进行补偿。\n\n正值表示提高笔尖高度(使得笔尖远离模型)，负值表示降低笔尖高度(使得笔尖更接近模型)。\n", font=("SimHei",12))
                else:
                    tooltip_11= CTkToolTip(label_item, message="\nSet the height difference of the nozzle tip relative to the default height, in MM.\n\nIf you find that the gluing pen tip is too high (cannot reach) or too low (severely compressed), you can adjust this value for compensation.\n\nA positive value indicates raising the pen tip height (making the pen tip away from the model), and a negative value indicates lowering the pen tip height (making the pen tip closer to the model).\n",wraplength=550, font=("Segoe UI",12))
    # 如果是修改模式，填充数据
    if Mode == "Modify":
        # 修改模式，读取配置文件的数据
        for i, label in enumerate(labels):
            if label == "涂胶速度限制[MM/S]":
                entries[i].delete(0, "end")  # CTkEntry清空方式
                entries[i].insert(0, str(para.Max_Speed))
                
            if label == "X坐标补偿值[MM]":
                entries[i].delete(0, "end")
                entries[i].insert(0, str(round(para.X_Offset,2)))
                
            if label == "Y坐标补偿值[MM]":
                entries[i].delete(0, "end")
                # entries[i].insert(0, str(para.Y_Offset))
                entries[i].insert(0, str(round(para.Y_Offset,2)))
                
            if label == "喷嘴笔尖高度差[MM]":
                entries[i].delete(0, "end")
                # entries[i].insert(0, str(para.Z_Offset))
                entries[i].insert(0, str(round(para.Z_Offset,2)))
                
            if label == "自定义工具头获取 G-code":
                entries[i].delete("1.0", "end")  # CTkTextbox清空方式
                entries[i].insert("1.0", para.Custom_Mount_Gcode)
                
            if label == "自定义工具头收起 G-code":
                entries[i].delete("1.0", "end")
                entries[i].insert("1.0", para.Custom_Unmount_Gcode)

            if label=="额外干燥时间[秒]":
                entries[i].delete(0, "end")
                entries[i].insert(0, str(para.User_Dry_Time))
                # print("填充额外干燥时间为:", para.User_Dry_Time)

            if label=="支撑体挤出倍率":
                entries[i].delete(0, "end")
                entries[i].insert(0, str(para.Support_Extrusion_Multiplier))

        # 处理擦料塔坐标和速度
        if "擦料塔的起始点" in labels:
            entry_x.delete(0, "end")
            entry_y.delete(0, "end")
            entry_x.insert(0, str(para.Wiper_x))
            entry_y.insert(0, str(para.Wiper_y))
            
        if "擦料塔打印速度[MM/S]" in labels:
            entry_speed.delete(0, "end")
            entry_speed.insert(0, str(para.WipeTower_Print_Speed))


        # 处理复选框状态
        if para.Use_Wiping_Towers.get() == False:
            checkbox.deselect()
        if para.Nozzle_Cooling_Flag.get() == False:
            checkbox_cool.deselect()
        # if para.Iron_apply_Flag.get() == False:
        #     checkbox_iron.deselect()
    button_save_frame = ctk.CTkFrame(popup)
    button_save_frame.grid(row=len(labels), column=0, columnspan=2, pady=10, sticky="ew")
    button_save_frame.configure(fg_color="transparent")  # 设置背景透明
    # 另存按钮
    save_as_btn = ctk.CTkButton(
       button_save_frame, text="另存为", command=lambda: on_save_as(),
        corner_radius=10,font=("SimHei", 15)
    )
    def popup_safe_close():
        para.Unsafe_Close_Flag=True
        print("设置Unsafe_Close_Flag为True")
        popup.destroy()
    #取消按钮
    cancel_btn = ctk.CTkButton(
        button_save_frame, text="取消", command=lambda: popup_safe_close(),
        corner_radius=10,font=("SimHei", 15)
    )

    # 提交按钮
    submit_btn = ctk.CTkButton(
        button_save_frame, text="确定", command=lambda: on_submit(),
        corner_radius=10,font=("SimHei", 15)
    )
    if lang_setting=="EN":
        save_as_btn.configure(text="Save As")
        cancel_btn.configure(text="Cancel")
        submit_btn.configure(text="Submit")
        #调整按钮字体
        save_as_btn.configure(font=("Segoe UI",15))
        cancel_btn.configure(font=("Segoe UI",15))
        submit_btn.configure(font=("Segoe UI",15))

    if lang_setting=="EN":
        #调整label的文本
        popup.title("Configuration Wizard")
        labels_en = [
            "Max Gluing Speed [MM/S]", "X Coordinate Offset [MM]", "Y Coordinate Offset [MM]",
            "Nozzle Tip Height Offset [MM]", "Custom Toolhead Deploy G-code", "Custom Toolhead Stow G-code",
            "Use Wiping Towers Instead of Lollipops", "Wipe Tower Starting Point", "Wipe Tower Print Speed [MM/S]",
            "Force Thick Bridge Switch (BambuStudio Only)","Nozzle Cooling During Gluing","Additional Drying Time [Seconds]", "Support Extrusion Multiplier"
        ]
        for i, label in enumerate(labels_en):
            label_item = popup.grid_slaves(row=i, column=0)[0]
            label_item.configure(text=label + ":",font=("Segoe UI",12))
            #调整字体
        

    cancel_btn.pack(side="right", padx=(0, 10))
    submit_btn.pack(side="right", padx=(0, 5))
    save_as_btn.pack(side="right", padx=(0, 5))

    def on_save_as():
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
        if lang_setting!="EN":
            dialog = ctk.CTkInputDialog(title="新建预设", text="请输入新预设的名称:",font=("SimHei",15))
        else:
            dialog = ctk.CTkInputDialog(title="New Preset", text="Please enter the name of the new preset:",font=("SimHei",15))
        # dialog = ctk.CTkInputDialog(title="新建预设", text="请输入新预设的名称:",font=("SimHei",15))
        # dialog.iconbitmap(mkpicon_path)
        dialog.after(201, lambda: dialog.iconbitmap(mkpicon_path))
        dialog.geometry(CenterWindowToDisplay(dialog, 400, 150, dialog._get_window_scaling()))
        para.New_Preset_Name = dialog.get_input()
        if para.New_Preset_Name.strip() != "":
            #认为用户输入了有效名称，允许保存
            para.Unsafe_Close_Flag=False
        popup.destroy()  # 关闭弹窗

    def on_submit():
        #对于喷嘴笔尖高度差，如果用户输入<0，立即报警
        if labels[3] == "喷嘴笔尖高度差[MM]" or labels_en[3] == "Nozzle Tip Height Offset [MM]":
            try:
                z_offset_value = float(entries[3].get())
                if z_offset_value < 0:
                    ct=MKPMessagebox.show_info("输入错误", "喷嘴笔尖高度差不能为负值！请重新输入。")
                    return  # 阻止关闭窗口，等待用户修改输入
            except ValueError:
                ct=MKPMessagebox.show_info("输入错误", "喷嘴笔尖高度差必须是数字！请重新输入。")
                return
        para.Unsafe_Close_Flag=False
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
        if lang_setting=="EN":
            ct=MKPMessagebox.show_info("Exit", "Are you sure you want to exit?",["Cancel","Exit"])
        else:
            ct=MKPMessagebox.show_info("退出", "您真的要退出吗?",["取消","退出"])
        if ct == "退出" or ct == "Exit":
            para.Unsafe_Close_Flag=True#不能写！
            print("用户通过关闭按钮退出配置向导,设置Unsafe_Close_Flag为True")
            popup.destroy()
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
    para.WipeTower_Print_Speed = round(float(User_Input[8]), 3)
    para.User_Dry_Time = int(User_Input[9])
    para.Support_Extrusion_Multiplier = round(float(User_Input[10]), 3)
#这个函数用来从传入的filepath读取配置到para类中的变量
def read_toml_config(file_path):
    para.Use_Wiping_Towers = Tk_BooleanVar(value=False)
    para.Nozzle_Cooling_Flag = Tk_BooleanVar(value=False)
    para.Iron_apply_Flag = Tk_BooleanVar(value=False)
    para.Force_Thick_Bridge_Flag = Tk_BooleanVar(value=False)
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
        para.Use_Wiping_Towers.set(wiping_config['have_wiping_components'])
        # if para.Have_Wiping_Components.get()==True:
        para.Wiper_x = wiping_config['wiper_x']
        para.Wiper_y = wiping_config['wiper_y']
        para.WipeTower_Print_Speed = wiping_config['wipetower_speed']
        try:
            para.Nozzle_Cooling_Flag.set(wiping_config['nozzle_cooling_flag'])
        except:
            para.Nozzle_Cooling_Flag = Tk_BooleanVar(value=False)
        try:
            para.Iron_apply_Flag.set(wiping_config['iron_apply_flag'])
        except:
            para.Iron_apply_Flag = Tk_BooleanVar(value=False)
        try:
            para.User_Dry_Time = wiping_config['user_dry_time']
        except:
            para.User_Dry_Time = 0
        try:
            para.Force_Thick_Bridge_Flag.set(wiping_config['force_thick_bridge_flag'])
        except:
            para.Force_Thick_Bridge_Flag = Tk_BooleanVar(value=False)
        try:
            para.Support_Extrusion_Multiplier = wiping_config['support_extrusion_multiplier']
        except:
            para.Support_Extrusion_Multiplier = 1.0
#这个函数用来创建一个输入框，目前只是用来输入预设名称
def create_input_dialog(title, prompt):
    if lang_setting!="EN":
        dialog = ctk.CTkInputDialog(title="新建预设", text="请输入新预设的名称:",font=("SimHei",15))
    else:
        dialog = ctk.CTkInputDialog(title="New Preset", text="Please enter the name of the new preset:",font=("Segoe UI",15))
    new_preset_name = dialog.get_input()
    if new_preset_name:
        para.Preset_Name = new_preset_name
        mkpsupport_path = os.path.join(create_mkpsupport_dir(), f"{new_preset_name}.toml")
        get_preset_values("Normal")
        if para.Allow_Proceed_Flag == True:
            write_toml_config(mkpsupport_path)
       
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
        if para.Use_Wiping_Towers.get()==False:
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
        print("have_wiping_components = "+Use_wiper_str+"#使用擦嘴塔而非擦嘴组件Enable wiping components",file=f)
        print("wiper_x = "+str(para.Wiper_x),file=f)
        print("wiper_y = "+str(para.Wiper_y),file=f)
        print("wipetower_speed = " + str(para.WipeTower_Print_Speed) + " # 擦嘴塔打印速度Wipe tower print speed", file=f)
        print("nozzle_cooling_flag = " + str(para.Nozzle_Cooling_Flag.get()).lower() + " # 涂胶期间是否降温 Nozzle cooling during gluing", file=f)
        print("iron_apply_flag = " + str(para.Iron_apply_Flag.get()).lower() + " # 最小化涂胶区域 Ironing apply flag", file=f)
        print("user_dry_time = " + str(para.User_Dry_Time) + " # 额外干燥时间 User dry time (seconds)", file=f)
        print("force_thick_bridge_flag = " + str(para.Force_Thick_Bridge_Flag.get()).lower() + " # 强制厚桥开关 Force thick bridge flag", file=f)
        print("support_extrusion_multiplier = " + str(para.Support_Extrusion_Multiplier) + " # 支撑体挤出倍率 Support extrusion multiplier", file=f)
    if save_as_flag==True:
        refresh_preset_frame_list()
#这个函数用来创建一个弹窗，让用户点击按钮复制命令到剪贴板
def copy_user_command():
    root1 = ctk.CTk()
    root1.title('文件路径')
    root1.geometry(CenterWindowToDisplay(root1, 600, 169, root1._get_window_scaling()))
    root1.maxsize(600, 170)
    root1.minsize(600, 169)
    root1.after(201, lambda: root1.iconbitmap(mkpicon_path))
    def copy_curr_exe_path():
        root1.clipboard_clear()
        command = f'"{os.path.abspath(sys.executable)}" --Toml "{para.Preset_Name}" --Gcode'
        root1.clipboard_append(command)
        if lang_setting!="EN":
            MKPMessagebox.show_info("完成", "路径已复制到剪贴板。")
        else:
            MKPMessagebox.show_info("Done", "The path has been copied to the clipboard.")
        # MKPMessagebox.show_info("完成", "路径已复制到剪贴板。")
        # cs=CTkMessagebox(title='完成', message='路径已复制到剪贴板。',option_1="确定", icon='check',bg_color=("white","black"),fg_color=("#e1e6e9","#343638"),border_width=1,font=("SimHei",15),border_color=("#d1d1d1","#3a3a3a"))
        # cs.after(500, lambda: cs.destroy())
        # tk.messagebox.showinfo(title='完成', message='路径已复制。软件将自动关闭')
        # if cs.get() == "确定":
        #     # print("路径已复制到剪贴板。")
        #     cs.destroy()
        #     # root1.destroy()
        #     # exit(0)
    # 提示信息
    if lang_setting!="EN":
        message = '点击“复制”拷贝程序所在的路径，并粘贴入工艺->其他->后处理脚本框中。'
    else:
        message = 'Click "Copy" to copy the command and paste it into Process -> Others -> Post-processing script'
    # message = '点击“复制”拷贝程序所在的路径，并粘贴入工艺->其他->后处理脚本框中。'
    label = ctk.CTkLabel(root1, text=message, wraplength=550,justify='center', font=("SimHei", 15))
    if lang_setting=="EN":
        label.configure(font=("Segoe UI", 14))
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
    if lang_setting!="EN":
        copy_button.configure(text='复制')
    else:
        copy_button.configure(text='Copy',font=("Segoe UI", 15))
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
            if float(value) + x_offset<para.Machine_Min_X or float(value) + x_offset>para.Machine_Max_X:
                window.withdraw()  # 隐藏主窗口
                if lang_setting!="EN":
                    MKPMessagebox.show_info("警告", f"偏移后的X坐标:{float(values[key])+x_offset:.1f}mm超出机器允许的范围({para.Machine_Min_X}-{para.Machine_Max_X}mm)，请"+["向左","向右"][ float(value)+ x_offset<para.Machine_Min_X]+"调整模型位置",["我知道了"])
                else:
                    MKPMessagebox.show_info("Warning", f"The offset X coordinate: {float(values[key])+x_offset:.1f}mm exceeds the machine's allowed range ({para.Machine_Min_X}-{para.Machine_Max_X}mm). Please adjust the model position to the "+["left","right"][ float(value)+ x_offset<para.Machine_Min_X],["Got it"])
                exit(0)
        elif key == 'Y':
            values[key] = round(float(value) + y_offset, 3)
            if float(value) + y_offset<para.Machine_Min_Y or float(value) + y_offset>para.Machine_Max_Y:
                window.withdraw()  # 隐藏主窗口
                if lang_setting!="EN":
                    MKPMessagebox.show_info("警告", f"偏移后的Y坐标:{float(values[key])+y_offset:.1f}mm超出机器允许的范围({para.Machine_Min_Y}-{para.Machine_Max_Y}mm)，请"+["向前","向后"][ float(value)+ y_offset>para.Machine_Min_Y]+"调整模型位置",["我知道了"])
                else:   
                    MKPMessagebox.show_info("Warning", f"The offset Y coordinate: {float(values[key])+y_offset:.1f}mm exceeds the machine's allowed range ({para.Machine_Min_Y}-{para.Machine_Max_Y}mm). Please adjust the model position to the "+["front","back"][ float(value)+ y_offset>para.Machine_Min_Y],["Got it"])
                exit(0)
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

#这个函数输出伪随机数
# 预定义 1-9 的"伪随机"序列

index = 0

def get_pseudo_random():
    pseudo_random_table = [3, 7, 2, 8, 1, 5, 9, 4, 6]
    global index
    num = pseudo_random_table[index]
    index = (index + 1) % len(pseudo_random_table)
    strnum = str(num)
    return strnum

gcode = f"G1 X15 Y2{get_pseudo_random()}"
# print(gcode)  # 示例：G1 X15 Y23

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
        window.attributes("-topmost", False)  # 取消主窗口置顶
        window.withdraw()  # 隐藏主窗口
        ctk.set_appearance_mode("dark")
        #创建一个向导框
        guide_window=ctk.CTkToplevel(window)
        guide_window.title("新手向导")
        guide_window.geometry(CenterWindowToDisplay(guide_window, 550,270, guide_window._get_window_scaling()))
        guide_window.after(201, lambda: guide_window.iconbitmap(mkpicon_path))
        guide_window.attributes("-topmost", True)  # 置顶
        #实现上抄之前的三个图片点击选择的按钮，但是这次不是互斥的
        label_guide = ctk.CTkLabel(guide_window, text="当前本地无可用预设。请选择以下设备以继续:", font=("SimHei", 16))
        label_guide.pack(pady=10)
        mkpexecutable_dir = os.path.dirname(sys.executable)
        # mkpinternal_dir = os.path.join(mkpexecutable_dir, "_internal")
        mkpres_dir = os.path.join(mkpexecutable_dir, "resources")
        MKP_image_frame=ctk.CTkFrame(guide_window)
        MKP_image_frame.pack(pady=5,side="top")
        MKP_button_image_path = mkpres_dir
        button_states = {"P1": True, "P2": False, "A1M": False, "A1": False}  # True=未选中, False=选中
         #创建三个图片按钮：A1,A1M,P1/X1
        ######################################################################################
        P1_button=ctk.CTkButton(
            MKP_image_frame,
            text="",
            width=100,
            height=100,
            fg_color="#242424",
            hover_color="#404040",\
            border_width=2,
            compound="top",
            font=("SimHei", 12),
            border_color=("#404040"),
            image=ctk.CTkImage(Image.open(MKP_button_image_path + r"\P1.png"), size=(100, 100)),
        )
        P2_button=ctk.CTkButton(
            MKP_image_frame,
            text="",
            width=100,
            height=100,
            fg_color="#242424",
            hover_color="#404040",\
            border_width=2,
            compound="top",
            font=("SimHei", 12),
            border_color=("#404040"),
            image=ctk.CTkImage(Image.open(MKP_button_image_path + r"\P2.png"), size=(100, 100)),
        )
        A1_button=ctk.CTkButton(
            MKP_image_frame,
            text="",
            width=100,
            height=100,
            fg_color="#242424",
            hover_color="#404040",\
            border_width=2,
            compound="top",
            font=("SimHei", 12),
            border_color=("#404040"),
            image=ctk.CTkImage(Image.open(MKP_button_image_path + r"\A1.png"), size=(100, 100)),
        )
        A1M_button=ctk.CTkButton(
            MKP_image_frame,
            text="",
            width=100,
            height=100,
            fg_color="#242424",
            hover_color="#404040",\
            border_width=2,
            compound="top",
            font=("SimHei", 12),
            border_color=("#404040"),
            image=ctk.CTkImage(Image.open(MKP_button_image_path + r"\A1M.png"), size=(100, 100)),
        )
        def create_switch_handler(button, btn_type):
            # global current_selected
            def on_click():
                # 如果点击的是已选中的按钮，则取消选中
                if para.current_selected_preset == btn_type:
                    normal_path = os.path.join(MKP_button_image_path, f"{btn_type}.png")
                    normal_image = ctk.CTkImage(Image.open(normal_path), size=(100, 100))
                    button.configure(image=normal_image, fg_color="#242424")
                    button_states[btn_type] = False
                    para.current_selected_preset = None
                else:
                    # 取消之前选中的按钮
                    if para.current_selected_preset:
                        prev_type = para.current_selected_preset
                        prev_path = os.path.join(MKP_button_image_path, f"{prev_type}.png")
                        prev_image = ctk.CTkImage(Image.open(prev_path), size=(100, 100))
                        # 根据prev_type找到对应的按钮对象并重置
                        if prev_type == "P1":
                            P1_button.configure(image=prev_image, fg_color="#242424")
                        elif prev_type == "P2":
                            P2_button.configure(image=prev_image, fg_color="#242424")
                        elif prev_type == "A1M":
                            A1M_button.configure(image=prev_image, fg_color="#242424")
                        elif prev_type == "A1":
                            A1_button.configure(image=prev_image, fg_color="#242424")
                        button_states[prev_type] = False
                    # 选中当前按钮
                    selected_path = os.path.join(MKP_button_image_path, f"{btn_type}_selected.png")
                    selected_image = ctk.CTkImage(Image.open(selected_path), size=(100, 100))
                    button.configure(image=selected_image, fg_color="#404040")
                    button_states[btn_type] = True
                    para.current_selected_preset = btn_type
                    guide_window.update()
            return on_click
        P1_button.configure(command=create_switch_handler(P1_button,"P1"))
        A1M_button.configure(command=create_switch_handler(A1M_button,"A1M"))
        A1_button.configure(command=create_switch_handler(A1_button,"A1"))
        P2_button.configure(command=create_switch_handler(P2_button,"P2"))
        P1_button.pack(pady=5,padx=5,side="left")
        A1M_button.pack(pady=5,padx=5,side="left")
        A1_button.pack(pady=5,padx=5,side="left")
        P2_button.pack(pady=5,padx=5,side="left")
        P1_button.configure(image=ctk.CTkImage(Image.open(MKP_button_image_path + r"\P1_selected.png"), size=(100, 100)))
        button_frame_b=ctk.CTkFrame(guide_window)
        button_frame_b.configure(fg_color="transparent")
        button_frame_b.pack(fill="x",side="bottom")
        button_frame=ctk.CTkFrame(button_frame_b)
        button_frame.configure(fg_color="transparent")
        button_frame.pack(pady=10,padx=6,side="right")

        def on_guide_confirm():
            selected_preset = para.current_selected_preset
            #现在抄download_presets():来下载预设
            preset_files = ["A1.toml", "A1M.toml", "X1.toml", "P2.toml"]
            base_url = "https://gitee.com/Jhmodel/MKPSupport/raw/main/Presets/"
            downloaded_files = []
            #接下来不需要显示进度条，直接下载
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
            if selected_preset:
                filename = f"{selected_preset}.toml"
                if filename=="P1.toml":
                    filename="X1.toml"
                try:
                    url = base_url+filename
                    response = requests.get(url, stream=True)
                    response.raise_for_status()
                    
                    filepath = os.path.join(folder_path, filename)
                    with open(filepath, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    downloaded_files.append(filename)
                    # MKPMessagebox.show_info("下载完成", f"已下载: {filename}")
                    guide_window.attributes("-topmost", False)  # 取消置顶
                    para.current_selected_preset=selected_preset
                    guide_window.quit()
                    guide_window.destroy()
                    
                    #并且还需要下载BBS预设
                    def download_bbs_presets_for_new(selected_preset):
                        """
                        新手向导：首次下载BBS预设
                        selected_preset: "A1", "A1M", "P1" 中的一个
                        """
                        # 1. 找到user下的所有不含"default"的文件夹
                        appdata_path = os.getenv("APPDATA")
                        bbs_user_path = os.path.join(appdata_path, "BambuStudio", "user")
                        
                        if not os.path.exists(bbs_user_path):
                            print("❌ BambuStudio user 文件夹不存在")
                            return False
                        
                        # 遍历查找所有不含default的文件夹
                        target_folders = []
                        for folder in os.listdir(bbs_user_path):
                            folder_path = os.path.join(bbs_user_path, folder)
                            if os.path.isdir(folder_path) and "default" not in folder.lower():
                                target_folders.append(folder)
                        
                        if not target_folders:
                            print("❌ 未找到任何有效的用户文件夹")
                            return False
                        
                        print(f"✅ 找到 {len(target_folders)} 个用户文件夹")
                        
                        # 2. 基础URL
                        base_url = "https://gitee.com/Jhmodel/MKPSupport/raw/main/BBS_Presets/"
                        
                        # 3. 根据selected_preset决定下载哪些机型
                        machines_to_download = []
                        
                        if selected_preset == "A1":
                            machines_to_download = ["A1"]
                        elif selected_preset == "A1M":
                            machines_to_download = ["A1 mini"]
                        elif selected_preset == "P1":
                            machines_to_download = ["P1", "X1"]  # P1同时下载X1
                        elif selected_preset == "P2":
                            machines_to_download = ["P2"]
                        
                        # 机型映射表
                        machine_mapping = {
                            "A1 mini": {
                                "support": "MKPSupport A1 mini.json",
                                "process": "MKPProcess A1 mini.json"
                            },
                            "A1": {
                                "support": "MKPSupport A1.json",
                                "process": "MKPProcess A1.json"
                            },
                            "X1": {
                                "support": "MKPSupport X1.json",
                                "process": "MKPProcess X1.json"
                            },
                            "P1": {
                                "support": "MKPSupport P1S.json",
                                "process": "MKPProcess P1S.json"
                            },
                            "P2": {
                                "support": "MKPSupport P2.json",
                                "process": "MKPProcess P2.json"
                            }
                        }
                        
                        # 4. 为每个用户文件夹下载文件
                        success_count = 0
                        for folder_name in target_folders:
                            bbs_path = os.path.join(bbs_user_path, folder_name)
                            print(f"\n📁 处理用户文件夹: {folder_name}")
                            
                            folder_success = True
                            
                            # 确保目录存在
                            machine_dir = os.path.join(bbs_path, "machine")
                            process_dir = os.path.join(bbs_path, "process")
                            os.makedirs(machine_dir, exist_ok=True)
                            os.makedirs(process_dir, exist_ok=True)
                            
                            def get_remote_file_content(url):
                                """获取远程文件内容"""
                                try:
                                    response = requests.get(url)
                                    if response.status_code == 200:
                                        return response.content.decode('utf-8')
                                    return None
                                except Exception as e:
                                    print(f"❌ 下载失败: {e}")
                                    return None
                            
                            # 下载文件
                            for machine_name in machines_to_download:
                                machine = machine_mapping[machine_name]
                                
                                # 下载support文件
                                support_url = base_url + machine["support"]
                                support_local = os.path.join(machine_dir, machine["support"])
                                support_content = get_remote_file_content(support_url)
                                if support_content:
                                    try:
                                        with open(support_local, 'w', encoding='utf-8') as f:
                                            f.write(support_content)
                                        print(f"  ✅ 已下载: {machine['support']}")
                                    except Exception as e:
                                        print(f"  ❌ 保存失败 {machine['support']}: {e}")
                                        folder_success = False
                                else:
                                    print(f"  ❌ 下载失败: {machine['support']}")
                                    folder_success = False
                                
                                # 下载process文件
                                process_url = base_url + machine["process"]
                                process_local = os.path.join(process_dir, machine["process"])
                                process_content = get_remote_file_content(process_url)
                                if process_content:
                                    try:
                                        with open(process_local, 'w', encoding='utf-8') as f:
                                            f.write(process_content)
                                        print(f"  ✅ 已下载: {machine['process']}")
                                    except Exception as e:
                                        print(f"  ❌ 保存失败 {machine['process']}: {e}")
                                        folder_success = False
                                else:
                                    print(f"  ❌ 下载失败: {machine['process']}")
                                    folder_success = False
                            
                            if folder_success:
                                success_count += 1
                        
                        # 返回结果
                        if success_count == len(target_folders):
                            print(f"\n🎉 所有 {success_count} 个用户文件夹都成功更新！")
                            return True
                        elif success_count > 0:
                            print(f"\n⚠️ 部分成功: {success_count}/{len(target_folders)} 个文件夹更新成功")
                            return True  # 仍然返回True，因为至少部分成功了
                        else:
                            print(f"\n❌ 所有文件夹都更新失败")
                            return False
                    download_bbs_presets_for_new(selected_preset)
                    return downloaded_files
                except Exception as e:
                    MKPMessagebox.show_info("下载失败", f"下载{filename}失败: {str(e)}")
            else:
                MKPMessagebox.show_info("未选择机型", "请至少选择一个机型以继续。")
        confirm_button=ctk.CTkButton(
            button_frame,
            text="确认",
            width=100,
            height=30,
            fg_color="#4CAF50",
            hover_color="#45a049",
            font=("SimHei", 15),
            command=on_guide_confirm
        )
        confirm_button.pack(pady=5,side="left",padx=10)
        def on_cancel():
            exit(0)
        cancel_button=ctk.CTkButton(
            button_frame,
            text="取消",
            width=100,
            height=30,
            fg_color="#f44336",
            hover_color="#da190b",
            font=("SimHei", 15),
            command=on_cancel
        )
        cancel_button.pack(pady=5,side="right",padx=10)
        def on_guide_closing():
            guide_window.quit()
            guide_window.attributes("-topmost", False)
            guide_window.destroy()

        guide_window.protocol("WM_DELETE_WINDOW", lambda: on_guide_closing())
        guide_window.mainloop()

    #创建主窗口
    print("Creating main window")
    global selection_dialog,local_version
    window.attributes("-topmost", False)  # 取消主窗口置顶
    ctk.set_appearance_mode("dark")  # 设置为暗黑模式
    selection_dialog = ctk.CTkToplevel(window)
    selection_dialog.attributes("-alpha", 0.1)  # 设置窗口透明度为98%
    # selection_dialog.resizable(0,0)
    
    selection_dialog.title(local_version)
    selection_dialog.iconbitmap(mkpicon_path)
    selection_dialog.after(201, lambda :selection_dialog.iconbitmap(mkpicon_path))  # 解决某些系统图标不显示的问题
    selection_dialog.geometry(CenterWindowToDisplay(selection_dialog, 550, 420, selection_dialog._get_window_scaling()))
    selection_dialog.maxsize(600, 500)
    selection_dialog.minsize(550, 420)
    selection_dialog.configure(fg_color=("#f1f2f3", "#242424"),bg_color=("#f1f2f3", "#242424"))
    window.withdraw()  # 隐藏主窗口
    def on_closing():
        os._exit(0)  # 直接退出程序
    selection_dialog.protocol("WM_DELETE_WINDOW", on_closing)
    ctk.set_default_color_theme("green")

    ######################################################################################
    #从resources文件夹加载mkp_config.toml,其中记载了上一次选择的预设的名称
    mkpexecutable_dir = os.path.dirname(sys.executable)
    mkpinternal_dir = os.path.join(mkpexecutable_dir, "resources")
    mkp_config_path = os.path.join(os.path.join(os.path.expanduser("~/Documents"), "MKPSupport"), "Data","mkp_config.toml") 
    mkp_config_last_selected_preset = ""
    if os.path.exists(mkp_config_path):
        with open(mkp_config_path, 'r', encoding='utf-8') as f:
            try:
                config = toml.load(f)
            except:
                config = {}
        try:
            mkp_config_last_selected_preset = config['last_selected_preset']
            # para.current_selected_preset = config['last_selected_preset']
            if mkp_config_last_selected_preset!="" and Have_Toml_Flag==True:
                #根据读取到的预设名称中含有的关键词来设置current_selected_preset
                if mkp_config_last_selected_preset.find("A1M") != -1:
                    para.current_selected_preset = "A1M"

                elif mkp_config_last_selected_preset.find("A1") != -1 and mkp_config_last_selected_preset.find("A1M") == -1:
                    para.current_selected_preset = "A1"

                elif mkp_config_last_selected_preset.find("P1") != -1 or mkp_config_last_selected_preset.find("X1") != -1:
                    para.current_selected_preset = "P1"
                elif mkp_config_last_selected_preset.find("P2") != -1:
                    para.current_selected_preset = "P2"
        
        except:
            para.current_selected_preset = "P1"
    ######################################################################################
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
        if lang_setting=="EN":
            tabview._segmented_button.configure(
                font=ctk.CTkFont(
                    family="Segoe UI",  # 设置字体为黑体
                    size=11,
                    weight="bold"  # 设置加粗
                )
            )
        # 添加两个选项卡（第二个选项卡预留空位）
        preset_manager_text="预设管理"
        if lang_setting=="EN":
            preset_manager_text="START"
        download_text="下载管理"
        if lang_setting=="EN":
            download_text="DOWNLOAD"
        cali_text="自动校准"
        if lang_setting=="EN":
            cali_text="CALIBE"
        tabview.add(preset_manager_text)  # 原有功能放在这里
        tabview.add(download_text)  # 留空，后续由你自行实现
        tabview.add(cali_text)  
        preset_frame = ctk.CTkFrame(tabview.tab(preset_manager_text),fg_color=("#f1f2f3", "#242424"),bg_color=("#f1f2f3", "#242424"))
        preset_frame.pack(fill="both", expand=True)

        MKP_image_frame=ctk.CTkFrame(preset_frame,fg_color="transparent",bg_color="transparent")
        #居中MKP_image_frame:CENTER
        MKP_image_frame.pack(side="top",fill="x",expand=False)
        # MKP_button_image_path = r"C:\Users\Administrator\Desktop\Bamboo version\resources"
        mkpres_dir = os.path.join(mkpexecutable_dir, "resources")
        MKP_button_image_path=mkpres_dir
        button_states = {"P1": False,"P2": False, "A1M": False, "A1": False}  # True=未选中, False=选中

        # 根据当前选中的预设更新按钮状态
        if para.current_selected_preset=="P1":
            button_states["P1"] = True
        elif para.current_selected_preset=="A1M":
            button_states["A1M"] = True
        elif para.current_selected_preset=="A1":
            button_states["A1"] = True
        elif para.current_selected_preset=="P2":
            button_states["P2"] = True
        
        def create_switch_handler(button, btn_type):
            # global current_selected
            def on_click():
                # 如果点击的是已选中的按钮，则取消选中
                if para.current_selected_preset == btn_type:
                    normal_path = os.path.join(MKP_button_image_path, f"{btn_type}.png")
                    normal_image = ctk.CTkImage(Image.open(normal_path), size=(100, 100))
                    button.configure(image=normal_image, fg_color="#242424")
                    button_states[btn_type] = False
                    para.current_selected_preset = None
                else:
                    # 取消之前选中的按钮
                    if para.current_selected_preset:
                        prev_type = para.current_selected_preset
                        prev_path = os.path.join(MKP_button_image_path, f"{prev_type}.png")
                        prev_image = ctk.CTkImage(Image.open(prev_path), size=(100, 100))
                        # 根据prev_type找到对应的按钮对象并重置
                        if prev_type == "P1":
                            P1_button.configure(image=prev_image, fg_color="#242424")
                        elif prev_type == "A1M":
                            A1M_button.configure(image=prev_image, fg_color="#242424")
                        elif prev_type == "A1":
                            A1_button.configure(image=prev_image, fg_color="#242424")
                        elif prev_type == "P2":
                            P2_button.configure(image=prev_image, fg_color="#242424")
                        button_states[prev_type] = False
                    # 选中当前按钮
                    selected_path = os.path.join(MKP_button_image_path, f"{btn_type}_selected.png")
                    selected_image = ctk.CTkImage(Image.open(selected_path), size=(100, 100))
                    button.configure(image=selected_image, fg_color="#404040")
                    button_states[btn_type] = True
                    para.current_selected_preset = btn_type
                scroll_frame_label.configure(text=f"{"P1" if button_states["P1"] else ''}{"P2" if button_states["P2"] else ''}{'A1M' if button_states['A1M'] else ''}{'A1' if button_states['A1'] else ''}  {scroll_frame_label_text}")
                refresh_preset_frame_list()
                selection_dialog.update()
            return on_click

        #创建三个图片按钮：A1,A1M,P1/X1
        ######################################################################################
        P1_button=ctk.CTkButton(
            MKP_image_frame,
            text="",
            width=100,
            height=100,
            fg_color="#242424",
            hover_color="#404040",\
            border_width=2,
            compound="top",
            font=("SimHei", 12),
            border_color=("#404040"),
            image=ctk.CTkImage(Image.open(MKP_button_image_path + r"\P1.png"), size=(100, 100)),
        )
        P2_button=ctk.CTkButton(
            MKP_image_frame,
            text="",
            width=100,
            height=100,
            fg_color="#242424",
            hover_color="#404040",\
            border_width=2,
            compound="top",
            font=("SimHei", 12),
            border_color=("#404040"),
            image=ctk.CTkImage(Image.open(MKP_button_image_path + r"\P2.png"), size=(100, 100)),
        )
        A1_button=ctk.CTkButton(
            MKP_image_frame,
            text="",
            width=100,
            height=100,
            fg_color="#242424",
            hover_color="#404040",\
            border_width=2,
            compound="top",
            font=("SimHei", 12),
            border_color=("#404040"),
            image=ctk.CTkImage(Image.open(MKP_button_image_path + r"\A1.png"), size=(100, 100)),
        )
        A1M_button=ctk.CTkButton(
            MKP_image_frame,
            text="",
            width=100,
            height=100,
            fg_color="#242424",
            hover_color="#404040",\
            border_width=2,
            compound="top",
            font=("SimHei", 12),
            border_color=("#404040"),
            image=ctk.CTkImage(Image.open(MKP_button_image_path + r"\A1M.png"), size=(100, 100)),
        )
        P1_button.configure(command=create_switch_handler(P1_button,"P1"))
        P2_button.configure(command=create_switch_handler(P2_button,"P2"))  
        A1M_button.configure(command=create_switch_handler(A1M_button,"A1M"))
        A1_button.configure(command=create_switch_handler(A1_button,"A1"))
        P1_button.pack(pady=5,padx=5,side="left")
        P2_button.pack(pady=5,padx=5,side="left")
        A1M_button.pack(pady=5,padx=5,side="left")
        A1_button.pack(pady=5,padx=5,side="left")

        if para.current_selected_preset=="P1":
            P1_button.configure(image=ctk.CTkImage(Image.open(MKP_button_image_path + r"\P1_selected.png"), size=(100, 100)), fg_color="#404040")
        elif para.current_selected_preset=="A1M":
            A1M_button.configure(image=ctk.CTkImage(Image.open(MKP_button_image_path + r"\A1M_selected.png"), size=(100, 100)), fg_color="#404040")
        elif para.current_selected_preset=="A1":
            A1_button.configure(image=ctk.CTkImage(Image.open(MKP_button_image_path + r"\A1_selected.png"), size=(100, 100)), fg_color="#404040")
        elif para.current_selected_preset=="P2":
            P2_button.configure(image=ctk.CTkImage(Image.open(MKP_button_image_path + r"\P2_selected.png"), size=(100, 100)), fg_color="#404040")
        # 创建滚动区域框架
        scroll_frame_label_text="预设列表"
        if lang_setting=="EN":
            scroll_frame_label_text="Preset List"
        #创建标签：？的预设列表，？来自当前为True的button_states
        print( button_states)
        scroll_frame_label = ctk.CTkLabel(
            preset_frame,
            text=f"{"P1" if button_states["P1"] else ''}{'A1M' if button_states['A1M'] else ''}{'A1' if button_states['A1'] else ''} {scroll_frame_label_text}",
            font=("SimHei", 12),
            anchor="w"
        )
        if lang_setting=="EN":
            scroll_frame_label.configure(font=("Segoe UI", 12))
        scroll_frame_label.pack(side='top',padx=10,fill='x')
        scroll_constraints_frame=ctk.CTkFrame(preset_frame,fg_color="transparent",bg_color="transparent",height=100)
        scroll_constraints_frame.pack(fill='x',expand=False,side='top')
        scroll_constraints_frame.pack_propagate(False)
        scroll_frame = ctk.CTkScrollableFrame(scroll_constraints_frame,fg_color=("#f1f2f3", "#262626"),bg_color=("#f1f2f3", "#242424"),height=100)
        scroll_frame.configure(border_width=1, border_color=("#d1d1d1", "#3a3a3a"))
        scroll_frame.pack(fill='x',expand=False, side='top',padx=10,pady=0)
        #需要限制scroll_frame的高度，否则预设文件过多时会撑大窗口
        # scroll_frame.pack_propagate(False)
        # preset_frame.pack_propagate(False)
        # 添加单选按钮
        toml_files = [f for f in os.listdir(folder_path) if f.endswith('.toml')]
        #对toml_files进行筛选:只保留与当前选中机型对应的预设文件
        if para.current_selected_preset=="P1":
            # toml_files = [f for f in toml_files if f.lower().startswith("x1") or f.lower().startswith("p1")]
            #这种方法并不够failsafe，因为用户可能会把预设文件改名。预设文件里有;A1,;A1M之类的注释，对于名字里没有机型标识的预设文件需要读取内容来判断。这个注释的位置在文件中间
            toml_files = [f for f in toml_files if f.lower().startswith("x1") or f.lower().startswith("p1")]
            for f in os.listdir(folder_path):
                if f.endswith('.toml') and f not in toml_files and f.lower().startswith("a1")==False:
                    #读取文件内容，判断是否含有;P1或;X1注释
                    filePath = os.path.join(folder_path, f)
                    try:
                        with open(filePath, 'r', encoding='utf-8') as file:
                            content = file.read()
                            if ";P1" in content or ";X1" in content:
                                toml_files.append(f)
                    except:
                        pass
        elif para.current_selected_preset=="A1M":
            toml_files = [f for f in toml_files if f.lower().startswith("a1m")]
            for f in os.listdir(folder_path):
                if f.endswith('.toml') and f not in toml_files:
                    #读取文件内容，判断是否含有;A1M注释
                    filePath = os.path.join(folder_path, f)
                    try:
                        with open(filePath, 'r', encoding='utf-8') as file:
                            content = file.read()
                            if ";A1M" in content:
                                toml_files.append(f)
                    except:
                        pass
        elif para.current_selected_preset=="A1":
            toml_files = [f for f in toml_files if f.lower().startswith("a1") and not f.lower().startswith("a1m")]
            for f in os.listdir(folder_path):
                if f.endswith('.toml') and f not in toml_files and f.lower().startswith("x1")==False and f.lower().startswith("p1")==False:
                    #读取文件内容，判断是否含有;A1注释
                    filePath = os.path.join(folder_path, f)
                    try:
                        with open(filePath, 'r', encoding='utf-8') as file:
                            content = file.read()
                            if ";A1" in content and ";A1M" not in content:
                                toml_files.append(f)
                    except:
                        pass
        elif para.current_selected_preset=="P2":
            toml_files = [f for f in toml_files if f.lower().startswith("p2")]
            for f in os.listdir(folder_path):
                if f.endswith('.toml') and f not in toml_files:
                    #读取文件内容，判断是否含有;P2注释
                    filePath = os.path.join(folder_path, f)
                    try:
                        with open(filePath, 'r', encoding='utf-8') as file:
                            content = file.read()
                            if ";P2" in content:
                                toml_files.append(f)
                    except:
                        pass
        #如果列表是空的，做一个label
        if not toml_files:
            no_preset_text="无可用预设文件--请下载MKP预设"
            if lang_setting=="EN":
                no_preset_text="No available preset files--Please download MKP presets"
            ctk.CTkLabel(
                scroll_frame,
                text=no_preset_text,
                font=("SimHei", 12),
                anchor="center"
            ).pack(pady=20)
                
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
            radio_button.pack(anchor='w', pady=5,padx=10)
            radio_buttons.append(radio_button)
        
        # selected_toml.set(toml_file_paths[0])
        # radio_buttons[0].select()
        # 设置默认选择
        
        if toml_file_paths:
            # 从mkp_last_selected_preset变量中读取上次选择的预设文件名，并设置为默认选中项
            if mkp_config_last_selected_preset!="":
                # pre_name=mkp_config_last_selected_preset.strip(".toml")
                #pre_name是删除了.toml与前面的文件夹层级的纯预设名称
                pre_name=os.path.basename(mkp_config_last_selected_preset)
                print(pre_name)
                for i, path in enumerate(toml_file_paths):
                    print("Range:"+os.path.basename(path))
                    if os.path.basename(path)==pre_name:
                        selected_toml.set(path)
                        radio_buttons[i].select()
                        break

            elif para.current_selected_preset!="":
                #根据current_selected_preset来尝试设置默认选中项
                for i, path in enumerate(toml_file_paths):
                    if para.current_selected_preset=="P1":
                        if os.path.basename(path).lower().startswith("x1") or os.path.basename(path).lower().startswith("p1"):
                            selected_toml.set(path)
                            radio_buttons[i].select()
                            break
                    elif para.current_selected_preset=="A1M":
                        if os.path.basename(path).lower().startswith("a1m"):
                            selected_toml.set(path)
                            radio_buttons[i].select()
                            break
                    elif para.current_selected_preset=="A1":
                        if os.path.basename(path).lower().startswith("a1") and not os.path.basename(path).lower().startswith("a1m"):
                            selected_toml.set(path)
                            radio_buttons[i].select()
                            break
          
        global refresh_preset_frame_list
        def refresh_preset_frame_list():
            """刷新预设列表的最快实现（适用于少量项目）"""
            #0.复位滚动条
            canvas = scroll_frame._parent_canvas  # CTkScrollableFrame的内部画布
    
            # 方法A：设置滚动位置为顶部
            canvas.yview_moveto(0.0)  # 0.0 = 顶部, 1.0 = 底部
            # scroll_frame.canvas.yview_moveto(0)  # 移动到最顶部 (0%)
            # 1. 清空现有单选按钮
            for widget in scroll_frame.winfo_children():
                widget.destroy()  # 直接销毁所有子部件
            # 2. 重新加载文件列表
            toml_files = [f for f in os.listdir(folder_path) if f.endswith('.toml')]
            # 对toml_files进行筛选:只保留与当前选中机型对应的预设文件
            if para.current_selected_preset=="P1":
                toml_files = [f for f in toml_files if f.lower().startswith("x1") or f.lower().startswith("p1")]
                for f in os.listdir(folder_path):
                    if f.endswith('.toml') and f not in toml_files and f.lower().startswith("a1")==False:
                        # 读取文件内容，判断是否含有;P1或;X1注释
                        filePath = os.path.join(folder_path, f)
                        try:
                            with open(filePath, 'r', encoding='utf-8') as file:
                                content = file.read()
                                if ";P1" in content or ";X1" in content:
                                    toml_files.append(f)
                        except:
                            pass
            elif para.current_selected_preset=="A1M":
                toml_files = [f for f in toml_files if f.lower().startswith("a1m")]
                for f in os.listdir(folder_path):
                    if f.endswith('.toml') and f not in toml_files:
                        # 读取文件内容，判断是否含有;A1M注释
                        filePath = os.path.join(folder_path, f)
                        try:
                            with open(filePath, 'r', encoding='utf-8') as file:
                                content = file.read()
                                if ";A1M" in content:
                                    toml_files.append(f)
                        except:
                            pass
            elif para.current_selected_preset=="A1":
                toml_files = [f for f in toml_files if f.lower().startswith("a1") and not f.lower().startswith("a1m")]
                for f in os.listdir(folder_path):
                    if f.endswith('.toml') and f not in toml_files and f.lower().startswith("x1")==False and f.lower().startswith("p1")==False:
                        # 读取文件内容，判断是否含有;A1注释
                        filePath = os.path.join(folder_path, f)
                        try:
                            with open(filePath, 'r', encoding='utf-8') as file:
                                content = file.read()
                                if ";A1" in content and ";A1M" not in content:
                                    toml_files.append(f)
                        except:
                            pass
            elif para.current_selected_preset=="P2":
                toml_files = [f for f in toml_files if f.lower().startswith("p2")]
                for f in os.listdir(folder_path):
                    if f.endswith('.toml') and f not in toml_files:
                        # 读取文件内容，判断是否含有;P2注释
                        filePath = os.path.join(folder_path, f)
                        try:
                            with open(filePath, 'r', encoding='utf-8') as file:
                                content = file.read()
                                if ";P2" in content:
                                    toml_files.append(f)
                        except:
                            pass
            
            #如果列表是空的，做一个label
            if not toml_files:
                no_preset_text="无可用预设文件--请下载MKP预设"
                if lang_setting=="EN":
                    no_preset_text="No available preset files--Please download MKP presets"
                ctk.CTkLabel(
                    scroll_frame,
                    text=no_preset_text,
                    font=("SimHei", 12),
                    anchor="center"
                ).pack(pady=20)
                return
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
                ).pack(anchor='w', pady=5,padx=10)

            # 4. 默认选中第一个（如果存在）
            if toml_file_paths:
                try:
                    selected_toml.set(toml_file_paths[0])
                    radio_buttons[0].select()
                except:
                    pass
                        
        hyperlink_frame_and_buttons_frame=ctk.CTkFrame(preset_frame, fg_color="transparent", bg_color="transparent")
        hyperlink_frame_and_buttons_frame.pack(side='bottom', fill='x', pady=(0, 10), padx=10)

        # ===== 新增代码：黑色超链接（点击变浅灰） =====
        hyperlink_frame = ctk.CTkFrame(hyperlink_frame_and_buttons_frame, fg_color="transparent", bg_color="transparent")
        hyperlink_frame.pack(side='top', fill='x', pady=(0, 10), padx=10)

        # 项目主页超链接
        def on_project_click(event):
            import webbrowser
            webbrowser.open("https://gitee.com/Jhmodel/MKPSupport")  # 替换为实际链接
            # event.widget.configure(text_color="#a0a0a0")  # 点击后变浅灰

        project_link_text="项目主页"
        if lang_setting=="EN":
            project_link_text="Project Home"
        project_link = ctk.CTkLabel(
            hyperlink_frame,
            # text="项目主页",
            text=project_link_text,
            text_color=("black", "white"),  # 亮色主题黑字，暗色主题白字
            cursor="hand2",
            font=("SimHei", 12, "underline")
        )
        if lang_setting=="EN":
            project_link.configure(font=("Segoe UI", 12, "underline"))
        project_link.pack(side='left', padx=(0, 20))
        project_link.bind("<Button-1>", on_project_click)

        # 视频教程超链接
        def on_tutorial_click(event):
            import webbrowser
            webbrowser.open("https://www.bilibili.com/video/BV1fhNFzfEp4/")  # 替换为实际链接
            # event.widget.configure(text_color="#a0a0a0")  # 点击后变浅灰
        video_tutorial_text="视频教程"
        if lang_setting=="EN":
            video_tutorial_text="Video Tutorial"
        
        tutorial_link = ctk.CTkLabel(
            hyperlink_frame,
            # text="视频教程",
            text=video_tutorial_text,
            text_color=("black", "white"),
            cursor="hand2",
            font=("SimHei", 12, "underline")
        )
        if lang_setting=="EN":
            tutorial_link.configure(font=("Segoe UI", 12, "underline"))
        tutorial_link.pack(side='left')
        tutorial_link.bind("<Button-1>", on_tutorial_click)

        #ChangeLog超链接
        def on_changelog_click(event):
            #调用show_change_log()
            change_log_url = "https://gitee.com/Jhmodel/MKPSupport/raw/main/changelog.md"
            change_log_path=os.path.join(os.path.join(os.path.expanduser("~/Documents"), "MKPSupport"), "Data", "changelog.md")
            local_change_log = ""
            with open(change_log_path, "r", encoding="utf-8") as f:
                local_change_log = f.read()
            try:
                response = requests.get(change_log_url, stream=True, verify=False)
                if response.status_code == 200:
                    content = response.text  # 将文件内容加载到内存
                    # print("Remote Change Log:", content)
                    #检本地行数==远程行数？
                    if content.count("\n") != local_change_log.count("\n"):#不等，说明远程有新东西
                        print("远程有"+str(content.count("\n"))+"行新内容")
                        print("本地内容行数："+str(local_change_log.count("\n")))
                    # if local_change_log.find(content) == -1:#没有，说明远程有新东西
                    #写入本地
                        with open(change_log_path, "w", encoding="utf-8", newline='\n') as f:
                            f.write(content)
                        show_change_log(content.replace(local_change_log, ""))

                else:
                    print(f"请求失败，状态码：{response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"请求失败，原因：{e}")
            show_change_log(content)
        change_log_text="更新日志"
        if lang_setting=="EN":
            change_log_text="Change Log"
        change_log_link = ctk.CTkLabel(
            hyperlink_frame,
            # text="更新日志",
            text=change_log_text,
            text_color=("black", "white"),
            cursor="hand2",
            font=("SimHei", 12, "underline")
        )
        if lang_setting=="EN":
            change_log_link.configure(font=("Segoe UI", 12, "underline"))
        change_log_link.pack(side='left', padx=(20, 0))
        change_log_link.bind("<Button-1>", on_changelog_click)
        # ===== 新增代码结束 =====
        auto_update_text="自动更新"
        if lang_setting=="EN":
            auto_update_text="Auto Update"
        auto_update_link = ctk.CTkLabel(
            hyperlink_frame,
            # text="自动更新",
            text=auto_update_text,
            text_color=("black", "white"),
            cursor="hand2",
            font=("SimHei", 12, "underline")
        )
        if lang_setting=="EN":
            auto_update_link.configure(font=("Segoe UI", 12, "underline"))
        auto_update_link.pack(side='left', padx=(20, 0))
        
        def on_auto_update_click(event):
            #做一个对话框，
            auto_update_popup = ctk.CTkToplevel(hyperlink_frame)
            auto_update_popup.withdraw()
            auto_update_popup.title(auto_update_text)
            auto_update_popup.after(201, lambda: auto_update_popup.iconbitmap(mkpicon_path))
            auto_update_popup.attributes("-topmost", True)
            auto_update_popup.geometry(CenterWindowToDisplay(auto_update_popup, 300, 150,auto_update_popup._get_window_scaling()))
            # auto_update_popup重新显示
            auto_update_popup.deiconify()
           # 里面有两个复选框，一个是程序本体的自动更新，一个是配置文件的自动更新
            
            auto_update_checkbox = ctk.CTkCheckBox(
                auto_update_popup,
                text="程序本体自动更新",
                font=("SimHei", 12)
            )
            if lang_setting=="EN":
                auto_update_checkbox.configure(text="Program Auto Update")
            auto_update_checkbox.pack(pady=15, padx=10)  # 添加 padx=10

            config_update_checkbox = ctk.CTkCheckBox(
                auto_update_popup,
                text="配置文件自动更新",
                font=("SimHei", 12)
            )
            if lang_setting=="EN":
                config_update_checkbox.configure(text="Configs Auto Update")
            config_update_checkbox.pack(pady=5, padx=10)  # 添加 padx=10

            def on_auto_update_confirm(auto_update, config_update):
                # 处理确认逻辑
                print(f"自动更新程序：{auto_update}")
                print(f"自动更新配置文件：{config_update}")

                config_path = os.path.join(os.path.join(os.path.expanduser("~/Documents"), "MKPSupport"), "Data","mkp_config.toml")
                with open(config_path, "r", encoding="utf-8") as f:
                    config = toml.load(f)
                try:
                    config["auto_update"]["program"] = auto_update
                    config["auto_update"]["config"] = config_update
                except:
                    #没有这两个键，就添加
                    config["auto_update"] = {}
                    config["auto_update"]["program"] = auto_update
                    config["auto_update"]["config"] = config_update
                with open(config_path, "w", encoding="utf-8") as f:
                    toml.dump(config, f)
                auto_update_popup.destroy()
            # 一个确认按钮
            confirm_button = ctk.CTkButton(
                auto_update_popup,
                text="确认",
                font=("SimHei", 12),
                command=lambda: on_auto_update_confirm(
                    auto_update_checkbox.get(),
                    config_update_checkbox.get()
                )
            )
            if lang_setting=="EN":
                confirm_button.configure(text="CONFIRM")
            confirm_button.pack(pady=10, padx=10)  # 添加 padx=10
        
            #检查本地的情况。如果本地的toml显示用户选择要更新，就把复选框勾选上
            #读取本地的toml文件，检查是否有自动更新设置
            config_path = os.path.join(os.path.join(os.path.expanduser("~/Documents"), "MKPSupport"), "Data","mkp_config.toml")
            config = toml.load(config_path)
            program_auto_update = config.get("auto_update", {}).get("program", False)
            config_auto_update = config.get("auto_update", {}).get("config", False)

            if program_auto_update:
                auto_update_checkbox.select()
            if config_auto_update:
                config_update_checkbox.select()
        auto_update_link.bind("<Button-1>", on_auto_update_click)
        ######################################################################################
        assign_text="指定"
        if lang_setting=="EN":
            assign_text="APPLY"
        new_text="新建"
        if lang_setting=="EN":
            new_text="NEW"
        edit_text="编辑"
        if lang_setting=="EN":
            edit_text="EDIT"
        delete_text="删除"
        if lang_setting=="EN":
            delete_text="DELETE"
        # 创建底部按钮框架
        button_frame = ctk.CTkFrame(hyperlink_frame_and_buttons_frame,fg_color=("#f1f2f3", "#242424"),bg_color=("#f1f2f3", "#242424"))
        button_frame.pack(side='bottom', fill='x', pady=(0, 10), padx=10)
        button_bold_font = ctk.CTkFont(
            family="SimHei",  # 设置字体为黑体
            size=15,
            weight="bold"  # 设置加粗
        )
        # 创建按钮 - 使用grid布局
        confirm_button = ctk.CTkButton(
            button_frame, 
            # text="指定",
            text=assign_text, 
            command=on_confirm,
            corner_radius=8,
            font=button_bold_font
        )
        if lang_setting=="EN":
            tool_button_tooltip = CTkToolTip(confirm_button, message="\nCopy the command required to enable the selected preset to the clipboard.\nThen paste it into the slicing software's Print Settings -> Others -> Post-Processing Scripts.\n", font=("Segoe UI", 12),wraplength=600)
        else:
            tool_button_tooltip = CTkToolTip(confirm_button, message="\n复制启用所选预设所需的命令到剪贴板。\n\n然后将其粘贴到切片软件的工艺设置->其他->后处理脚本中。\n", font=("SimHei", 12),wraplength=600)
        
        new_button = ctk.CTkButton(
            button_frame, 
            # text="新建", 
            text=new_text,
            command=on_new,
            corner_radius=8,
            font=button_bold_font
        )
        if lang_setting=="EN":
            tool_button_tooltip = CTkToolTip(new_button, message="\nCreate a new glue preset configuration file.\nAfter creating, please adjust the parameters as needed and then save.\n", font=("Segoe UI", 12),wraplength=400)
        else:
            tool_button_tooltip = CTkToolTip(new_button, message="\n创建一个新的涂胶预设配置文件。\n\n新建后请根据需要调整各项参数，然后保存。\n", font=("SimHei", 12),wraplength=400)
        edit_button = ctk.CTkButton(
            button_frame, 
            # text="编辑", 
            text=edit_text,
            command=on_edit,
            corner_radius=8,
            font=button_bold_font
        )
        if lang_setting=="EN":
            tool_button_tooltip = CTkToolTip(edit_button, message="\nEdit the selected glue preset configuration file.\nAfter making changes, please click Confirm to apply the changes.\nHover over the parameter names to see parameter descriptions.\n", font=("Segoe UI", 12),wraplength=900)
        else:
            tool_button_tooltip = CTkToolTip(edit_button, message="\n编辑所选的涂胶预设配置文件。\n\n修改后请点击确定以应用更改。\n\n鼠标移动到参数名称上可以查看参数介绍\n", font=("SimHei", 12),wraplength=900)
        delete_button = ctk.CTkButton(
            button_frame, 
            # text="删除", 
            text=delete_text,
            command=on_delete,
            corner_radius=8,
            fg_color="#d9534f",
            hover_color="#c9302c",
            font=button_bold_font
        )
        if lang_setting=="EN":
            tool_button_tooltip = CTkToolTip(delete_button, message="\nDelete the selected glue preset configuration file.\n\nPlease operate with caution, as the file cannot be recovered after deletion.\n",font=("Segoe UI", 12),wraplength=300)
        else:
            tool_button_tooltip = CTkToolTip(delete_button, message="\n删除所选的涂胶预设配置文件。\n\n请谨慎操作，删除后文件无法恢复。\n", font=("SimHei", 12),wraplength=300)
        if lang_setting=="EN":
            #字体
            confirm_button.configure(font=("Segoe UI", 12, "bold"))
            new_button.configure(font=("Segoe UI", 12, "bold"))
            edit_button.configure(font=("Segoe UI", 12, "bold"))
            delete_button.configure(font=("Segoe UI", 12, "bold"))
        # 将按钮放置在网格中
        confirm_button.grid(row=0, column=0, padx=5, sticky="ew")
        new_button.grid(row=0, column=1, padx=5, sticky="ew")
        edit_button.grid(row=0, column=2, padx=5, sticky="ew")
        delete_button.grid(row=0, column=3, padx=5, sticky="ew")
        #比4CAF50更显眼一些的绿色:#43A047不够亮，需要
        if Have_Toml_Flag!=True:
            #这肯定是第一次运行，我们需要在指定按钮上方添加一个浮动的箭头，或者设置它闪烁
            def flash_button(button, flashes=90, interval=500):
                def toggle_color(count):
                    if count > 0:
                        current_color = button.cget("fg_color")
                        #像呼吸灯一样,颜色的切换是渐变的
                        # new_color = 
                        new_color = "#4CAF50" if current_color != "#4CAF50" else "#A5D6A7"
                        button.configure(fg_color=new_color)
                        button.after(interval, toggle_color, count - 1)
                    else:
                        # 最后确保按钮恢复到原始颜色
                        button.configure(fg_color="#4CAF50")
                toggle_color(flashes)
            flash_button(confirm_button)   
        # 配置网格列权重使按钮均匀分布
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.grid_columnconfigure(2, weight=1)
        button_frame.grid_columnconfigure(3, weight=1)

        download_frame = ctk.CTkFrame(tabview.tab(download_text),fg_color=("#f1f2f3", "#242424"),bg_color=("#f1f2f3", "#242424"))
        download_frame.pack(fill="both", expand=False)
        
        # MKP 分区
        mkp_frame = ctk.CTkFrame(download_frame, fg_color=("#f1f2f3", "#242424"))
        mkp_frame.pack(side="top", fill="both", expand=True, pady=5, padx=10)
        if lang_setting=="EN":
            mkp_label = ctk.CTkLabel(mkp_frame, text="MKP Presets", font=("Segoe UI", 14,"bold"))
        else:
            mkp_label = ctk.CTkLabel(mkp_frame, text="MKP预设", font=("SimHei", 14,"bold"))
        mkp_label.pack(anchor="w", pady=5)
        if lang_setting!="EN":
            mkp_label_tooltip = CTkToolTip(mkp_label, message="\n用于调整涂胶参数,例如速度和偏移(*.TOML)\n\n可以通过点击下载按钮获取最新的MKP预设文件。\n", font=("SimHei", 12),wraplength=300)
            mkp_frame_tooltip = CTkToolTip(mkp_frame, message="\n用于调整涂胶参数,例如速度和偏移(*.TOML)\n\n可以通过点击下载按钮获取最新的MKP预设文件。\n", font=("SimHei", 12),wraplength=300)
        else:
            mkp_label_tooltip = CTkToolTip(mkp_label, message="\nUsed to adjust glue parameters, such as speed and offset (*.TOML)\n\nYou can get the latest MKP preset files by clicking the download button.\n", font=("Segoe UI", 12),wraplength=300)
            mkp_frame_tooltip = CTkToolTip(mkp_frame, message="\nUsed to adjust glue parameters, such as speed and offset (*.TOML)\n\nYou can get the latest MKP preset files by clicking the download button.\n", font=("Segoe UI", 12),wraplength=300)
        bbs_frame = ctk.CTkFrame(download_frame, fg_color=("#f1f2f3", "#242424"))
        bbs_frame.pack(side="top", fill="both", expand=True, pady=5, padx=10)
        if lang_setting=="EN":
            bbs_label = ctk.CTkLabel(bbs_frame, text="BBS Presets", font=("Segoe UI", 14,"bold"))
        else:
            bbs_label = ctk.CTkLabel(bbs_frame, text="BBS预设", font=("SimHei", 14,"bold"))
        bbs_label.pack(anchor="w", pady=5)
        if lang_setting!="EN":
            bbs_label_tooltip = CTkToolTip(bbs_label, message="\n用于调整切片工艺以配合MKP涂胶，属于切片工艺预设。\n\n下载后重启切片软件即可显示，通常以MKPProcess开头。\n", font=("SimHei", 12),wraplength=300)
        else:
            bbs_label_tooltip = CTkToolTip(bbs_label, message="\nUsed to adjust slicing processes to work with MKP glue application, belonging to slicing process presets.\n\nAfter downloading, restart the slicing software to display it, usually starting with MKPProcess.\n", font=("Segoe UI", 12),wraplength=300)
        # ------------------------- MKP预设功能 -------------------------
        def fetch_mkp_presets():
            """联网拉取MKP预设列表"""
            base_url = "https://gitee.com/Jhmodel/MKPSupport/raw/main/Presets/"
            preset_files = ["A1.toml", "A1M.toml", "X1.toml", "P2.toml"]  # 预设文件名列表
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
        
        global update_mkp_presets
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
                    #A1的适用于A1机型，X1的适用于X1/P1机型，A1M的适用于A1M机型,为了对齐，A1后面加了两个空格,X1前面加了两个空格
                    text = f"{filename_without_ext} MKP预设"+("  " if filename_without_ext=="A1" else (" " if filename_without_ext=="A1M" else "  ")),
                    # text=f"{preset['filename']} (更新时间: {preset['publish_date']})",
                    font=("SimHei", 12),
                    anchor="w"
                )
                if lang_setting=="EN":
                    name_label.configure(font=("Segoe UI",12),text=f"{filename_without_ext} MKP Preset"+("  " if filename_without_ext=="A1" else (" " if filename_without_ext=="A1M" else "  ")))
                name_label.pack(side="left", padx=5)
                # name_label_tooltip = CTkToolTip(name_label, message=f"\n用于调整"+("A1" if filename_without_ext=="A1" else ("A1M" if filename_without_ext=="A1M" else "X1/P1"))+"机型的涂胶参数,例如速度和偏移(*.TOML)\n\n可以通过点击下载/更新按钮获取最新的MKP预设文件。\n", font=("SimHei", 12),wraplength=400)
                if lang_setting=="EN":
                    name_label_tooltip = CTkToolTip(name_label, message=f"\nUsed to adjust glue parameters, such as speed and offset for "+("A1" if filename_without_ext=="A1" else ("A1M" if filename_without_ext=="A1M" else "X1/P1"))+" models (*.TOML)\n\nYou can get the latest MKP preset files by clicking the download/update button.\n", font=("Segoe UI", 12),wraplength=400)
                else:
                    name_label_tooltip = CTkToolTip(name_label, message=f"\n用于调整"+("A1" if filename_without_ext=="A1" else ("A1M" if filename_without_ext=="A1M" else "X1/P1"))+"机型的涂胶参数,例如速度和偏移(*.TOML)\n\n可以通过点击下载/更新按钮获取最新的MKP预设文件。\n", font=("SimHei", 12),wraplength=400)
                # 状态标签
                status_color = "red" if preset["status"] == "已过时" else (("gray","white") if preset["status"] == "未下载" else ("black","lightgreen"))
                status_label = ctk.CTkLabel(
                    row_frame,
                    text=preset["status"],
                    text_color=status_color,
                    font=("SimHei", 12, "bold"  )
                )
                if lang_setting=="EN":
                    if status_label.cget("text")=="已过时":
                        status_label.configure(text="Outdated")
                    elif status_label.cget("text")=="未下载":
                        status_label.configure(text="Not Downloaded")
                    elif status_label.cget("text")=="最新":
                        status_label.configure(text="Latest")
                    status_label.configure(font=("Segoe UI", 12, "bold"  ))
                if status_label.cget("text")!="Latest" and status_label.cget("text")!="最新":
                    status_label.pack(side="left", padx=5)
                if lang_setting=="EN":
                    status_label_tooltip = CTkToolTip(status_label, message=f"\nPreset File: {preset['filename']}\n\nStatus: {preset['status']}\n\nUpdate Time: {preset['publish_date']}\n\nLocal File Update Time: {preset['local_date']}\n", font=("Segoe UI", 12),wraplength=400)
                else:
                    status_label_tooltip = CTkToolTip(status_label, message=f"\n预设文件: {preset['filename']}\n\n状态: {preset['status']}\n\n更新时间: {preset['publish_date']}\n\n本地文件更新时间: {preset['local_date']}\n", font=("SimHei", 12),wraplength=400)
                
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
                if lang_setting=="EN":
                    if button.cget("text")=="下载":
                        button.configure(text="CATCH")
                    elif button.cget("text")=="更新":
                        button.configure(text="UPDATE")
                    elif button.cget("text")=="最新":
                        button.configure(text="LATEST")
                    button.configure(font=("Segoe UI", 11, "bold"))
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
            if lang_setting=="EN":
                bbs_frame_tooltip = CTkToolTip(right_frame, message="\nUsed to adjust slicing processes to match MKP gluing, belonging to slicing process presets.\n\nAfter downloading, restart the slicing software to display, usually starting with MKPProcess.\n", font=("Segoe UI", 12),wraplength=300)
            else:
                bbs_frame_tooltip = CTkToolTip(right_frame, message="\n用于调整切片工艺以配合MKP涂胶，属于切片工艺预设。\n\n下载后重启切片软件即可显示，通常以MKPProcess开头。\n", font=("SimHei", 12),wraplength=300)
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
                    {"name": "P2", "support_file": "MKPSupport P2S.json", "process_file": "MKPProcess P2S.json"},
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
                    if lang_setting=="EN":
                        button_text = "Latest"
                    button_color = "gray"
                    if not support_exists or not process_exists:
                        button_text = "下载"
                        if lang_setting=="EN":  
                            button_text = "Download"
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
                                    # print(f"第{i+1}行不同: 本地='{local_line}', 远程='{remote_line}'")

                            # 检查行数是否不同
                            if len(support_local_lines) != len(support_remote_lines) and process_local_path.find("X1")==-1 and process_local_path.find("P1")==-1:
                                Differ_Flag = True
                                print(f"行数不同: 本地={len(support_local_lines)}, 远程={len(support_remote_lines)}")
                        
                            for i, (local_line, remote_line) in enumerate(zip(process_local_lines, process_remote_lines)):
                                if local_line != remote_line and remote_line.find("请将")==-1:
                                    Differ_Flag = True
                                    # print(f"第{i+1}行不同: 本地='{local_line}', 远程='{remote_line}'")
                            
                            if len(process_local_lines) != len(process_remote_lines):
                                Differ_Flag = True
                                # print(f"行数不同: 本地={len(process_local_lines)}, 远程={len(process_remote_lines)}")
                            if support_local_path.find("X1")!=-1 and support_local_path.find("P1")!=-1:
                                Differ_Flag = False  # X1和P1的配置文件不进行内容比较
                        except:
                            Differ_Flag = True

                        # print(f"Support Match: {support_match}, Process Match: {process_match}")
                        if Differ_Flag and machine["name"].find("X1")==-1 and machine["name"].find("P1")==-1:
                            button_text = "更新"
                            if lang_setting=="EN":
                                button_text = "Update"
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
                    if lang_setting=="EN":
                        state_button.configure(font=("Segoe UI", 12))
                    state_button.pack(side="right", padx=5)
                right_label.destroy()
            if lang_setting!="EN":
                DEFAULT_RIGHT_TEXT = "点击左侧用户ID对应的按钮\n\n会显示对应用户的预设列表"
                LOADING_TEXT = "在线检索中"
            else:
                DEFAULT_RIGHT_TEXT = "Click ID button to display your preset list"
                LOADING_TEXT = "Retrieving online"
            para.right_text_var = ctk.StringVar(value=DEFAULT_RIGHT_TEXT)
            right_label = ctk.CTkLabel(right_frame, textvariable=para.right_text_var, font=("SimHei", 15))
            if lang_setting=="EN":
                right_label.configure(font=("Segoe UI", 15))
            right_label.pack(expand=True)
            folders = load_bbs_presets()
            def refresh_right_label(foldername):
                # right_label.destroy()
                # right_label = ctk.CTkLabel(right_frame, text=LOADING_TEXT,font=("SimHei", 13))
                # right_label.configure(text="在线检索中")
                para.right_text_var.set(LOADING_TEXT)
                selection_dialog.update()
                # root.update()
                # right_label.pack(expand=True)
                refresh_bbs_rframe_list(foldername)      
            for folder in folders:
                folder_button = ctk.CTkButton(
                    left_frame,
                    text=folder,
                    # command=lambda f=folder: refresh_bbs_rframe_list(f),
                    command = lambda f=folder: (
                        refresh_right_label(f),  # 先更新标签文字
                    ),
                    width=120,
                    font=("SimHei", 12)
                )
                folder_button.pack(pady=2)
                if lang_setting!="EN":
                    folder_button_tooltip = CTkToolTip(folder_button, message=f"\n管理 {folder} 的BBS预设文件。\n\n点击后可下载或更新对应机型的配置文件。\n", font=("SimHei", 12),wraplength=300)
                else:
                    folder_button_tooltip = CTkToolTip(folder_button, message=f"\nManage BBS preset files for {folder}.\n\nClick to download or update configuration files for the corresponding model.\n", font=("Segoe UI", 12),wraplength=300)

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
                if action == "下载" or action == "Download":
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
                    #有时候用户需要0.2喷嘴的预设，这个预设的名称只在.json前加“ 0.2”,如果远程存在这种文件，则也下载，并且还可能是0.6或者0.8
                    nozzle_sizes = ["0.2","0.4","0.6","0.8"]
                    for size in nozzle_sizes:
                        support_file_nozzle = machine["support_file"].replace(".json", f" {size}.json")
                        process_file_nozzle = machine["process_file"].replace(".json", f" {size}.json")
                        support_url_nozzle = remote_base_url + support_file_nozzle
                        process_url_nozzle = remote_base_url + process_file_nozzle
                        if check_remote_file_exists(process_url_nozzle):
                            # 下载支持文件
                            support_content_nozzle = requests.get(support_url_nozzle).content
                            with open(os.path.join(bbs_path, "machine", support_file_nozzle), "wb") as f:
                                f.write(support_content_nozzle)
                            
                            # 下载流程文件
                            process_content_nozzle = requests.get(process_url_nozzle).content
                            with open(os.path.join(bbs_path, "process", process_file_nozzle), "wb") as f:
                                f.write(process_content_nozzle)
                            
                            print(f"✅ 已下载 {machine['name']} 喷嘴规格 {size} 的配置文件")
                elif action == "更新" or action == "Update":
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
                
                elif action == "最新" or action == "Latest":
                    print(f"ℹ️ {machine['name']} 的配置文件已是最新，无需操作")
                nozzle_sizes = ["0.2","0.4","0.6","0.8"]
                for size in nozzle_sizes:
                    support_file_nozzle = machine["support_file"].replace(".json", f" {size}.json")
                    process_file_nozzle = machine["process_file"].replace(".json", f" {size}.json")
                    support_url_nozzle = remote_base_url + support_file_nozzle
                    process_url_nozzle = remote_base_url + process_file_nozzle
                    if check_remote_file_exists(support_url_nozzle) and check_remote_file_exists(process_url_nozzle):
                        # 下载支持文件
                        support_content_nozzle = requests.get(support_url_nozzle).content
                        with open(os.path.join(bbs_path, "machine", support_file_nozzle), "wb") as f:
                            f.write(support_content_nozzle)
                        
                        # 下载流程文件
                        process_content_nozzle = requests.get(process_url_nozzle).content
                        with open(os.path.join(bbs_path, "process", process_file_nozzle), "wb") as f:
                            f.write(process_content_nozzle)
                        
                        print(f"✅ 已下载 {machine['name']} 喷嘴规格 {size} 的配置文件")
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
        calibr_preset = ctk.CTkFrame(tabview.tab(cali_text), fg_color=("#f1f2f3", "#242424"), bg_color=("#f1f2f3", "#242424"))
        calibr_preset.pack(fill="both", expand=True, padx=10, pady=10)
        cali_button_font = ctk.CTkFont(
            family="SimHei",  # 设置字体为黑体
            size=14
        )
        if lang_setting=="EN":
            cali_button_font = ctk.CTkFont(
                family="Segoe UI",  # 设置字体为黑体
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
        if lang_setting!="EN":
            LB_c1=ctk.CTkLabel(title_save_frame, text="喷嘴笔尖高度差校准", font=("SimHei", 14))
        else:
            LB_c1=ctk.CTkLabel(title_save_frame, text="Nozzle-Tip Offset", font=("Segoe UI", 14))
        LB_c1.pack(side="left")
        if lang_setting!="EN":
            cp_c1 = CTkToolTip(LB_c1, message="通过打印校准模型，测量笔尖与支撑面的高度差，从而校准喷嘴笔尖高度差。",font=("SimHei", 12))
        else:
            cp_c1 = CTkToolTip(LB_c1, message="Calibrate the nozzle-tip offset by printing the calibration model and measuring the height difference between the pen tip and the support surface.",wraplength=550,font=("SimHei", 12))
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
        if lang_setting!="EN":
            ctk.CTkLabel(save_frame, text="保存到:",font=cali_button_font).pack(side="left")
        else:
            ctk.CTkLabel(save_frame, text="Save to:",font=cali_button_font).pack(side="left")
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
            if lang_setting!="EN":
                z_button_text = "打开3MF"
            else:
                z_button_text = "Open"
            z_button_color = "green"
        else:
            if lang_setting!="EN":
                z_button_text = "下载"
            else:
                z_button_text = "Download"
            z_button_color = "#1E90FF"
        button_outer_frame = ctk.CTkFrame(z_frame, fg_color="transparent")
        button_outer_frame.pack(fill="x", expand=True, pady=5,anchor="center")
        button_frame = ctk.CTkFrame(button_outer_frame, fg_color="transparent")
        button_frame.pack(anchor="center")

        z_button = ctk.CTkButton(button_frame,font=cali_button_font, text=z_button_text,fg_color=z_button_color, command=lambda: check_or_download("ZOffset Calibration.3mf", z_button))
        z_button.pack(pady=5,side="left", padx=5)
        # 保存按钮

        ZSave=ctk.CTkButton(button_frame,font=cali_button_font, text="保存", command=lambda: save_z_offset())
        if lang_setting=="EN":
            ZSave.configure(text="Save")
        ZSave.pack(pady=5, side="left", padx=5)
        # ZSave.configure(state="disabled",fg_color="grey")  # 初始状态禁用
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
        if lang_setting!="EN":
            LB_c2=ctk.CTkLabel(title_save_frame, text="XY偏移值校准", font=("SimHei", 14))
        else:
            LB_c2=ctk.CTkLabel(title_save_frame, text="XY Offset Calibration", font=("Segoe UI", 14))
        LB_c2.pack(side="left")
        if lang_setting!="EN":
            Cb_c2= CTkToolTip(LB_c2,message="打印校准模型，通过找到与笔尖轨迹最重合的打印的校准线，校准XY偏移值。",font=("SimHei", 12))
        else:
            Cb_c2= CTkToolTip(LB_c2,message="Print the calibration model and calibrate the XY offset value by finding the printed calibration line that best matches the pen tip trajectory.",wraplength=550,font=("Segoe UI", 12))
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
        if lang_setting!="EN":
            ctk.CTkLabel(save_frame, text="保存到:",font=cali_button_font).pack(side="left")
        else:
            ctk.CTkLabel(save_frame, text="Save to:",font=cali_button_font).pack(side="left")
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
            xy_button_text = "打开3MF"
            if lang_setting=="EN":
                xy_button_text = "Open"
            xy_button_color = "green"
        else:
            xy_button_text = "下载"
            if lang_setting=="EN":
                xy_button_text = "Download"
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
            xy_button_text = "打开3MF"
            if lang_setting=="EN":
                xy_button_text = "Open"
            xy_button_color = "green"
        else:
            xy_button_text = "下载"
            if lang_setting=="EN":
                xy_button_text = "Download"

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
        if lang_setting=="EN":
            XYSave.configure(text="Save")
        XYSave.pack(pady=5, side="left", padx=5)
        # XYSave.configure(state="disabled", fg_color="grey")  # 初始状态禁用
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
        if lang_setting!="EN":
            lb_c6=ctk.CTkLabel(title_frame, text="L形精密度校准", font=("SimHei", 14))
        else:
            lb_c6=ctk.CTkLabel(title_frame, text="L-Shape Precision Calibration", font=("Segoe UI", 14))
        lb_c6.pack(side="left")
        if lang_setting!="EN":
            Cp_c3= CTkToolTip(lb_c6, message="MKPv2不需执行这个测试。通过打印L形校准模型，观察笔尖在两个垂直平面上的晃动，从而检验打印件公差。",font=("SimHei", 12))
        else:
            Cp_c3= CTkToolTip(lb_c6, message="MKPv2 does not require this test. By printing the L-shape calibration model, observe the wobble of the pen tip on two perpendicular planes to check the tolerance of the printed part.",wraplength=550,font=("Segoe UI", 12))
        # 按钮和文件检查
        filepath = os.path.join(CALIBR_DIR, "LShape Calibration.3mf")
        if os.path.exists(filepath):
            l_button_text = "不再适用"
            l_button_color = "grey"
        else:
            l_button_text = "不再适用"
            l_button_color = "grey"

        l_button = ctk.CTkButton(
            title_frame,
            text=l_button_text,
            fg_color=l_button_color,
            command=lambda: check_or_download("LShape Calibration.3mf", l_button),
            font=cali_button_font
        )
        # l_button.pack(pady=5,side="right", padx=5)


        # ------------------------- 功能函数（使用 ctk 对话框） -------------------------
        def check_or_download(filename, button):
            """检查文件是否存在，否则下载"""
            #machine:A1,P1,X1
            #根据下拉框变量里的选中机型确定机型,如果里面不含有A1、P1、X1，则默认为A1 mini
            if filename=="ZOffset Calibration.3mf":
                #从z_save_option获取选中的机型
                selected_preset = z_save_option.get()
                if selected_preset.find("A1")!=-1 and selected_preset.find("A1M")==-1:
                    machine = "A1"
                elif selected_preset.find("P1")!=-1:
                    machine = "P1"
                elif selected_preset.find("X1")!=-1:
                    machine = "P1"
                elif selected_preset.find("P2")!=-1:
                    machine = "P2"
                else:
                    machine = "A1M"
            elif filename=="Precise Calibration.3mf":
                selected_preset = xy_save_option.get()
                if selected_preset.find("A1")!=-1 and selected_preset.find("A1M")==-1:
                    machine = "A1"
                elif selected_preset.find("P1")!=-1:
                    machine = "P1"
                elif selected_preset.find("X1")!=-1:
                    machine = "P1"
                elif selected_preset.find("P2")!=-1:
                    machine = "P2"
                else:
                    machine = "A1M"

            filepath = os.path.join(CALIBR_DIR, filename)
            if not os.path.exists(CALIBR_DIR):
                os.makedirs(CALIBR_DIR, exist_ok=True)

            if os.path.exists(filepath):
                #以防万一，还是尝试联网，如果联网成功，则重新下载
                os.remove(filepath)
                try:
                    response = requests.get(f"{GITEE_URL}/{machine}/{filename}")
                    response.raise_for_status()
                    with open(os.path.join(CALIBR_DIR, filename), "wb") as f:
                        f.write(response.content)
                except Exception as e:
                    print(e)
                        

                button.configure(text="打开3MF", fg_color="green")
                if lang_setting=="EN":
                    button.configure(text="Open", fg_color="green")
                #启动filename对应的3mf
                os.startfile(filepath)
                

            else:
                button.configure(text="下载", fg_color="red")
                if lang_setting=="EN":
                    button.configure(text="Download", fg_color="red")
                # if ask_yesno_dialog("确认", f"下载 {filename}？"):
                
                download_file(filename, button)
                # show_calibration_prompt(filename)

        def download_file(filename, button):
            if filename=="ZOffset Calibration.3mf":
                #从z_save_option获取选中的机型
                selected_preset = z_save_option.get()
                if selected_preset.find("A1")!=-1 and selected_preset.find("A1M")==-1:
                    machine = "A1"
                elif selected_preset.find("P1")!=-1:
                    machine = "P1"
                elif selected_preset.find("X1")!=-1:
                    machine = "P1"
                else:
                    machine = "A1M"
            elif filename=="Precise Calibration.3mf":
                selected_preset = xy_save_option.get()
                if selected_preset.find("A1")!=-1 and selected_preset.find("A1M")==-1:
                    machine = "A1"
                elif selected_preset.find("P1")!=-1:
                    machine = "P1"
                elif selected_preset.find("X1")!=-1:
                    machine = "P1"
                else:
                    machine = "A1M"

            """从Gitee下载文件"""
            try:
                response = requests.get(f"{GITEE_URL}/{machine}/{filename}")
                print(f"{GITEE_URL}/{machine}/{filename}")
                response.raise_for_status()
                with open(os.path.join(CALIBR_DIR, filename), "wb") as f:
                    f.write(response.content)
                print("Successfully downloaded")
                button.configure(text="打开3MF", fg_color="green")
                if lang_setting=="EN":
                    button.configure(text="Open", fg_color="green")
                filepath = os.path.join(CALIBR_DIR, filename)
                os.startfile(filepath)
                # show_calibration_prompt(filename)
            except Exception as e:
                pass
            
                
            
        def show_calibration_prompt(filename):
            dialog = ctk.CTkToplevel()
            dialog.title("校准")
            dialog.geometry("1200x600")
            dialog.after(201, lambda :dialog.iconbitmap(mkpicon_path))  # 解决某些系统图标不显示的问题
            # dialog.resizable(False, False)
            # dialog.geometry()
            dialog.geometry(CenterWindowToDisplay(dialog, 700, 500, dialog._get_window_scaling()))
            dialog.maxsize(700, 500)
            dialog.minsize(700, 500)
            # selection_dialog.geometry(CenterWindowToDisplay(selection_dialog, 550, 400, selection_dialog._get_window_scaling()))
            mkpexecutable_dir = os.path.dirname(sys.executable)
            mkpinternal_dir = os.path.join(mkpexecutable_dir, "resources")
            dialog.attributes("-topmost", True)  # 确保对话框在最上层
            
            def continue_function():
                popup = ctk.CTkToplevel(dialog)
                popup.after(201, lambda: popup.iconbitmap(mkpicon_path))
                popup.title("继续校准" if lang_setting != "EN" else "Continue Calibration")
                popup.geometry("720x520")  # 稍微扩大窗口
                popup.geometry(CenterWindowToDisplay(popup, 720, 520, popup._get_window_scaling()))
                popup.maxsize(720, 520)
                popup.minsize(720, 520)
                # 设置窗口透明度和深灰色背景
                popup.configure(fg_color='#1a1a1a')
                popup.attributes('-alpha', 0.9)
                
                # 主框架
                main_frame = ctk.CTkFrame(popup, fg_color='#1a1a1a')
                main_frame.pack(fill="both", expand=True, padx=20, pady=50)
                
                # 标题
                title_label = ctk.CTkLabel(
                    main_frame,
                    text="请选择涂胶最合适的平面位置" if lang_setting != "EN" else "Please select the most suitable plane position for gluing",
                    font=("SimHei", 16, "bold"),
                    text_color='#ffffff'
                )
                title_label.pack(pady=(0, 30))
                breathing_id = None
                # 创建画布框架 - 加大尺寸
                canvas_frame = ctk.CTkFrame(main_frame, fg_color='#1a1a1a', width=720, height=230)
                canvas_frame.pack()
                canvas_frame.pack_propagate(False)
                
                # 单独导入tkinter Canvas
                import tkinter as tk_canvas
                
                # 创建画布
                canvas = tk_canvas.Canvas(
                    canvas_frame,
                    width=720,
                    height=230,
                    bg='#1a1a1a',
                    highlightthickness=0,
                    bd=0
                )
                canvas.pack()
                
                # 计算方块参数 - 增加边距确保完全显示
                num_blocks = 11
                block_size = 44
                spacing = 22
                total_width = num_blocks * (block_size + spacing) - spacing
                start_x = (720 - total_width) // 2
                # 确保起始位置至少有20像素边距
                y_position = 70  # 下移一点
                
                # 存储方块坐标和值的对应关系
                blocks = []
                
                # 绘制连接所有方块的长条
                long_bar_y = y_position + block_size  # 直接紧贴
                long_bar_start_x = start_x 
                long_bar_end_x = start_x + num_blocks * (block_size + spacing) - spacing 
                
                # 绘制长条（白色）
                long_bar = canvas.create_rectangle(
                    long_bar_start_x, long_bar_y,
                    long_bar_end_x, long_bar_y + 12,
                    fill='#ffffff',
                    outline='#f0f0f0',
                    width=1
                )
                def create_rounded_rect(canvas, x1, y1, x2, y2, radius=8, **kwargs):
                    """创建只有左上和右上圆角的矩形"""
                    points = []
                    
                    # 左上角圆角
                    points.extend([x1 + radius, y1])  # 起点
                    points.extend([x2 - radius, y1])  # 上边
                    
                    # 右上角圆角
                    for i in range(90, 0, -15):  # 从90度到0度，步长15度
                        angle = i * 3.14159 / 180
                        points.append(x2 - radius + radius * (1 - i/90))  # 简化版，实际应该用cos
                        points.append(y1 + radius * (1 - i/90))  # 简化版，实际应该用sin
                    
                    # 右下角直角
                    points.extend([x2, y1 + radius])
                    points.extend([x2, y2])
                    
                    # 左下角直角
                    points.extend([x1, y2])
                    points.extend([x1, y1 + radius])
                    
                    # 闭合左上角
                    points.extend([x1 + radius, y1])
                    
                    return canvas.create_polygon(points, smooth=True, **kwargs)
                # 绘制方块和刻度
                for i in range(num_blocks):
                    x1 = start_x + i * (block_size + spacing)
                    y1 = y_position
                    x2 = x1 + block_size
                    y2 = y1 + block_size
                    
                    # 计算对应的值（从-0.5到+0.5）
                    value = 0.5 + i * (-0.1)
                    
                    # 绘制方块 - 无边框，白色填充
                    block_id = canvas.create_rectangle(
                        x1, y1, x2, y2,
                        outline='',
                        width=0,
                        fill='#ffffff',
                        tags=f"block_{i}"
                    )
                    
                    # 在方块上显示数值
                    text_id = canvas.create_text(
                        x1 + block_size//2,
                        y1 + block_size//2,
                        text="",
                        fill='#333333',
                        font=("SimHei", 11, "bold")
                    )
                    
                    blocks.append({
                        'id': block_id,
                        'text_id': text_id,
                        'value': value,
                        'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
                        'index': i
                    })
                    
                    # 创建更大的点击区域（透明矩形覆盖更大范围）
                    click_padding = 10
                    click_id = canvas.create_rectangle(
                        x1 - click_padding, y1 - click_padding,
                        x2 + click_padding, y2 + click_padding,
                        outline='',
                        fill='',
                        tags=f"click_{i}"
                    )
                    
                    # 绑定点击事件到点击区域
                    def make_click_handler(idx):
                        return lambda event: on_block_click(idx)
                    
                    canvas.tag_bind(f"click_{i}", '<Button-1>', make_click_handler(i))
                    
                    # 绑定悬停事件到点击区域
                    def make_enter_handler(idx):
                        return lambda event: on_block_enter(idx)
                    
                    def make_leave_handler(idx):
                        return lambda event: on_block_leave(idx)
                    
                    canvas.tag_bind(f"click_{i}", '<Enter>', make_enter_handler(i))
                    canvas.tag_bind(f"click_{i}", '<Leave>', make_leave_handler(i))
                    
                    # 在方块上方添加刻度线
                    tick_x = x1 + block_size // 2
                    tick_y = y1 - 8  # 再往上一点
                    canvas.create_line(
                        tick_x, tick_y - 5,
                        tick_x, tick_y,
                        fill='#888888',
                        width=2
                    )
                    
                    # 在刻度线上方添加数值文字
                    canvas.create_text(
                        tick_x, tick_y - 15,  # 在刻度线上方
                        text=f"{value:.1f}",
                        fill='#cccccc',  # 浅灰色
                        font=("SimHei", 12)
                    )
                
                # 标记中心位置（0点）- 特殊颜色
                center_idx = num_blocks // 2
                center_x = start_x + center_idx * (block_size + spacing) + block_size // 2
                center_tick_y = y_position - 8
                # canvas.create_text(
                #     center_x, center_tick_y - 15,
                #     text="0.0",
                #     fill='#ffaa00',  # 橙黄色
                #     font=("SimHei", 10, "bold")
                # )
                
                # 标记左右边界提示
                canvas.create_text(
                    long_bar_start_x+27, y_position + 70,
                    text="笔压减小↑",
                    fill='#ff7f7f',
                    font=("SimHei", 10)
                )
                canvas.create_text(
                    long_bar_end_x-27, y_position + 70,
                    text="笔压增大↓",
                    fill='#99ff99',
                    font=("SimHei", 10)
                )
                
                # 当前选中的方块
                selected_block = None
                glow_item = None
                hover_item = None
                
                def on_block_enter(idx):
                    """鼠标悬停时的浅光效果"""
                    nonlocal hover_item
                    
                    if selected_block and selected_block['index'] == idx:
                        return  # 已选中的方块不覆盖
                    
                    # 清除之前的悬停效果
                    if hover_item:
                        canvas.delete(hover_item)
                    
                    block = blocks[idx]
                    x1, y1, x2, y2 = block['x1'], block['y1'], block['x2'], block['y2']
                    
                    # 创建浅色发光效果
                    from PIL import Image, ImageDraw, ImageFilter, ImageTk
                    
                    glow_img = Image.new("RGBA", (canvas.winfo_width(), canvas.winfo_height()), (0, 0, 0, 0))
                    draw = ImageDraw.Draw(glow_img)
                    
                    # 绘制发光矩形
                    padding = 10
                    draw.rectangle(
                        [max(0, x1-padding), max(0, y1-padding), 
                        min(canvas.winfo_width(), x2+padding), min(canvas.winfo_height(), y2+padding)],
                        fill=(30, 255, 30, 80)  # 更低透明度
                    )
                    
                    glow_img = glow_img.filter(ImageFilter.GaussianBlur(6))
                    
                    glow_photo = ImageTk.PhotoImage(glow_img)
                    hover_item = canvas.create_image(0, 0, anchor='nw', image=glow_photo)
                    canvas.tag_lower(hover_item)
                    
                    canvas.hover_photo = glow_photo
                
                def on_block_leave(idx):
                    """鼠标离开时清除悬停效果"""
                    nonlocal hover_item
                    if hover_item:
                        canvas.delete(hover_item)
                        hover_item = None
                
                def on_block_click(idx):
                    nonlocal selected_block, glow_item, hover_item, breathing_id  # 添加 breathing_id
                    
                    print(f"点击了方块 {idx}")
                    
                    # 清除悬停效果
                    if hover_item:
                        canvas.delete(hover_item)
                        hover_item = None
                    
                    # 清除之前的动画
                    if breathing_id:
                        canvas.after_cancel(breathing_id)
                        breathing_id = None
                    
                    if glow_item:
                        canvas.delete(glow_item)
                        glow_item = None
                    
                    # 恢复之前选中的方块
                    if selected_block:
                        canvas.itemconfig(selected_block['id'], fill='#ffffff')
                        canvas.itemconfig(selected_block['text_id'], fill='#333333')
                    
                    # 设置新选中的方块
                    selected_block = blocks[idx]
                    canvas.itemconfig(selected_block['id'], fill='#00ff00')
                    canvas.itemconfig(selected_block['text_id'], fill='#000000')
                    
                    # 创建发光效果并开始呼吸
                    create_glow_with_breath(idx)
                    
                    selected_value_label.configure(
                        text=f"选中值: {selected_block['value']:.1f} mm" if lang_setting != "EN" 
                        else f"Selected: {selected_block['value']:.1f} mm",
                        text_color='#00ff00'
                    )

                def create_glow_with_breath(idx):
                    """创建呼吸发光效果"""
                    nonlocal glow_item, breathing_id
                    
                    block = blocks[idx]
                    x1, y1, x2, y2 = block['x1'], block['y1'], block['x2'], block['y2']
                    
                    # 呼吸参数
                    breath_step = [0]
                    breath_direction = [1]
                    
                    def update_glow():
                        nonlocal glow_item
                        
                        # 呼吸效果：半径在5-15之间变化
                        breath_step[0] += breath_direction[0] * 0.5
                        if breath_step[0] > 0:
                            breath_direction[0] = -1
                        elif breath_step[0] < -2:
                            breath_direction[0] = 1
                        
                        padding = 8 + breath_step[0]
                        opacity = 255
                        
                        # 创建发光图片
                        from PIL import Image, ImageDraw, ImageFilter, ImageTk
                        import numpy as np
                        
                        glow_img = Image.new("RGBA", (canvas.winfo_width(), canvas.winfo_height()), (0, 0, 0, 0))
                        draw = ImageDraw.Draw(glow_img)
                        draw.rectangle(
                            [x1-padding, y1-padding, x2+padding, y2+padding],
                            fill=(30, 255, 30, opacity)
                        )
                        
                        glow_img = glow_img.filter(ImageFilter.GaussianBlur(6))
                        
                        # 强度调整
                        glow_array = np.array(glow_img).astype(np.float32) / 255.0
                        glow_array[..., :3] *= 2.2
                        glow_array = np.clip(glow_array, 0, 1)
                        glow_img = Image.fromarray((glow_array * 255).astype(np.uint8), "RGBA")
                        
                        glow_photo = ImageTk.PhotoImage(glow_img)
                        
                        # 更新显示
                        if glow_item:
                            canvas.delete(glow_item)
                        glow_item = canvas.create_image(0, 0, anchor='nw', image=glow_photo)
                        canvas.tag_lower(glow_item)
                        canvas.glow_photo = glow_photo
                        
                        # 继续动画
                        nonlocal breathing_id
                        breathing_id = canvas.after(70, update_glow)
                    
                    # 启动呼吸动画
                    update_glow()
                    nonlocal selected_block, glow_item, hover_item
                    
                    print(f"点击了方块 {idx}")
                    
                    # 清除悬停效果
                    if hover_item:
                        canvas.delete(hover_item)
                        hover_item = None
                    
                    # 清除之前的发光效果
                    if glow_item:
                        canvas.delete(glow_item)
                        glow_item = None
                    
                    # 恢复之前选中的方块颜色为白色（包括边框）
                    if selected_block:
                        canvas.itemconfig(selected_block['id'], 
                                        fill='#ffffff',  # 填充白色
                                        outline='',      # 无边框
                                        width=0)
                        canvas.itemconfig(selected_block['text_id'], fill='#333333')

                    # 设置新选中的方块
                    selected_block = blocks[idx]

                    # # 将选中方块变成绿色边框
                    # canvas.itemconfig(selected_block['id'], 
                    #                 fill='#ffffff',      # 填充保持白色
                    #                 outline='#00ff00',   # 边框绿色
                    #                 width=3)             # 边框宽度3
                    # canvas.itemconfig(selected_block['text_id'], fill='#333333')  # 文字保持深灰色
                    
                    # 创建点击发光效果
                    from PIL import Image, ImageDraw, ImageFilter, ImageTk
                    import numpy as np
                    
                    x1, y1, x2, y2 = selected_block['x1'], selected_block['y1'], selected_block['x2'], selected_block['y2']
                    
                    # 创建发光图层
                    glow_img = Image.new("RGBA", (canvas.winfo_width(), canvas.winfo_height()), (0, 0, 0, 0))
                    draw = ImageDraw.Draw(glow_img)
                    
                    # 绘制发光矩形
                    padding = 8
                    draw.rectangle(
                        [max(0, x1-padding), max(0, y1-padding), 
                        min(canvas.winfo_width(), x2+padding), min(canvas.winfo_height(), y2+padding)],
                        fill=(30, 255, 30, 255)
                    )
                    
                    glow_img = glow_img.filter(ImageFilter.GaussianBlur(6))
                    
                    # 强度调整
                    glow_array = np.array(glow_img).astype(np.float32) / 255.0
                    glow_array[..., :3] *= 2.2
                    glow_array = np.clip(glow_array, 0, 1)
                    glow_img = Image.fromarray((glow_array * 255).astype(np.uint8), "RGBA")
                    
                    glow_photo = ImageTk.PhotoImage(glow_img)
                    
                    glow_item = canvas.create_image(0, 0, anchor='nw', image=glow_photo)
                    canvas.tag_lower(glow_item)
                    
                    canvas.glow_photo = glow_photo
                    
                    # 更新选中值显示
                    selected_value_label.configure(
                        text=f"选中值: {selected_block['value']:.1f} mm" if lang_setting != "EN" 
                        else f"Selected: {selected_block['value']:.1f} mm",
                        text_color='#ffffff'
                    )
                    
                    print(f"已选中值: {selected_block['value']}")
                
                # 显示选中值的标签
                selected_value_label = ctk.CTkLabel(
                    main_frame,
                    text="请点击选择一个方块" if lang_setting != "EN" else "Please click to select a block",
                    font=("SimHei", 14),
                    text_color='#ffffff'
                )
                selected_value_label.pack(pady=20)
                
                # 按钮框架
                button_frame = ctk.CTkFrame(main_frame, fg_color='#1a1a1a')
                button_frame.pack(pady=10)
                
                # 确定按钮
                def confirm_selection():
                    if selected_block is None:
                        selected_value_label.configure(
                            text="请先选择一个方块！" if lang_setting != "EN" 
                            else "Please select a block first!",
                            text_color='#ff6666'
                        )
                        return
                    
                    selected_value = float(selected_block['value'])
                    print(f"确认选择的平面值：{selected_value}")
                    
                    para.Temp_ZOffset_Calibr = selected_value
                    print(f"类型: {type(selected_value)}")
                    print(f"类型: {type(para.Temp_ZOffset_Calibr)}")
                    if abs(para.Temp_ZOffset_Calibr) < 0.09:
                        MKPMessagebox.show_info(
                            title='错误' if lang_setting != "EN" else 'Error',
                            message="校准值太小，请重新选择" if lang_setting != "EN" 
                            else "Calibration value too small, please select again"
                        )
                        return
                    
                    # 关闭弹窗
                    popup.destroy()
                    dialog.destroy()
                    
                    # 保存配置
                    z_save_option_value = z_save_option.get() + ".toml"
                    documents_path = os.path.expanduser("~/Documents")
                    mkpsupport_path = os.path.join(documents_path, "MKPSupport")
                    z_save_option_value = os.path.join(mkpsupport_path, z_save_option_value)
                    
                    read_toml_config(z_save_option_value)
                    Temp_Obsolete_ZOffset = float(para.Z_Offset)
                    
                    para.Z_Offset = Temp_Obsolete_ZOffset + para.Temp_ZOffset_Calibr
                    
                    write_toml_config(z_save_option_value)
                    
                    show_info_dialog(
                        "结果" if lang_setting != "EN" else "Result",
                        f"喷嘴笔尖高度差校准结果已保存到 {z_save_option.get()+'.toml'}\n\n"
                        f"原偏移值为: {Temp_Obsolete_ZOffset:.2f}mm\n\n"
                        f"新Z偏移值为: {para.Z_Offset:.2f}mm"
                    )
                
                confirm_button = ctk.CTkButton(
                    button_frame,
                    text="确定" if lang_setting != "EN" else "Confirm",
                    command=confirm_selection,
                    font=("SimHei", 14),
                    width=100,
                    fg_color='#00aa00',
                    hover_color='#00ff00'
                )
                confirm_button.pack(side="left", padx=10)
                
                # 取消按钮
                cancel_button = ctk.CTkButton(
                    button_frame,
                    text="取消" if lang_setting != "EN" else "Cancel",
                    command=popup.destroy,
                    font=("SimHei", 14),
                    width=100,
                    fg_color='#aa0000',
                    hover_color='#ff0000'
                )
                cancel_button.pack(side="left", padx=10)
                
                dialog.withdraw()
                                

            def xy_continue_function():
                popup = ctk.CTkToplevel(dialog)
                popup.title("继续校准" if lang_setting != "EN" else "Continue Calibration")
                popup.after(201, lambda: popup.iconbitmap(mkpicon_path))
                # popup.geometry("720x520")
                popup.geometry(CenterWindowToDisplay(popup, 720, 600, popup._get_window_scaling()))
                popup.maxsize(720, 600)
                popup.minsize(720, 600)
                
                # 设置窗口透明度和深灰色背景
                popup.configure(fg_color='#1a1a1a')
                popup.attributes('-alpha', 0.93)
                
                # 主框架
                main_frame = ctk.CTkFrame(popup, fg_color='#1a1a1a')
                main_frame.pack(fill="both", expand=True, pady=10)
                
                # 标题
                title_label = ctk.CTkLabel(
                    main_frame,
                    text="请选择与笔尖轨迹最重合的校准线" if lang_setting != "EN" else "Please select the calibration line that best matches the tip trajectory",
                    font=("SimHei", 16, "bold"),
                    text_color='#ffffff'
                )
                title_label.pack(pady=10)
                
                # 创建画布框架
                canvas_frame = ctk.CTkFrame(main_frame, fg_color='#1a1a1a', width=720, height=450)
                canvas_frame.pack()
                canvas_frame.pack_propagate(False)
                
                # 单独导入tkinter Canvas
                import tkinter as tk_canvas
                from PIL import Image, ImageDraw, ImageFilter, ImageTk
                
                # 创建画布
                canvas = tk_canvas.Canvas(
                    canvas_frame,
                    width=720,
                    height=450,
                    bg='#1a1a1a',
                    highlightthickness=0,
                    bd=0
                )
                canvas.pack()
                
                # 定义原点坐标（左下角）
                origin_x = 120
                origin_y = 450
                
                # 定义参数
                num_lines = 11
                line_spacing = 40
                line_length_normal = 40
                line_length_center = 55
                
                # 存储X轴和Y轴的线
                x_lines = []
                y_lines = []
                
                # 绘制X轴主轴线 - 从原点向右
                canvas.create_line(
                    origin_x, origin_y,
                    origin_x + (num_lines-1) * line_spacing + 41, origin_y,
                    fill='#00ff00',
                    width=2
                )
                
                # 绘制Y轴主轴线 - 从原点向上
                canvas.create_line(
                    origin_x, origin_y,
                    origin_x, origin_y - (num_lines-1) * line_spacing - 41,
                    fill='#00ff00',
                    width=2
                )
                
                # 绘制X轴方向的线 - 从X轴向上生长
                for i in range(num_lines):
                    x_pos = origin_x + 39 + i * line_spacing
                    value = -1.0 + i * 0.2
                    
                    # 确定线长
                    if i == 5:
                        line_length = line_length_center
                        line_color = '#ffffff'
                    else:
                        line_length = line_length_normal
                        line_color = '#ffffff'
                    
                    # 绘制竖线 - 从X轴向上
                    line_id = canvas.create_line(
                        x_pos, origin_y,
                        x_pos, origin_y - line_length,
                        fill=line_color,
                        width=4,
                        tags=f"x_line_{i}"
                    )
                    
                    # 显示数值
                    text_id = canvas.create_text(
                        x_pos, origin_y - line_length - 12,
                        text="" if abs(value + 1.0) < 0.001 else f"{value:.1f}", 
                        fill='#cccccc',
                        font=("SimHei", 12),
                        tags=f"x_text_{i}"
                    )
                    
                    x_lines.append({
                        'id': line_id,
                        'text_id': text_id,
                        'value': value,
                        'x': x_pos,
                        'y_top': origin_y - line_length,
                        'y_bottom': origin_y,
                        'index': i,
                        'axis': 'x'
                    })
                    
                    # 点击区域
                    click_padding = 20
                    click_id = canvas.create_rectangle(
                        x_pos - click_padding, origin_y - line_length - click_padding,
                        x_pos + click_padding, origin_y + click_padding,
                        outline='',
                        fill='',
                        tags=f"x_click_{i}"
                    )
                    
                    def make_x_click_handler(idx):
                        return lambda event: on_line_click(idx, 'x')
                    
                    def make_x_enter_handler(idx):
                        return lambda event: on_line_enter(idx, 'x')
                    
                    def make_x_leave_handler(idx):
                        return lambda event: on_line_leave(idx, 'x')
                    
                    canvas.tag_bind(f"x_click_{i}", '<Button-1>', make_x_click_handler(i))
                    canvas.tag_bind(f"x_click_{i}", '<Enter>', make_x_enter_handler(i))
                    canvas.tag_bind(f"x_click_{i}", '<Leave>', make_x_leave_handler(i))
                
                # 绘制Y轴方向的线 - 从Y轴向右生长
                for i in range(num_lines):
                    y_pos = origin_y - 39 - i * line_spacing
                    value = -1.0 + i * 0.2
                    
                    # 确定线长
                    if i == 5:
                        line_length = line_length_center
                        line_color = '#ffffff'
                    else:
                        line_length = line_length_normal
                        line_color = '#ffffff'
                    
                    # 绘制横线 - 从Y轴向右
                    line_id = canvas.create_line(
                        origin_x, y_pos,
                        origin_x + line_length, y_pos,
                        fill=line_color,
                        width=4,
                        tags=f"y_line_{i}"
                    )
                    
                    # 显示数值
                    text_id = canvas.create_text(
                        origin_x + line_length +24, y_pos,
                        text="" if abs(value + 1.0) < 0.001 else f"{value:.1f}", 
                        fill='#cccccc',
                        font=("SimHei", 12),
                        tags=f"y_text_{i}"
                    )
                    
                    y_lines.append({
                        'id': line_id,
                        'text_id': text_id,
                        'value': value,
                        'y': y_pos,
                        'x_left': origin_x,
                        'x_right': origin_x + line_length,
                        'index': i,
                        'axis': 'y'
                    })
                    
                    # 点击区域
                    click_padding = 10
                    click_id = canvas.create_rectangle(
                        origin_x - click_padding, y_pos - click_padding,
                        origin_x + line_length + click_padding, y_pos + click_padding,
                        outline='',
                        fill='',
                        tags=f"y_click_{i}"
                    )
                    
                    def make_y_click_handler(idx):
                        return lambda event: on_line_click(idx, 'y')
                    
                    def make_y_enter_handler(idx):
                        return lambda event: on_line_enter(idx, 'y')
                    
                    def make_y_leave_handler(idx):
                        return lambda event: on_line_leave(idx, 'y')
                    
                    canvas.tag_bind(f"y_click_{i}", '<Button-1>', make_y_click_handler(i))
                    canvas.tag_bind(f"y_click_{i}", '<Enter>', make_y_enter_handler(i))
                    canvas.tag_bind(f"y_click_{i}", '<Leave>', make_y_leave_handler(i))
                
                
                # 当前选中的线
                selected_x_line = None
                selected_y_line = None
                x_glow_item = None
                y_glow_item = None
                x_hover_item = None
                y_hover_item = None
                
                def on_line_enter(idx, axis):
                    nonlocal x_hover_item, y_hover_item
                    
                    lines = x_lines if axis == 'x' else y_lines
                    selected_ref = selected_x_line if axis == 'x' else selected_y_line
                    
                    if selected_ref and selected_ref['index'] == idx:
                        return
                    
                    if axis == 'x' and x_hover_item:
                        canvas.delete(x_hover_item)
                        x_hover_item = None
                    elif axis == 'y' and y_hover_item:
                        canvas.delete(y_hover_item)
                        y_hover_item = None
                    
                    line = lines[idx]
                    
                    glow_img = Image.new("RGBA", (canvas.winfo_width(), canvas.winfo_height()), (0, 0, 0, 0))
                    draw = ImageDraw.Draw(glow_img)
                    
                    if axis == 'x':
                        x, y_top, y_bottom = line['x'], line['y_top'], line['y_bottom']
                        padding = 12
                        draw.rectangle(
                            [x-padding, y_top-padding, x+padding, y_bottom+padding],
                            fill=(30, 255, 30, 70)
                        )
                    else:
                        x_left, x_right, y = line['x_left'], line['x_right'], line['y']
                        padding = 12
                        draw.rectangle(
                            [x_left-padding, y-padding, x_right+padding, y+padding],
                            fill=(30, 255, 30, 70)
                        )
                    
                    glow_img = glow_img.filter(ImageFilter.GaussianBlur(9))
                    glow_photo = ImageTk.PhotoImage(glow_img)
                    
                    hover_item = canvas.create_image(0, 0, anchor='nw', image=glow_photo)
                    canvas.tag_lower(hover_item)
                    
                    if axis == 'x':
                        x_hover_item = hover_item
                        canvas.x_hover_photo = glow_photo
                    else:
                        y_hover_item = hover_item
                        canvas.y_hover_photo = glow_photo
                
                def on_line_leave(idx, axis):
                    nonlocal x_hover_item, y_hover_item
                    
                    if axis == 'x' and x_hover_item:
                        canvas.delete(x_hover_item)
                        x_hover_item = None
                    elif axis == 'y' and y_hover_item:
                        canvas.delete(y_hover_item)
                        y_hover_item = None
                
                def on_line_click(idx, axis):
                    nonlocal selected_x_line, selected_y_line, x_glow_item, y_glow_item, x_hover_item, y_hover_item
                    
                    # 清除悬停
                    if axis == 'x' and x_hover_item:
                        canvas.delete(x_hover_item)
                        x_hover_item = None
                    elif axis == 'y' and y_hover_item:
                        canvas.delete(y_hover_item)
                        y_hover_item = None
                    
                    # 清除之前的发光
                    if axis == 'x' and x_glow_item:
                        canvas.delete(x_glow_item)
                        x_glow_item = None
                    elif axis == 'y' and y_glow_item:
                        canvas.delete(y_glow_item)
                        y_glow_item = None
                    
                    lines = x_lines if axis == 'x' else y_lines
                    selected_ref = selected_x_line if axis == 'x' else selected_y_line
                    
                    # 恢复之前选中的线
                    if selected_ref:
                        if selected_ref['index'] == 5:
                            canvas.itemconfig(selected_ref['id'], fill='#ffffff')
                        else:
                            canvas.itemconfig(selected_ref['id'], fill='#ffffff')
                    
                    # 设置新选中的线
                    new_selected = lines[idx]
                    if axis == 'x':
                        selected_x_line = new_selected
                    else:
                        selected_y_line = new_selected
                    
                    # 变绿色
                    canvas.itemconfig(new_selected['id'], fill='#00ff00')
                    
                    # 创建发光效果
                    glow_img = Image.new("RGBA", (canvas.winfo_width(), canvas.winfo_height()), (0, 0, 0, 0))
                    draw = ImageDraw.Draw(glow_img)
                    
                    if axis == 'x':
                        x, y_top, y_bottom = new_selected['x'], new_selected['y_top'], new_selected['y_bottom']
                        padding = 6
                        draw.rectangle(
                            [x-padding, y_top-padding, x+padding, y_bottom+padding-5],
                            fill=(30, 255, 30, 200)
                        )
                    else:
                        x_left, x_right, y = new_selected['x_left'], new_selected['x_right'], new_selected['y']
                        padding = 6
                        draw.rectangle(
                            [x_left-padding, y-padding, x_right+padding, y+padding],
                            fill=(30, 255, 30, 200)
                        )
                    
                    glow_img = glow_img.filter(ImageFilter.GaussianBlur(4))
                    glow_photo = ImageTk.PhotoImage(glow_img)
                    
                    glow_item = canvas.create_image(0, 0, anchor='nw', image=glow_photo)
                    canvas.tag_lower(glow_item)
                    
                    if axis == 'x':
                        x_glow_item = glow_item
                        canvas.x_glow_photo = glow_photo
                        x_selected_label.configure(
                            text=f"X轴: {new_selected['value']:.1f} mm",
                            text_color='#00ff00'
                        )
                    else:
                        y_glow_item = glow_item
                        canvas.y_glow_photo = glow_photo
                        y_selected_label.configure(
                            text=f"Y轴: {new_selected['value']:.1f} mm",
                            text_color='#00ff00'
                        )
                
                # 选中值显示
                selection_frame = ctk.CTkFrame(main_frame, fg_color='#1a1a1a')
                selection_frame.pack(pady=0)
                
                x_selected_label = ctk.CTkLabel(
                    selection_frame,
                    text="X轴: 未选择",
                    font=("SimHei", 14),
                    text_color='#ffffff'
                )
                x_selected_label.pack(side="left", padx=20)
                
                y_selected_label = ctk.CTkLabel(
                    selection_frame,
                    text="Y轴: 未选择",
                    font=("SimHei", 14),
                    text_color='#ffffff'
                )
                y_selected_label.pack(side="left", padx=20)
                
                # 按钮框架
                button_frame = ctk.CTkFrame(main_frame, fg_color='#1a1a1a')
                button_frame.pack(pady=10)
                
                def confirm_selection():
                    if selected_x_line is None or selected_y_line is None:
                        error_msg = "请先选择X轴和Y轴的校准线！" if lang_setting != "EN" else "Please select both X and Y axis calibration lines!"
                        x_selected_label.configure(text=error_msg, text_color='#ff6666')
                        return
                    
                    x_value = float(selected_x_line['value'])
                    y_value = float(selected_y_line['value'])
                    
                    para.Temp_XOffset_Calibr = x_value
                    para.Temp_YOffset_Calibr = y_value
                    
                    if abs(para.Temp_XOffset_Calibr) < 0.09 and abs(para.Temp_YOffset_Calibr) < 0.09:
                        MKPMessagebox.show_info(
                            title='错误' if lang_setting != "EN" else 'Error',
                            message="校准值太小，请重新选择" if lang_setting != "EN" else "Calibration values too small, please select again"
                        )
                        return
                    
                    popup.destroy()
                    dialog.destroy()
                    
                    xy_save_option_value = xy_save_option.get() + ".toml"
                    documents_path = os.path.expanduser("~/Documents")
                    mkpsupport_path = os.path.join(documents_path, "MKPSupport")
                    xy_save_option_value = os.path.join(mkpsupport_path, xy_save_option_value)
                    
                    read_toml_config(xy_save_option_value)
                    Temp_Obsolete_XOffset = float(para.X_Offset)
                    Temp_Obsolete_YOffset = float(para.Y_Offset)
                    
                    para.X_Offset = Temp_Obsolete_XOffset + para.Temp_XOffset_Calibr
                    para.Y_Offset = Temp_Obsolete_YOffset + para.Temp_YOffset_Calibr
                    
                    write_toml_config(xy_save_option_value)
                    
                    show_info_dialog(
                        "结果" if lang_setting != "EN" else "Result",
                        f"XY轴偏移校准结果已保存到 {xy_save_option.get() + '.toml'}\n\n"
                        f"原 X 偏移值为: {Temp_Obsolete_XOffset:.2f}mm\n"
                        f"原 Y 偏移值为: {Temp_Obsolete_YOffset:.2f}mm\n\n"
                        f"新 X 偏移值为: {para.X_Offset:.2f}mm\n"
                        f"新 Y 偏移值为: {para.Y_Offset:.2f}mm"
                    )
                
                confirm_button = ctk.CTkButton(
                    button_frame,
                    text="确定" if lang_setting != "EN" else "Confirm",
                    command=confirm_selection,
                    font=("SimHei", 14),
                    width=100,
                    fg_color='#00aa00',
                    hover_color='#00ff00'
                )
                confirm_button.pack(side="left", padx=10)
                
                cancel_button = ctk.CTkButton(
                    button_frame,
                    text="取消" if lang_setting != "EN" else "Cancel",
                    command=popup.destroy,
                    font=("SimHei", 14),
                    width=100,
                    fg_color='#aa0000',
                    hover_color='#ff0000'
                )
                cancel_button.pack(side="left", padx=10)
                
                dialog.withdraw()
                
            def show_calibration_message():
                 # 创建一个顶层窗口作为弹窗
                popup = ctk.CTkToplevel(dialog)
                # popup.title("校准完成")
                if lang_setting!="EN":
                    popup.title("校准完成")
                else:
                    popup.title("Calibration Complete")
                popup.after(201, lambda :popup.iconbitmap(mkpicon_path))  # 解决某些系统图标不显示的问题
                popup.geometry("300x200")
                popup.geometry(CenterWindowToDisplay(popup, 300, 200, popup._get_window_scaling()))
                popup.maxsize(300, 200)
                popup.minsize(300, 200)
                popup.attributes("-topmost", True)  # 确保弹窗在最上层
                # 添加提示信息
                if lang_setting!="EN":
                    label = ctk.CTkLabel(popup, text="您的喷嘴笔尖高度差已经校准",font=("SimHei", 14))
                else:
                    label = ctk.CTkLabel(popup, text="Your nozzle tip height offset has been calibrated",font=  ("Segoe UI", 12),wraplength=250)
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
                popup.after(201, lambda :popup.iconbitmap(mkpicon_path))  # 解决某些系统图标不显示的问题
                popup.geometry("300x200")
                popup.geometry(CenterWindowToDisplay(popup, 300, 200, popup._get_window_scaling()))
                popup.maxsize(300, 200)
                popup.minsize(300, 200)
                popup.attributes("-topmost", True)  # 确保弹窗在最上层
                # 添加提示信息
                label = ctk.CTkLabel(popup, text="您的XY偏移值已经校准",font=("SimHei", 14))
                if lang_setting=="EN":
                    label = ctk.CTkLabel(popup, text="Your XY offset value has been calibrated",wraplength=250,font=("Segoe UI", 12))
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
                # dialog.title("喷嘴笔尖高度差校准")
                if lang_setting!="EN":
                    dialog.title("喷嘴笔尖高度差校准")
                else:
                    dialog.title("Nozzle Tip Height Offset Calibration")
                dialog.after(201, lambda :dialog.iconbitmap(mkpicon_path))  # 解决某些系统图标不显示的问题
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
                if lang_setting!="EN":
                    prompt_label = ctk.CTkLabel(frame, text="数字0所对应的平面在涂胶时是否出现未涂胶,涂胶过多,或涂胶时笔尖摇晃的问题?",font=("SimHei", 14))
                else:
                    prompt_label = ctk.CTkLabel(frame, text="Does the plane corresponding to digit 0 exhibit issues such as insufficient glue, excessive glue, or tip wobbling during gluing?",wraplength=500,font=("Segoe UI", 12))
                # prompt_label = ctk.CTkLabel(frame, text="数字0所对应的平面在涂胶时是否出现未涂胶,涂胶过多,或涂胶时笔尖摇晃的问题?",font=("SimHei", 14))
                prompt_label.pack(pady=10)
                button_frame = ctk.CTkFrame(frame,fg_color="transparent")
                button_frame.pack(pady=10)
                # "存在"按钮
                exist_button = ctk.CTkButton(
                    button_frame,
                    text="存在",
                    font=("SimHei", 14),
                    command=continue_function
                )
                if lang_setting!="EN":
                    exist_button.configure(text="存在")
                else:
                    exist_button.configure(text="YES",font=("Segoe UI", 14))
                exist_button.pack(pady=10,side="right", padx=5)

                # "不存在"按钮
                not_exist_button = ctk.CTkButton(
                    button_frame,
                    text="不存在",
                    font=("SimHei", 14),
                    command=show_calibration_message
                )
                if lang_setting!="EN":
                    not_exist_button.configure(text="不存在")
                else:
                    not_exist_button.configure(text="NO",font=("Segoe UI", 14))
                not_exist_button.pack(pady=10, side="right", padx=5)
              
            elif filename == "Precise Calibration.3mf":
                if lang_setting!="EN":
                    dialog.title("XY偏移值校准")
                else:
                    dialog.title("XY Offset Calibration")
                # dialog.title("XY偏移值校准")
                dialog.after(201, lambda :dialog.iconbitmap(mkpicon_path))  # 解决某些系统图标不显示的问题
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
                if lang_setting!="EN":
                    prompt_label = ctk.CTkLabel(frame, text="涂胶时,笔尖的移动轨迹完全重合的横线或纵线是否是中央0线?",font=("SimHei", 14))
                else:
                    prompt_label = ctk.CTkLabel(frame, text="During gluing, does the line that perfectly overlaps with the tip's movement trajectory correspond to the central 0 line?",wraplength=500,font=("Segoe UI", 14))
                # prompt_label = ctk.CTkLabel(frame, text="涂胶时,笔尖的移动轨迹完全重合的横线或纵线是否是中央0线?",font=("SimHei", 14))
                prompt_label.pack(pady=10)
                button_frame = ctk.CTkFrame(frame,fg_color="transparent")
                button_frame.pack(pady=10)
                # "存在"按钮
                exist_button = ctk.CTkButton(
                    button_frame,
                    text="否",
                    font=("SimHei", 14),
                    command=xy_continue_function
                )
                if lang_setting=="EN":
                    exist_button.configure(text="NO",font=("Segoe UI", 14))
                exist_button.pack(pady=10,side="right", padx=5)

                # "不存在"按钮
                not_exist_button = ctk.CTkButton(
                    button_frame,
                    text="是",
                    font=("SimHei", 14),
                    command=show_calibration_message_xy
                )
                if lang_setting=="EN":
                    not_exist_button.configure(text="YES",font=("Segoe UI", 14))
                not_exist_button.pack(pady=10, side="right", padx=5)
                pass
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

        def show_info_dialog(title, message):
            """自定义信息弹窗"""
            # 创建弹窗
            dialog = ctk.CTkToplevel()
            dialog.title(title)  # 设置标题
            dialog.after(201, lambda :dialog.iconbitmap(mkpicon_path))  # 解决某些系统图标不显示的问题
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
            show_calibration_prompt("ZOffset Calibration.3mf")
        def save_xy_offset():
            show_calibration_prompt("Precise Calibration.3mf")


    selected_toml = ctk.StringVar()
    
    def on_confirm():
        para.Preset_Name = selected_toml.get()
        #然后再删去前面的路径部分，只保留预设名称和扩展名
        #para.preset_name保存到mkp_config.toml的last_selected_preset字段中，以便下次启动时默认选择该预设
        def write_last_selected_preset(preset_name):
            config_path = mkp_config_path
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = toml.load(f)
            else:
                config_data = {}
            temp_pset_name = os.path.basename(preset_name)  # 获取文件名部分
            config_data['last_selected_preset'] = temp_pset_name
            print(f"写入上次选择的预设: {temp_pset_name} 到配置文件.")
            with open(config_path, 'w', encoding='utf-8') as f:
                toml.dump(config_data, f)
        try:
            write_last_selected_preset(para.Preset_Name)
        except Exception as e:
            MKPMessagebox.show_info("错误", f"写入上次选择的预设时出现错误: {str(e)}")
        #copy_user_command()这个函数是为了弹出复制窗口，但是可能会有问题，我现在要给出异常捕获
        try:
            copy_user_command()
        except Exception as e:
            #做新的对话框提示
            MKPMessagebox.show_info("错误", f"复制用户命令时出现错误: {str(e)}")
        selection_dialog.destroy()
    
    def on_delete():
        selected_file = selected_toml.get()
        if selected_file:
            if lang_setting!="EN":
                confirm =MKPMessagebox.show_info("确认删除", f"确定要删除预设: {os.path.basename(selected_file)}吗?",["确定","取消"])
            else:
                confirm =MKPMessagebox.show_info("Confirm Deletion", f"Are you sure you want to delete the preset: {os.path.basename(selected_file)}?",["YES","NO"])
            # confirm =CTkMessagebox(title="确认删除", message=f"确定要删除预设: {os.path.basename(selected_file)}吗?",
            #             icon="question", option_1="取消", option_2="确定",bg_color=("white","black"),fg_color=("#e1e6e9","#343638"),border_width=1,font=("SimHei",15),border_color=("#d1d1d1","#3a3a3a"))
            # 只有当用户点击"确定删除"时才执行删除
            if confirm== "确定" or confirm=="YES":
                os.remove(selected_file)
                refresh_preset_frame_list()  # 刷新列表
                
                update_mkp_presets()

                # refresh_toml_list()
                # fetch_mkp_presets():
                # selection_dialog.update()
    
                


    
    def on_edit():
        selected_file = selected_toml.get()
        read_toml_config(selected_file)
        get_preset_values("Modify")
        if para.Unsafe_Close_Flag==False:
            write_toml_config(selected_file)
    
    def on_new():
        if lang_setting!="EN":
            dialog = ctk.CTkInputDialog(title="新建预设", text="请输入新预设的名称:",font=("SimHei",15))
        else:
            dialog = ctk.CTkInputDialog(title="New Preset", text="Please enter the name of the new preset:",font=("Segoe UI",15))
        dialog.after(201, lambda :dialog.iconbitmap(mkpicon_path))  # 解决某些系统图标不显示的问题
        dialog.geometry(CenterWindowToDisplay(dialog, 400, 150, dialog._get_window_scaling()))
        new_preset_name = dialog.get_input()
        if new_preset_name:
            para.Preset_Name = new_preset_name
            mkpsupport_path = os.path.join(create_mkpsupport_dir(), f"{new_preset_name}.toml")
            get_preset_values("Normal")
            write_toml_config(mkpsupport_path)
            refresh_toml_list()
    
    refresh_toml_list()
    # selection_dialog.after(1, lambda:selection_dialog.attributes("-alpha", 0.23))
    # selection_dialog.after(100, lambda:selection_dialog.attributes("-alpha", 0.43))
    # selection_dialog.after(200, lambda:selection_dialog.attributes("-alpha", 0.63))
    # selection_dialog.after(100, lambda:selection_dialog.attributes("-alpha", 0.83))
    # selection_dialog.after(200, lambda:selection_dialog.attributes("-alpha",0.93))
    #采用after实现更为平滑的淡入效果，最大是0.93
    def fade_in(step=0.05, delay=60):
        current_alpha = selection_dialog.attributes("-alpha")
        # if current_alpha < 0.93:
        #     new_alpha = min(current_alpha + step, 0.93)
        #     selection_dialog.attributes("-alpha", new_alpha)
        #     selection_dialog.after(delay, fade_in, step, delay)
        # 有一点不好：我想要在前半段慢，后半段快一点
        if current_alpha < 0.93:
            if current_alpha < 0.2:
                step = 0.05
            else:
                step = 0.3
            new_alpha = min(current_alpha + step, 0.93)
            selection_dialog.attributes("-alpha", new_alpha)
            selection_dialog.after(delay, fade_in, step, delay)
    fade_in()
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
        if para.Interface_ironing_Flag==False:
            #如果最后一行是一个既含有（G1 X或者G1 Y）又含有F,且不含有E的行，那么把它删去
            if (interface[-1].find("G1 X") != -1 or interface[-1].find("G1 Y") != -1 ) and interface[-1].find("F") != -1 and interface[-1].find("E") == -1:
                interface=interface[:-1]#这一行肯定是空驶，删掉
            #在末尾添加一个跳Z标记
            interface.append(";ZJUMP_START")
        if para.Interface_ironing_Flag==True:
            interface.append(";ZJUMP_START")

    #接下来查找interface中是否还有;WIPE_END，在每一个;WIPE_END之前都添加一个;ZJUMP_START
    for i in range(len(interface)-1,-1,-1):
        if interface[i].find("; WIPE_END") != -1:
            interface.insert(i+1,";ZJUMP_START")
            break

    if para.Interface_ironing_Flag==True:
        #此时interface中会存在一种特殊的情形：打印完成一小段熨烫后不作wipe而是直接空驶去下一处。这种情况的特征是：G1 X开头，并且含有F，Z，不含有E。它的下一行会描述另外一个点，这个点会描述Z高度。
        #这种情况下，应该这样处理：对于这个行，删除之并添加;ZJUMP_START,对于它的下一行，移除z字符（包括其本身）后的所有内容.这种跳Z可能存在多次
        Temp_interface=[]
        for i in range(len(interface)):
            if (interface[i].find("G1 X") != -1 or interface[i].find("G1 Y") != -1 ) and interface[i].find("F") != -1 and interface[i].find("Z") != -1 and interface[i].find("E") == -1:
                interface[i]=";ZJUMP_START"
                interface[i+1]=interface[i+1][:interface[i+1].find("Z")]
            #另外一种情况：没有含有F，但是含有Z。其余不变.如果其下一行以“G1 Z”开头，那么,不删除本行，但是在本行之前插入;ZJUMP_START，同时本行内容移除Z字符（包括其本身）后的所有内容
            elif interface[i].find("G1 X") != -1 and interface[i].find("Z") != -1 and interface[i].find("E") == -1:
                if interface[i+1].find("G1 Z") != -1:
                    Temp_interface.append(";ZJUMP_START")
                    interface[i]=interface[i][:interface[i].find("Z")]
            Temp_interface.append(interface[i])
        interface=Temp_interface[:]
        Temp_interface.clear()
    return interface


def main():
    global window,text_label_loading
    if CCkcheck_flag!=True:
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
    Walls=[]
    Bridges=[]
    Collision_Walls=[]
    Supports=[]
    Collision_Check=[]
    Gcode_Storage = []#临时存储GCode
    InterFace_Moisture = []#存储接触面
    Copy_Flag_Moisture=False
    Find_Last_XY_In_This_Layer_Flag=True#是否已经找到最后一个XY命令了
    XY_Moisture_Command=""
    This_Layer_Have_Too_Low_Extrusion=False
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
    if para.Custom_Mount_Gcode.find("NOCOOLDOWN") != -1 and para.Custom_Mount_Gcode.find(";L803") == -1:
        #用户指定降温
        para.L803_Leak_Pervent_Flag = False
    else:
        para.L803_Leak_Pervent_Flag = True
    #读取当前的等待值
    if para.Custom_Unmount_Gcode.find("G4") != -1:
        for line in para.Custom_Unmount_Gcode.strip("\n").split("\n"):
            if line.find("G4") != -1:
                para.Wait_for_Drying_Command= line
                break
    #读取MKP要求的回抽
    if para.Custom_Mount_Gcode.find("G1 E") != -1:
        for line in para.Custom_Mount_Gcode.strip("\n").split("\n"):
            if line.find("G1 E") != -1:
                para.MKPRetract=Num_Strip(line)[1]
                if para.MKPRetract>0:
                    para.MKPRetract=-para.MKPRetract
                break
    
    #读取MKP的填充回抽命令
    if para.Custom_Unmount_Gcode.find("G1 E") != -1:
        for line in para.Custom_Unmount_Gcode.strip("\n").split("\n"):
            if line.find("G1 E") != -1 and "Wipe" not in line:
                para.Refill_Extrude_Command = line
                print("MKP填充回抽命令:",line)
                break
    if para.Custom_Unmount_Gcode.find("SILICONE_WIPE") != -1 and para.Custom_Unmount_Gcode.find(";SILICONE_WIPE") == -1 and para.Use_Wiping_Towers.get()!=True:
        para.Silicone_Wipe_Flag=False
    else:
        para.Silicone_Wipe_Flag=False
    

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
            para.Wall_Print_Speed = Num_Strip(CurrGCommand)[0]
            # para.WipeTower_Print_Speed = Num_Strip(CurrGCommand)[0]
            # para.WipeTower_Print_Speed=para.WipeTower_Print_Speed*0.6
            Diameter_Count+=1
        if CurrGCommand.find("; retraction_length = ") != -1 and para.Retract_Length==0:
            para.Retract_Length = Num_Strip(CurrGCommand)[0]
            Diameter_Count+=1
        if CurrGCommand.find("; nozzle_temperature = ") != -1:
            para.Nozzle_Switch_Tempature = Num_Strip(CurrGCommand)[0]
            Diameter_Count+=1
        if CurrGCommand.find("; nozzle_diameter = ") != -1:
            Temp_Nozzle_frisk = Num_Strip(CurrGCommand)[0]
            if Temp_Nozzle_frisk<=0.3 and Temp_Nozzle_frisk>=0.15:
                para.Minor_Nozzle_Diameter_Flag = True
        if CurrGCommand.find("; filament_settings_id ") != -1:
            if CurrGCommand.find("PETG")!=-1 or CurrGCommand.find("petg")!=-1:
                para.Filament_Type = "PETG"
            elif CurrGCommand.find("ABS")!=-1 or CurrGCommand.find("abs")!=-1 or CurrGCommand.find("PA6")!=-1 or CurrGCommand.find("pa6")!=-1 or CurrGCommand.find("nylon")!=-1 or CurrGCommand.find("-CF")!=-1 or CurrGCommand.find("-cf")!=-1:
                para.Filament_Type = "ABS"
            elif CurrGCommand.find("TPU")!=-1 or CurrGCommand.find("tpu")!=-1:
                para.Filament_Type = "TPU"
            else:
                para.Filament_Type = "PLA"
        if CurrGCommand.find("; support_interface_speed = ") != -1:
            para.Support_Interface_Speed = Num_Strip(CurrGCommand)[0]
        if CurrGCommand.find("; enable_support_ironing = ") != -1:
            if Num_Strip(CurrGCommand)[0]==1:
                para.Interface_ironing_Flag=True
            else:
                para.Interface_ironing_Flag=False
            print("para.Interface_ironing_Flag:",para.Interface_ironing_Flag)
        if CurrGCommand.find("; support_type = ") != -1:
            if CurrGCommand.find("tree")!=-1:
                para.Tree_Support_Flag=True
            else:
                para.Tree_Support_Flag=False
        if CurrGCommand.find("; filament_retraction_length = ")!=-1:
            para.Retract_Length = Num_Strip(CurrGCommand)[0]
        if CurrGCommand.find("; CONFIG_BLOCK_END")!=-1:
            break
    
    with open(GSourceFile, 'r', encoding='utf-8') as file:
        content = file.readlines()
    Output_Filename = GSourceFile + "_Output.gcode"
    TempExporter = open(Output_Filename+'.te', "w", encoding="utf-8")
    Inconsistent_Count=47#用来记录没有涂胶的层数
    This_Layer_is_First_Layer_Revitalization=False
    #第一次循环。这个循环的主要任务是输出涂胶和熨烫，记录接触面的轨迹方便下一次循环的预涂胶
    Temp_Rebuild_Pressure=[]
    if para.Interface_ironing_Flag==True:
        para.Slicer="OrcaSlicer"
    else:
        para.Slicer="BambuStudio"#强制指定为BambuStudio切片
    if para.Tree_Support_Flag==True:
        para.Support_Extrusion_Multiplier=1.27
    #总切片进度
    para.progress_calc= len(content)
    #获取text_label_loading的当前的文本变量
    cccl=text_label_loading.cget("text")
    print( cccl)
    text_label_loading.configure(text="\n\n\n\n\n\n\n正在生成Gcode路径:0%")
    if lang_setting=="EN":
        text_label_loading.configure(text="\n\n\n\n\n\n\nGenerating Gcode Path:0%")
    cccl=text_label_loading.cget("text")
    print( cccl)
    window.update()

    #检查擦嘴塔是否可能和模型重叠。现在提取GCODE的带有E挤出和XY移动的G1命令，得出四至点（X最大，最小，Y最大，最小），如果擦嘴塔的坐标在这个范围内，就弹窗警告用户可能会有问题
    Start_Index=0
    E_Index=0
    for i in range(len(content)):
        if content[i].startswith("; layer num/total_layer_count: 1"):
            Start_Index=i
            break
    for i in range(len(content)-1,-1,-1):
        if content[i].startswith("; layer num/total_layer_count:"):
            End_Index=i
            break
    print(f"Start_Index:{Start_Index},End_Index:{End_Index}")
    Allow_Calculate_Flag=True

    # 初始化变量
    conflict_points = []  # 存储冲突点
    cal_points = []  # 存储计算点
    conflict_count = 0    # 冲突点计数
    processed_count = 0  # 处理计数器
    Allow_Calculate_Flag = False

    # 动态调整抽样间隔
    total_lines = End_Index - Start_Index
    if total_lines > 10000:
        sample_interval = 500  # 每50个点取一个
        max_cal_points = 500  # 最多200个抽样点
    elif total_lines > 5000:
        sample_interval = 150  # 每30个点取一个
        max_cal_points = 150
    else:
        sample_interval = 50  # 每20个点取一个
        max_cal_points = 100

    # 首先找到冲突点
    for i in range(Start_Index, End_Index):
        CurrGCommand = content[i].strip("\n")
        
        # FEATURE类型检测
        if CurrGCommand.startswith("; FEATURE"):
            if (CurrGCommand.startswith("; FEATURE: Outer wall") or 
                CurrGCommand.startswith("; FEATURE: Brim") or CurrGCommand.startswith("; FEATURE: Support")):
                Allow_Calculate_Flag = True
            else:
                Allow_Calculate_Flag = False
            continue
        
        # 跳过非检测区域
        if not Allow_Calculate_Flag:
            continue
        
        # 检测G1 X移动指令（带挤出）
        if CurrGCommand.startswith("G1 X") and " E" in CurrGCommand:
            try:
                X_Coord = Num_Strip(CurrGCommand)[1]
                Y_Coord = Num_Strip(CurrGCommand)[2]

                processed_count += 1
                # ====== 系统抽样（每N个点取一个） ======
                if processed_count % sample_interval == 0 and len(cal_points) < max_cal_points:
                    cal_points.append((X_Coord, Y_Coord))

                # 检查是否在擦嘴塔范围内
                if (para.Wiper_x - 3 <= X_Coord <= para.Wiper_x + 26 and 
                    para.Wiper_y - 3 <= Y_Coord <= para.Wiper_y + 26):
                    
                    conflict_points.append((X_Coord, Y_Coord))
                    conflict_count += 1
                    
                    # 抽样：每10个点记录一个，避免内存过大
                    if conflict_count % 10 == 0 and len(conflict_points) < 100:
                        conflict_points.append((X_Coord, Y_Coord))
                        
            except:
                pass

    # 判断是否有冲突
    if conflict_count > 0 and para.Use_Wiping_Towers.get()==True:
        print(f"⚠️ 检测到 {conflict_count} 个冲突点")
        
        # 粗略计算冲突区域的中心点（如果有采样点）
        if conflict_points:
            # 计算冲突点的平均位置
            avg_x = sum(p[0] for p in cal_points) / len(cal_points)
            avg_y = sum(p[1] for p in cal_points) / len(cal_points)
            
            # 计算擦嘴塔的中心点
            wipe_center_x = (para.Wiper_x - 1 + para.Wiper_x + 24) / 2
            wipe_center_y = (para.Wiper_y - 1 + para.Wiper_y + 24) / 2
            
            print(f"冲突区域中心: ({avg_x:.1f}, {avg_y:.1f})")
            print(f"擦嘴塔中心: ({wipe_center_x:.1f}, {wipe_center_y:.1f})")
            X_Move_Direction=""
            Y_Move_Direction=""
            X_Move_Direction = "right" if avg_x > wipe_center_x else "left"
            Y_Move_Direction = "up" if avg_y > wipe_center_y else "down"
            # 定义映射
            direction_map = {
                ("", "up"): ("upward", "向上"),
                ("", "down"): ("downward", "向下"),
                ("right", ""): ("rightward", "向右"),
                ("left", ""): ("leftward", "向左"),
                ("right", "up"): ("upward rightward", "向右上"),
                ("right", "down"): ("downward rightward", "向右下"),
                ("left", "up"): ("upward leftward", "向左上"),
                ("left", "down"): ("downward leftward", "向左下"),
            }

            # 一行获取结果
            if (X_Move_Direction, Y_Move_Direction) in direction_map:
                en, cn = direction_map[(X_Move_Direction, Y_Move_Direction)]
                MKPMessage_DIRECTION = en if lang_setting == "EN" else cn
            else:
                MKPMessage_DIRECTION = ""
            if MKPMessage_DIRECTION!="":
                window.attributes("-topmost", False)  # 使窗口保持在最前端
                window.withdraw()#先隐藏主窗口再弹窗，这样用户就不会看到主窗口的闪烁
                if lang_setting!="EN":
                    # window.destroy()#销毁主窗口
                    MKPMessagebox.show_info("警告", "模型可能和擦嘴塔重叠。请尝试"+MKPMessage_DIRECTION+"调整模型位置","OK")
                    #试图使得MKPMessagebox最前方显示,应该怎么做》
                else:
                    MKPMessagebox.show_info("Warning", "Your model may overlap with the wiping tower. Please try adjusting the model position "+MKPMessage_DIRECTION,"OK")
                exit(0)#直接退出程序，避免用户继续操作
    else:
        print("✅ 模型与擦嘴塔无冲突")
    
    for i in range(len(content)):
        #每当i%1000==0时，更新一次进度
        if i%20000==0:
            progress_percent=int((i/para.progress_calc)*100)
            # text_label_loading.configure(text=f"\n\n\n\n\n\n\n正在生成Gcode路径:{progress_percent}%")
            if lang_setting=="EN":
                text_label_loading.configure(text=f"\n\n\n\n\n\n\nGenerating Gcode Path:{progress_percent}%")
            else:
                text_label_loading.configure(text=f"\n\n\n\n\n\n\n正在生成Gcode路径:{progress_percent}%")
            window.update()
        CurrGCommand = content[i].strip("\n")
        # if CurrGCommand.startswith("; BambuStudio"):
        #     para.Slicer="BambuStudio"
        if ( CurrGCommand.find("G1 X") != -1 or CurrGCommand.find("G1 Y") != -1 ) and CurrGCommand.find("E") == -1 and Last_XY_Command_FE_Flag:
            last_xy_command_in_other_features=CurrGCommand
        if CurrGCommand.find("; Z_HEIGHT: ") != -1:
            Last_Layer_Height = Current_Layer_Height
            Current_Layer_Height = Num_Strip(CurrGCommand)[0]
            Layer_Thickness=Current_Layer_Height-Last_Layer_Height
            Inconsistent_Count+=1
            Find_Last_XY_In_This_Layer_Flag=True
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
            para.Machine_Max_X=260
            para.Machine_Min_X=-40
            para.Machine_Max_Y=255
            para.Machine_Min_Y=0
            Read_MachineType_Flag=False
        if Read_MachineType_Flag and CurrGCommand.find(";===== machine: X1") != -1:
            MachineType_Main = "X1"
            para.Machine_Max_X=255
            para.Machine_Min_X=0
            para.Machine_Max_Y=265
            para.Machine_Min_Y=0
            Read_MachineType_Flag=False
        if Read_MachineType_Flag and CurrGCommand.find(";===== machine: A1 mini") != -1:
            MachineType_Main = "A1mini"
            para.Machine_Max_X=180
            para.Machine_Min_X=-10
            para.Machine_Max_Y=180
            para.Machine_Min_Y=0
            Read_MachineType_Flag=False
        if Read_MachineType_Flag and CurrGCommand.find(";===== machine: P1") != -1:
            MachineType_Main = "P1Lite"
            para.Machine_Max_X=255
            para.Machine_Min_X=0
            para.Machine_Max_Y=265
            para.Machine_Min_Y=0
            Read_MachineType_Flag=False
        if Read_MachineType_Flag and CurrGCommand.find(";======== P2S start gcode==========") != -1:
            MachineType_Main = "P1Lite"
            para.Machine_Max_X=255
            para.Machine_Min_X=0
            para.Machine_Max_Y=265
            para.Machine_Min_Y=0
            Read_MachineType_Flag=False



        if CurrGCommand.find("; FEATURE:") != -1:
            Local_Feature=CurrGCommand
      
        if CurrGCommand.find("; FEATURE: Support interface") != -1 and para.Slicer=="BambuStudio":
            Copy_Flag=True
            Start_Index=i
            Last_XY_Command_FE_Flag=False
            # print(";LSTXY:"+last_xy_command_in_other_features)
            # print("start_index:",Start_Index)
        if Copy_Flag==True and CurrGCommand.find("; CHANGE_LAYER") != -1 and para.Slicer=="BambuStudio":
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
        if CurrGCommand.find("; FEATURE:")!=-1 and CurrGCommand.find("; FEATURE: Support interface") == -1 and Copy_Flag and para.Slicer=="BambuStudio":#这是另外一种挤出
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

        if CurrGCommand.find("; FEATURE: Support interface") != -1 and para.Interface_ironing_Flag==True:# Moisture
            Copy_Flag_Moisture=True
            Start_Index_Moisture=i
            if Find_Last_XY_In_This_Layer_Flag==True:
                # InterFace_Moisture.clear()
                #从Start_Index_Moisture开始向前倒查最近的一个G1 X 不含E
                for j in range(Start_Index_Moisture-1,0,-1):
                    if content[j].find("G1 X") != -1 and content[j].find("E") == -1:
                        if content[j].find("Z") != -1:
                            #切掉
                            content[j]=content[j][:content[j].find("Z")]
                        XY_Moisture_Command=content[j]
                        Find_Last_XY_In_This_Layer_Flag=False
                        break

        if CurrGCommand.find("; FEATURE:")!=-1 and CurrGCommand.find("; FEATURE: Support interface") == -1 and Copy_Flag_Moisture and para.Interface_ironing_Flag==True:# Moisture
            Copy_Flag_Moisture=False
            End_Index_Moisture=i-1
            

            for i in range(Start_Index_Moisture, End_Index_Moisture): 
                if content[i].find("M620 S") != -1:
                    End_Index_Moisture=i-1
                    break
            # if Inconsistent_Count>5:
            InterFace_Moisture.extend(delete_wipe(content[Start_Index_Moisture:End_Index_Moisture]))
        if CurrGCommand.find("; FEATURE: Support ironing") != -1 and para.Interface_ironing_Flag==True:
            print(";Support ironing",file=TempExporter)
            Copy_Flag=True
            Start_Index=i
            Last_XY_Command_FE_Flag=False
            #从这里开始检索，直到下一次的type切换为止，对这两次之间的content[i]执行累加。如果E_Sum>5，把Iron_Act_Flag设为False,防止太大的熨烫导致堵头
            E_Sum=0
            for j in range(i+1,len(content)):
                Temp_Line=content[j]
                if Temp_Line.find("; FEATURE:") != -1 and Temp_Line.find("; FEATURE: Support ironing") == -1:
                    break
                if (Temp_Line.find("G1 X") != -1 or Temp_Line.find("G1 Y") != -1) and Temp_Line.find("E") != -1:
                    #检查字母E后面是数字还是“.”,如果是数字直接读取，如果是“.”，说明是0.XXX的形式，前面没有整数部分，补0
                    if Temp_Line[Temp_Line.find("E")+1].isdigit():
                        #切掉字母E前面的部分（包括字母E）
                        Temp_E_num=Temp_Line[Temp_Line.find("E")+1:]
                        # print(";E_NUM:"+str(Num_Strip(Temp_E_num)[0]))
                    elif Temp_Line[Temp_Line.find("E")+1]==".":
                        Temp_E_num="0."+Temp_Line[Temp_Line.find("E")+2:]
                        # print(";E_NUM:"+str(Num_Strip(Temp_E_num)[0]))
                        E_Sum+=Num_Strip(Temp_E_num)[0]
            E_Sum=round(E_Sum,3)
            # print(";E_Sum for ironing segment:"+str(E_Sum))
            if E_Sum<0.1:
                #说明挤出量实在太低，必须强制使用全涂
                # InterFace.extend("Warning, Too low extrusion for ironing segment.")
                This_Layer_Have_Too_Low_Extrusion=True
            if This_Layer_Have_Too_Low_Extrusion and E_Sum>0.15:
                This_Layer_Have_Too_Low_Extrusion=False
            if E_Sum>7.9:
                # Copy_Flag=False
                print("G1 E-"+str(para.Retract_Length), file=TempExporter)#回抽
                para.Ironing_Removal_Flag=True

                # tk.messagebox.showwarning(title='警报', message="熨烫部分挤出过多，已自动取消熨烫。挤出量:"+str(E_Sum))
                print(";Warning: Excessive ironing detected. Ironing cancelled. E_Sum="+str(E_Sum), file=TempExporter)    
        if CurrGCommand.find("; FEATURE:")!=-1 and CurrGCommand.find("; FEATURE: Support ironing") == -1 and Copy_Flag and para.Interface_ironing_Flag==True:
            print(";Find different feature:",file=TempExporter)
            Copy_Flag=False
            if para.Ironing_Removal_Flag==True:
                para.Ironing_Removal_Flag=False
                # print("G1 Z"+str(round(Current_Layer_Height+1,3))+";Skip Ironing", file=TempExporter)
                #从content的当前i向前回溯到最近一个有G1 X或者G1 Y的行，存储为XY_load_temp
                for k in range(i-1,-1,-1):
                    if content[k].find("G1 X") != -1 or content[k].find("G1 Y") != -1:
                        XY_load_temp=content[k].strip("\n")
                        break
                if XY_load_temp.find("Z")!=-1:
                    print(XY_load_temp, file=TempExporter)
                else:
                    print("G1 Z"+str(round(Current_Layer_Height+1,3))+";Skip Ironing", file=TempExporter)
                    print(XY_load_temp, file=TempExporter)

                #Z恢复原位
                print("G1 Z"+str(round(Current_Layer_Height,3)), file=TempExporter)    
                print("G1 E"+str(para.Retract_Length), file=TempExporter)#恢复回抽
            Copy_Flag=False
            End_Index=i-1
            for i in range(Start_Index, End_Index): 
                if content[i].find("M620 S") != -1:
                    End_Index=i-1
                    break
            InterFace.extend(delete_wipe(content[Start_Index:End_Index]))
            # print(InterFace)
            # exit(0)
            Temp_InterFace_Frisk = []
            Temp_InterFace_Frisk.extend(InterFace)
            if check_validity_interface_set(Temp_InterFace_Frisk) == True:
                Act_Flag=True
                Temp_InterFace_Frisk.clear()
            else:
                InterFace.clear()

        if CurrGCommand.startswith("; FEATURE: "):
            para.Last_Feature=CurrGCommand
        #如果这个para.Move_Walls_Height为真，并且接下来遇到外墙的指令，就把这些指令全部存储起来。先从本行向后查找，找到最近的一个以"; layer num/total_layer_count"开头的行，记录这个行数为End_Index
        #然后把在本行和end_index之间的全部InnerWall和OuterWall的指令存储起来，直到i到end_index的时候释放出来，全部释放之后把para.Move_Walls_Height设为False，等待下一次遇到"; layer num/total_layer_count"开头的行
        # if para.Move_Walls_Height+0.35>Current_Layer_Height and Current_Layer_Height!=para.First_Layer_Height: 
        #     if CurrGCommand.startswith("G1 X") and (not "E" in CurrGCommand):
        #         if content[i+1].startswith("G1 Z"):
        #             #如果是特殊情况，para.Need_to_append_silent_Wall_Flag是真，那么重置为false，同时把para.Avoid_Wall_Export_Flag为真
        #             if para.Need_to_append_silent_Wall_Flag==True:
        #                 para.Need_to_append_silent_Wall_Flag=False
        #                 para.Avoid_Wall_Export_Flag=True
        #                 print(";Silent Wall", file=TempExporter)
        #                 Walls.append("; FEATURE: Outer wall")
        #             #从这里往后查找，如果在6行以内找到InnerWall或者OuterWall的指令，就发出警报
        #             for j in range(i+1, min(i+7, len(content))):
        #                 if content[j].find("; FEATURE: Outer wall") != -1 or content[j].find("; FEATURE: Inner wall") != -1 or content[j].find("; FEATURE: Gap infill") != -1:
        #                     print(";Walls Ahead!", file=TempExporter)
        #                     para.Avoid_Wall_Export_Flag=True
        #                     Walls.append("G1 F" + str(para.Travel_Speed*60)+";Wall Move Command")
        #                     break
        #         elif content[i+1].find("; FEATURE: Outer wall") != -1 or content[i+1].find("; FEATURE: Inner wall") != -1 or content[i+1].find("; FEATURE: Gap infill") != -1:
        #             print(";Walls Ahead!", file=TempExporter)
        #             para.Avoid_Wall_Export_Flag=True
        #     if para.Allow_Temp_Export_Flag==False and CurrGCommand.startswith("G1 X") and (not "E" in CurrGCommand):
        #         if content[i+1].startswith("G1 Z"):
        #             for j in range(i+1, min(i+7, len(content))):
        #                 if content[j].find("; FEATURE:") != -1 and (not content[j].startswith("; FEATURE: Outer wall") ) and (not content[j].startswith("; FEATURE: Inner wall")) and (not content[j].startswith("; FEATURE: Gap infill")):
        #                     print(";Different Extrusion!", file=TempExporter)
        #                     para.Avoid_Wall_Export_Flag=False
        #                     break
        #                 else:
        #                     Walls.append(CurrGCommand)
        #         elif content[i+1].find("; FEATURE:")!=-1 and (not content[i+1].startswith("; FEATURE: Outer wall") ) and (not content[i+1].startswith("; FEATURE: Inner wall")) and (not content[i+1].startswith("; FEATURE: Gap infill")):
        #             print(";Different Extrusion!", file=TempExporter)
        #             para.Avoid_Wall_Export_Flag=False
        #         else:
        #             Walls.append(CurrGCommand)
        #     elif para.Avoid_Wall_Export_Flag==True:
        #         Walls.append(CurrGCommand)

        # if CurrGCommand.find("; CHANGE_LAYER") != -1:
        #     if Walls!=[]:
        #         para.Avoid_Wall_Export_Flag=False

        #         if content[i+3].startswith("; WIPE_START") and (not(para.Last_Feature=="; FEATURE: Outer wall" or para.Last_Feature=="; FEATURE: Inner wall" or para.Last_Feature=="; FEATURE: Gap infill")):
        #             # print('; MKPWiper Start',file=TempExporter)
        #             # print(";Last Feature is "+para.Last_Feature,file=TempExporter)
        #             #从这里开始向下找，直到找到一个以"; WIPE_END"开头的行。把里面的东西提前取出
        #             for j in range(i+3, len(content)):
        #                 print(content[j].strip("\n"), file=TempExporter)
        #                 # content[j]=";"+content[j]
        #                 if content[j-1].startswith("; WIPE_END"):
        #                     break
        #             para.Wipe_remove_flag=1
        #             # print('; MKPWiper End',file=TempExporter)

        #         print(";Walls Released", file=TempExporter)
        #         print("; LAYER_HEIGHT: "+str(para.Typical_Layer_Height), file=TempExporter)
        #         for i in range(len(Walls)):
        #             #直接把Walls里面的指令发出
        #             print(Walls[i], file=TempExporter)
        #         Walls.clear()
        #     if para.Last_Feature=="; FEATURE: Outer wall" or para.Last_Feature=="; FEATURE: Inner wall":
        #         #说明最后一次的 extrusion是外墙或者内墙，那么就发出警告，因为下一次可能不会移动它，但是理应是移动它
        #         # print(";The last extrusion is a wall, but the next layer is not moving it!", file=TempExporter)
        #         para.Need_to_append_silent_Wall_Flag=True

        # if para.Wipe_remove_flag==1 and CurrGCommand.startswith("; WIPE_START"):
        #     para.Wipe_remove_flag=2
        # if para.Wipe_remove_flag==2 and CurrGCommand.startswith("; WIPE_END"):
        #     para.Wipe_remove_flag=0

        if CurrGCommand.find("; layer num/total_layer_count") != -1 and Act_Flag:
            # para.Move_Walls_Height=Current_Layer_Height 
            # print(";Next layer Needs to Move Walls", file=TempExporter)
            if Inconsistent_Count>0:
                Inconsistent_Count-=1
            else:
                Inconsistent_Count=0
            Last_XY_Command_FE_Flag=True
            Act_Flag=False
            # print(len(InterFace))
            InterFaceIroning = []
            InterFaceGlueing = []
            InterFacePreGlueing = []#预涂胶部分
            last_xy_command_in_other_features_old=last_xy_command_in_other_features
            if Inconsistent_Count>5 and para.Interface_ironing_Flag==True:
                if Inconsistent_Count>30:
                    This_Layer_is_First_Layer_Revitalization=True
                Inconsistent_Count=0#复位
                InterFace=InterFace_Moisture[:]
                InterFace_Moisture.clear()
                last_xy_command_in_other_features=XY_Moisture_Command
                
                
            
            elif This_Layer_Have_Too_Low_Extrusion:
                print(";Warning, Too low extrusion for ironing segment.")
                #说明挤出量实在太低，必须强制使用全涂
                InterFace=InterFace_Moisture[:]
                last_xy_command_in_other_features=XY_Moisture_Command
                InterFace_Moisture.clear()
            else:
                InterFace_Moisture.clear()
            This_Layer_Have_Too_Low_Extrusion=False
            InterFacePreGlueing.extend(InterFace)
            InterFaceIroning.extend(InterFace)
            InterFaceGlueing.extend(InterFace)
            print(";Pre-glue preparation", file=TempExporter)
            #FAN SECTION
            if para.Filament_Type!="ABS":
                if MachineType_Main == "X1" or MachineType_Main == "P1lite":
                    print("M106 P1 S255", file=TempExporter) 
                elif MachineType_Main == "A1" or MachineType_Main == "A1mini":
                    print("M106 S255", file=TempExporter)
            #RETRACT SECTION
            if MachineType_Main == "P1Lite":
                print("G1 X20 Z"+str(round(Current_Layer_Height+1, 3))+ " E"+ str( para.MKPRetract )+" F" + str(para.Travel_Speed*60), file=TempExporter) #Move to Waiting Point
            elif MachineType_Main == "P1Lite":
                print("G1 X20 Z"+str(round(Current_Layer_Height+1, 3))+ " E"+ str( para.MKPRetract )+" F" + str(para.Travel_Speed*60), file=TempExporter) #Move to Waiting Point
            elif MachineType_Main == "A1":
                print("G1 X252 Z"+str(round(Current_Layer_Height+1, 3))+ " E"+ str( para.MKPRetract ) +" F" + str(para.Travel_Speed*60), file=TempExporter)#Move to Waiting Point
            elif MachineType_Main == "A1mini":
                print("G1 X160 Z"+str(round(Current_Layer_Height+1, 3))+ " E"+ str( para.MKPRetract )+" F" + str(para.Travel_Speed*60), file=TempExporter)#Move to Waiting Point
            #DE-LEAK SECTION
            if para.Nozzle_Cooling_Flag.get()==True:
                print(";Pervent Leakage", file=TempExporter)
                print("M104 S"+str( para.Nozzle_Switch_Tempature - 30), file=TempExporter)

            print(";Rising Nozzle a little", file=TempExporter)
            if Current_Layer_Height<3:
                print("G1 Z" + str(round(Current_Layer_Height+para.Z_Offset+6, 3)), file=TempExporter) #Avoid collision
            else:
                print("G1 Z" + str(round(Current_Layer_Height+para.Z_Offset+3, 3)), file=TempExporter)
            print(";Mounting Toolhead", file=TempExporter)
            #把para.Custom_Mount_Gcode.strip("\n")按行写入
            for line in para.Custom_Mount_Gcode.strip("\n").split("\n"):
                if line.strip().find("G1 E") != -1:
                    pass
                elif line.strip().find("L801")==-1:
                    print(line.strip(), file=TempExporter)
                else:
                    if Current_Layer_Height<3:
                        print("G1 Z"+str(round(Current_Layer_Height+para.Z_Offset+4, 3))+";L801", file=TempExporter)#Avoid collision
                    else:
                        print("G1 Z"+str(round(Current_Layer_Height+para.Z_Offset+3, 3))+";L801", file=TempExporter)
            print(";Toolhead Mounted", file=TempExporter)
            print("G1 Z" + str(round(Last_Layer_Height+para.Z_Offset+3, 3)), file=TempExporter) #Avoid collision
            print(";Glueing Started", file=TempExporter)
            print(";Inposition", file=TempExporter)
            print("G1 F" + str(para.Travel_Speed*60), file=TempExporter) 

            print(Process_GCode_Offset(last_xy_command_in_other_features, para.X_Offset, para.Y_Offset, para.Z_Offset+3,'normal').strip("\n"), file=TempExporter)#Inposition
            # print(Process_GCode_Offset(last_xy_command_in_other_features_old, para.X_Offset, para.Y_Offset, para.Z_Offset+3,'normal').strip("\n"), file=TempExporter)#Inposition
            First_XY_Command_IN_Flag=True
            if para.Minor_Nozzle_Diameter_Flag==True:
                #隔一个删除一个以G1 X或者G1 Y开头的行
                for i in range(len(InterFaceGlueing)-1, -1, -1):
                    if InterFaceGlueing[i].find("G1 X") != -1 or InterFaceIroning[i].find("G1 Y") != -1:
                        if i%2==0:
                            InterFaceGlueing.pop(i)
                            
            #尝试恢复胶水压力,对于10层以上的差异才会执行
            CD_Flag=False
            Have_Rev=False
            if This_Layer_is_First_Layer_Revitalization:
                This_Layer_is_First_Layer_Revitalization = False
                print(";Gluepen Revitalization Start", file=TempExporter)
                print("G1 F" + str(round(max(30*60,para.Max_Speed/2))), file=TempExporter)
                # 润笔目标总长度
                TARGET_LENGTH = 100.0  # 目标累计位移100mm
                
                # 提取所有符合条件的G1命令并计算累计长度
                selected_commands = []
                total_length = 0.0
                last_x = None
                last_y = None
                
                for line in InterFaceGlueing:
                    if line.find("G1 ") != -1 and line.find("G1 E") == -1 and line.find("G1 F") == -1:
                        if line.find("G1 X") != -1 or line.find("G1 Y") != -1:
                            # 提取坐标
                            x_match = re.search(r'X([\d\.-]+)', line)
                            y_match = re.search(r'Y([\d\.-]+)', line)
                            
                            if x_match and y_match:
                                x = float(x_match.group(1))
                                y = float(y_match.group(1))
                                
                                # 计算位移长度（如果有上一个点）
                                if last_x is not None and last_y is not None:
                                    length = np.sqrt((x - last_x)**2 + (y - last_y)**2)
                                    total_length += length
                                
                                last_x, last_y = x, y
                                selected_commands.append(line)
                
                # 根据目标长度确定要输出的命令数量
                if total_length > 0:
                    Have_Rev=True
                    # 计算比例：我们需要输出的长度占比
                    output_ratio = min(1.0, TARGET_LENGTH / total_length)
                    output_count = max(1, int(len(selected_commands) * output_ratio))
                    InterFaceGlueingRev = InterFaceGlueing.copy()  # 或者 list(InterFaceGlueing)
                    # 输出润笔命令
                    for i in range(output_count):
                        if InterFaceGlueingRev[i].find("G1 ") != -1 and InterFaceGlueingRev[i].find("G1 E") == -1 and InterFaceGlueingRev[i].find("G1 F") == -1:
                            if InterFaceGlueingRev[i].find("G1 X") != -1 or InterFaceGlueingRev[i].find("G1 Y") != -1:
                                Physical_Glueing_Point = Process_GCode_Offset(InterFaceGlueingRev[i], 0, 0, para.Z_Offset+3, 'normal')
                                if First_XY_Command_IN_Flag == True:
                                    first_xy_command_in_interface = Physical_Glueing_Point
                                    First_XY_Command_IN_Flag = False
                            
                            InterFaceGlueingRev[i] = Process_GCode_Offset(InterFaceGlueingRev[i], para.X_Offset, para.Y_Offset, para.Z_Offset, 'normal')
                            if CD_Flag == False:
                                print("G1 Z" + str(round(Last_Layer_Height + para.Z_Offset, 3)), file=TempExporter)
                                print("G1 F"+str(para.Max_Speed),file=TempExporter)
                                CD_Flag = True
                            print(InterFaceGlueingRev[i].strip("\n"), file=TempExporter)
                            
                            
                                
                        elif InterFaceGlueingRev[i].find(";ZJUMP_START") != -1:
                            NextStartIndex = i + 1
                            if i + 1 < len(InterFaceGlueingRev):
                                for j in range(i + 1, len(InterFaceGlueingRev)):
                                    if InterFaceGlueingRev[j].find("G1 X") != -1 or InterFaceGlueingRev[j].find("G1 Y") != -1:
                                        NextStartIndex = j
                                        break
                                print("G1 F" + str(para.Travel_Speed * 60), file=TempExporter)
                                print("G1 Z" + str(round(Current_Layer_Height + para.Z_Offset + 3, 3)), file=TempExporter)
                                TempJumpZ = Process_GCode_Offset(InterFaceGlueingRev[NextStartIndex], para.X_Offset, para.Y_Offset, para.Z_Offset + 3, 'normal')
                                print(TempJumpZ.strip("\n"), file=TempExporter)
                                print("G1 Z" + str(round(Last_Layer_Height + para.Z_Offset, 3)), file=TempExporter)
                                print("G1 F" + str(para.Max_Speed * para.Small_Feature_Factor), file=TempExporter)

                
                print(";Gluepen Revitalization End", file=TempExporter)
                print("G1 Z" + str(round(Current_Layer_Height+para.Z_Offset+1, 3)), file=TempExporter)#Jump_Z
                print("G1 F" + str(para.Travel_Speed*60), file=TempExporter)
                # print(last_xy_command_in_other_features,file=TempExporter)
                # print("G1 Z" + str(round(Last_Layer_Height+para.Z_Offset, 3)), file=TempExporter)#Adjust
                print("G1 F"+str(para.Max_Speed),file=TempExporter)
                CD_Flag=False
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
                    if Have_Rev==False:
                        print("G1 Z" + str(round(Last_Layer_Height+para.Z_Offset, 3)), file=TempExporter)#Adjust
                        print("G1 F"+str(para.Max_Speed),file=TempExporter)
                    else:
                        print(InterFaceGlueing[i].strip("\n"),file=TempExporter)
                        print("G1 Z" + str(round(Last_Layer_Height+para.Z_Offset, 3)), file=TempExporter)#Adjust
                        print("G1 F"+str(para.Max_Speed),file=TempExporter)
                    print(InterFaceGlueing[i].strip("\n"),file=TempExporter)
                    
                elif InterFaceGlueing[i].find(";ZJUMP_START") != -1:
                    #从i开始，检查往后的i+1，i+2，i+3行等等谁含有G1 X 或者G1 Y,记录这一个数值
                    NextStartIndex=i+1
                    if i+1<len(InterFaceGlueing):
                        for j in range(i+1, len(InterFaceGlueing)):
                            if InterFaceGlueing[j].find("G1 X") != -1 or InterFaceGlueing[j].find("G1 Y") != -1:
                                NextStartIndex=j
                                break
                        print("G1 F" + str(para.Travel_Speed*60), file=TempExporter) #Move to Wiping Point
                        print("G1 Z" + str(round(Current_Layer_Height+para.Z_Offset+3, 3)), file=TempExporter)#Avoid spoiling
                        TempJumpZ=Process_GCode_Offset(InterFaceGlueing[NextStartIndex], para.X_Offset, para.Y_Offset , para.Z_Offset+3,'normal')
                        print(TempJumpZ.strip("\n"),file=TempExporter)
                        print("G1 Z"+ str(round(Last_Layer_Height+para.Z_Offset, 3)), file=TempExporter)#Adjust
                        print("G1 F"+str(para.Max_Speed*para.Small_Feature_Factor),file=TempExporter)
            print(";Glueing Finished", file=TempExporter)
            print("G1 F" + str(para.Travel_Speed*60), file=TempExporter)
            print("G1 Z" + str(round(Current_Layer_Height+para.Z_Offset+3, 3)), file=TempExporter)#Avoid collision
            print(";Lift-z:"+str(round(Current_Layer_Height+para.Z_Offset+3, 3)), file=TempExporter)
            if para.First_Pen_Revitalization_Flag==True:
                para.First_Pen_Revitalization_Flag=False
                print(";Waiting for Glue Settling", file=TempExporter)
                print("G4 P6000", file=TempExporter)
            print(";Unmounting Toolhead", file=TempExporter)
            #同上处理，strip\n后按行写入，检l801
            for line in para.Custom_Unmount_Gcode.strip("\n").split("\n"):
                # if line.strip().find("G1 E") != -1:
                #     if para.Have_Wiping_Components.get()==True:
                #         print(line.strip(), file=TempExporter)
                #     else:
                #         print("G1 E"+str(para.MKPRetract), file=TempExporter)
                if line.strip().find(";Wipe") != -1:
                    pass
                    # if para.Use_Wiping_Towers.get()!=True and para.Silicone_Wipe_Flag!=True:
                    #     print(line.strip(), file=TempExporter)
                    # else:
                    #     pass
                elif line.strip().find(";Brush") != -1:
                    # if para.Silicone_Wipe_Flag==True:
                    #     if line.strip().find("L801")!=-1:
                    #         print("G1 Z"+str(round(Current_Layer_Height+para.Z_Offset+3, 3))+";L801", file=TempExporter)
                    #     else:
                    #         print(line.strip(), file=TempExporter)
                    # else:
                    #     pass
                    pass
                elif line.strip().find("M106 S[AUTO]") != -1:
                    print("M106 S" + str(para.Fan_Speed), file=TempExporter)
                elif line.strip().find("M106 P1 S[AUTO]") != -1:
                    print("M106 P1 S" + str(para.Fan_Speed), file=TempExporter)
                elif line.strip().find("G1 E") != -1:
                    if para.Use_Disk_Wipe_Flag==True:
                        pass
                    else:
                        print(line.strip(), file=TempExporter)
                else:
                    print(line.strip(), file=TempExporter)
            print(";Toolhead Unmounted", file=TempExporter)
            # print(";Move to the next print start position", file=TempExporter)
            
            # #如果使用擦嘴组件，在填充上回复温度
            # if para.Use_Wiping_Towers.get()!=True:
            #     print("; FEATURE: Outer wall", file=TempExporter)
            #     if para.Nozzle_Cooling_Flag.get()==True:
            #         print("M104 S"+str( para.Nozzle_Switch_Tempature ), file=TempExporter)
            #     if para.User_Dry_Time!=0:
            #         print(";User Dry Time Activated", file=TempExporter)
            #         print("G4 P"+str(para.User_Dry_Time*1000), file=TempExporter)

            #     print(";Print sparse/solid infill first",file=TempExporter)
            #     print("G1 F" + str(para.Travel_Speed*60), file=TempExporter)
            #     try:
            #         #Temp_Rebuild_Pressure的第一行去除E部分之后输出，第一行一定存在且一定有E
            #         print(Temp_Rebuild_Pressure[0][:Temp_Rebuild_Pressure[0].find("E")].strip("\n"), file=TempExporter)
            #         print("G1 Z"+ str(round(Last_Layer_Height+0.1, 3)), file=TempExporter)#Adjust
            #         #调速
            #         print("G1 F600", file=TempExporter)
            #         #其余行完整输出
            #         for j in range(1,len(Temp_Rebuild_Pressure)):
            #             print(Temp_Rebuild_Pressure[j].strip("\n"), file=TempExporter)
            #     except:
            #         pass
                
            
            #如果不使用擦嘴组件，在擦料塔上回复温度
            if para.Use_Wiping_Towers.get()==True:
                
                print(Process_GCode_Offset("G1 X20 Y10.19", para.Wiper_x-5, para.Wiper_y-5, Current_Layer_Height+3,'normal').strip("\n"), file=TempExporter)
                print(";Prepare for next tower", file=TempExporter)
                if para.Nozzle_Cooling_Flag.get()==True:
                    if para.User_Dry_Time!=0:
                        print("M104 S"+str( para.Nozzle_Switch_Tempature ), file=TempExporter)
                    else :
                        print("M109 S"+str( para.Nozzle_Switch_Tempature ), file=TempExporter)
                print(para.Refill_Extrude_Command,file=TempExporter)
                if para.User_Dry_Time!=0:
                    print(";User Dry Time Activated", file=TempExporter)
                    print("G4 P"+str(para.User_Dry_Time*1000), file=TempExporter)
            else:
                print(";Prepare for next tower",file=TempExporter)
            Layer_Height_Index[Current_Layer_Height] = ['','','','','']
            # Layer_Height_Index[Current_Layer_Height][0]= InterFacePreGlueing.copy()
            Layer_Height_Index[Current_Layer_Height][1]= Last_Layer_Height
            Layer_Height_Index[Current_Layer_Height][2]= Process_GCode_Offset(last_xy_command_in_other_features, para.X_Offset, para.Y_Offset, para.Z_Offset+3,'normal').strip("\n")
            Layer_Height_Index[Current_Layer_Height][3]=Process_GCode_Offset(last_xy_command_in_other_features,0, 0, para.Z_Offset+3,'normal').strip("\n")
            Layer_Height_Index[Current_Layer_Height][4]=Layer_Thickness
            InterFaceGlueing.clear()
            InterFaceIroning.clear()
            InterFacePreGlueing.clear()
            InterFace.clear()

        if CurrGCommand.find("; layer num/total_layer_count")!=-1:
            if InterFace_Moisture!=[]:
                InterFace_Moisture.clear()
        para.Allow_Temp_Export_Flag=True
        if para.Ironing_Removal_Flag==True:
            para.Allow_Temp_Export_Flag=False
        if para.Avoid_Wall_Export_Flag==True:
            para.Allow_Temp_Export_Flag=False

        if para.Wipe_remove_flag==2:
            # print(";Wipe Removal", file=TempExporter)
            para.Allow_Temp_Export_Flag=False

        #Allow_Temp_Export_Flag
        # if para.Ironing_Removal_Flag!=True:
        if para.Allow_Temp_Export_Flag==True:
            print(CurrGCommand, file=TempExporter)

    TempExporter.close()

    #输出的预涂胶代码
    Trigger_Flag=False
    Tower_Flag=False
    FirstLayer_Tower_Height=0
    First_layer_Tower_Flag=True
    First_layer_Flag=True
    Last_Layer_Height=0
    CurrMax_Tower_Height=para.First_Layer_Height
    try:
        Last_Key=max(Layer_Height_Index.keys())
    except:
        Last_Key=0
    # print("Last Key:",Last_Key)
    Output_Filename = GSourceFile + "_Output.gcode"
    with open(Output_Filename+'.te', 'r', encoding='utf-8') as file:
        content = file.readlines()
    try:
        GcodeExporter = open(Output_Filename, "w", encoding="utf-8")
    except:
        # tk.messagebox.showinfo(title='提示', message="Standby")
        GcodeExporter = open(Output_Filename, "w", encoding="utf-8")
    CutNozzle_Wrap_Detect=False
    Next_TJ=False
    Pen_Wipe_Flag=False
    Thick_bridge_action_flag=False
    CurrThickness=0
    Suggested_Ratio=1.0
    Adjust_support_action_flag=False
    last_selected_disk=None
    Disk_history=[]
    print(para.Support_Extrusion_Multiplier)
    for i in range(len(content)):
        LastGCommand = CurrGCommand
        CurrGCommand = content[i].strip("\n")
        
        if CurrGCommand.find("; LAYER_HEIGHT: ") != -1:
            CurrThickness=Num_Strip(CurrGCommand)[0]
            #以下是挤出的进给率的逻辑：如果>=50%的喷嘴直径，则此层高与实际需要层高一致，Suggested_Ratio=1.0；如果在喷嘴直径的20%则此层高远小于要求，需要增加挤出量，Suggested_Ratio=（实际需要层高/当前层高），而实际需要层高是基于喷嘴直径的0.65倍计算的，即实际需要层高=0.6*Nozzle_Diameter；如果在20%-50%之间，则线性插值计算
            if CurrThickness>=(0.5*para.Nozzle_Diameter):
                Suggested_Ratio=1.0
            elif CurrThickness<=(0.2*para.Nozzle_Diameter):
                Suggested_Ratio=(0.6*para.Nozzle_Diameter)/CurrThickness
            else:
                Suggested_Ratio=1.0+((0.6*para.Nozzle_Diameter)/CurrThickness-1.0)*((0.5*para.Nozzle_Diameter)-CurrThickness)/((0.5*para.Nozzle_Diameter)-(0.2*para.Nozzle_Diameter))
            # print(";Suggested Ratio:"+str(Suggested_Ratio))

        # if para.Force_Thick_Bridge_Flag.get()==True:
        if Current_Layer_Height>0.3:
            if CurrGCommand.find("; FEATURE: Support") != -1 and CurrGCommand.find("; FEATURE: Support transition") == -1 and CurrGCommand.find("; FEATURE: Support interface") == -1 and CurrGCommand.find("; FEATURE: Support ironing") == -1:
                Adjust_support_action_flag=True
                # print("; LAYER_HEIGHT: "+str(round(CurrThickness*Suggested_Ratio,3)), file=GcodeExporter)
            if CurrGCommand.find("; FEATURE: ") != -1 and (CurrGCommand.find("; FEATURE: Support") == -1 or CurrGCommand.find("; FEATURE: Support transition") != -1 or CurrGCommand.find("; FEATURE: Support interface") != -1 or CurrGCommand.find("; FEATURE: Support ironing") != -1):
                Adjust_support_action_flag=False 
                # print("; LAYER_HEIGHT: "+str(CurrThickness), file=GcodeExporter)
            
        if Adjust_support_action_flag==True and CurrGCommand.find("G1 X") != -1 and CurrGCommand.find("E") != -1:#开始调整挤出
            
            #找到E后面的数值
            E_Index=CurrGCommand.find("E")
            E_Value_Str=CurrGCommand[E_Index+1:]
            #需要区分是数字还是“.”开头
            E_Value=0
            if E_Value_Str[0].isdigit():
                #五位小数
                E_Value=round(Num_Strip(E_Value_Str)[0],5)
                # E_Value=Num_Strip(E_Value_Str)[0]
            elif E_Value_Str[0]==".":
                E_Value=round(Num_Strip("0"+E_Value_Str)[0],5)
                # E_Value=Num_Strip("0"+E_Value_Str)[0]
            #还需要区分是正数还是负数，如果是负数，不调整，直接跳过
            if CurrGCommand[E_Index+1]=="-":
                Gcode_Storage.append(CurrGCommand)
                # print("OriginalCommand:"+CurrGCommand+" Adjusted Command:"+CurrGCommand)
                continue
            New_E_Value=round(E_Value*para.Support_Extrusion_Multiplier,5)
            #对于0.x的情况，和原指令一样的省略0
            if New_E_Value<1.0 and New_E_Value>0.0:
                str_New_E_Value=str(New_E_Value)[1:]
            else:
                str_New_E_Value=str(New_E_Value)
            New_GCommand=CurrGCommand[:E_Index+1]+str_New_E_Value
            # print("OriginalCommand:"+CurrGCommand+" Adjusted Command:"+New_GCommand)
            CurrGCommand=New_GCommand+";Adjust as support"

        
        if CurrGCommand.startswith("; FEATURE: Support") or CurrGCommand.startswith("; FEATURE: Support transition") or CurrGCommand.startswith("; FEATURE: Support interface"):
            para.Append_Support_Flag=True

        if ( CurrGCommand.startswith("; FEATURE: ") and ( not CurrGCommand.startswith("; FEATURE: Support") ) ) or CurrGCommand.startswith("; FEATURE: Support ironing"):
            para.Append_Support_Flag=False
        if para.Append_Support_Flag==True and CurrGCommand.startswith("G1 X"):
            Supports.append(CurrGCommand)
            # Supports.append(";"+str(Current_Layer_Height))

        if CurrGCommand.find("; Z_HEIGHT: ") != -1:
            # print("Current Layer Height:"+str(Current_Layer_Height)+" Last Layer Height:"+str(Last_Layer_Height))
            # print("Current - Last :"+str(Current_Layer_Height-Last_Layer_Height))
            Last_Layer_Height = Current_Layer_Height
            Current_Layer_Height = Num_Strip(CurrGCommand)[0]
            if Current_Layer_Height in Layer_Height_Index and Current_Layer_Height>0.4:
                Trigger_Flag=True

            if para.Use_Wiping_Towers.get()==True and First_layer_Flag==True and Current_Layer_Height>0.01:
                First_layer_Flag=False
                FirstLayer_Tower_Height=Current_Layer_Height

            for j in range(i+1, len(content)):
                if content[j].find("; Z_HEIGHT: ") != -1:
                    break
                if content[j].find(";Rising Nozzle a little") != -1:
                    Next_TJ=True
                    # print(";Triggering LH:"+ str(Current_Layer_Height))
                    # para.Switch_Tower_Type=1
                    break
            if Next_TJ==False:
                Suggested_LH=(0.65*para.Nozzle_Diameter)
            else:
                Suggested_LH=round(Current_Layer_Height-Last_Layer_Height,3)
                if Suggested_LH<(0.2*para.Nozzle_Diameter):
                    Suggested_LH=(0.2*para.Nozzle_Diameter)
                # if round(Current_Layer_Height-Last_Layer_Height,3)<para.Typical_Layer_Height:
                #     Suggested_LH=para.Typical_Layer_Height
            LastMax_Tower_Height=CurrMax_Tower_Height
            if Current_Layer_Height<Last_Key+0.4:
                if CurrMax_Tower_Height+Suggested_LH< Current_Layer_Height or Next_TJ==True:
                    Next_TJ=False
                    CurrMax_Tower_Height=round(CurrMax_Tower_Height+Suggested_LH,3)
                    # print(";Current Max Tower Height:"+str(CurrMax_Tower_Height))
                    # print("Suggested Layer Height:"+str(Suggested_LH))
                else:
                    pass
                if LastMax_Tower_Height< CurrMax_Tower_Height:
                    # print(";Current Max Tower Height:"+str(CurrMax_Tower_Height))
                    Tower_Flag=True
                else:
                    pass
                    # print(";Current Max Tower Height:"+str(CurrMax_Tower_Height)+" vs ;Last Max Tower Height:"+str(LastMax_Tower_Height))

            #检索该层层内是否有内墙或者外墙，如果没有则该层的Tower_Flag=False
        
        #输出首层塔代码
        if CurrGCommand.find("; CHANGE_LAYER") != -1 and First_layer_Tower_Flag==True and para.Use_Wiping_Towers.get()==True:
            First_layer_Tower_Flag=False
            # print("G1 Z" + str(round(para.First_Layer_Height, 3) )+ ";TowerBase Z", file=GcodeExporter)#Adjust z height
            para.Tower_Extrude_Ratio = round((para.First_Layer_Height/ 0.2)*0.8, 3)
            Gcode_Storage.append("G1 F" + str(para.Travel_Speed*60))
            for j in range(len(para.Tower_Base_Layer_Gcode)):
                if para.Tower_Base_Layer_Gcode[j].find("EXTRUDER_REFILL")!=-1:
                    Gcode_Storage.append("G92 E0")
                    Gcode_Storage.append("G1 E"+str(para.Retract_Length))
                    Gcode_Storage.append("G92 E0")
                elif para.Tower_Base_Layer_Gcode[j].find("NOZZLE_HEIGHT_ADJUST") != -1:
                    Gcode_Storage.append("G1 Z" + str(round(para.First_Layer_Height, 3) )+ ";Tower Z")
                elif para.Tower_Base_Layer_Gcode[j].find("EXTRUDER_RETRACT")!=-1:
                    # Gcode_Storage.append("G92 E0")
                    # Gcode_Storage.append("G1 E-"+str(para.Retract_Length))
                    Gcode_Storage.append("G92 E0")
                elif para.Tower_Base_Layer_Gcode[j].find("G92 E0") != -1:
                    Gcode_Storage.append("G92 E0")
                elif para.Tower_Base_Layer_Gcode[j].find("G1 ") != -1 and para.Tower_Base_Layer_Gcode[j].find("G1 E") == -1 and para.Tower_Base_Layer_Gcode[j].find("G1 F") == -1:
                    # print(para.Tower_Base_Layer_Gcode[1])
                    TowerGCTemp=Process_GCode_Offset(para.Tower_Base_Layer_Gcode[j],para.Wiper_x-5, para.Wiper_y-5, 0,'tower')
                    # para.Tower_Base_Layer_Gcode[j] = Process_GCode_Offset(para.Tower_Base_Layer_Gcode[j],0, 0, 0,'tower')
                    
                    Gcode_Storage.append(TowerGCTemp.strip("\n"))
                
                elif para.Tower_Base_Layer_Gcode[j].find("G1 F9600") != -1:
                    Gcode_Storage.append("G1 F" + str(para.First_Layer_Speed*60))
            Gcode_Storage.append("G1 F" + str(para.Travel_Speed*60)) 

        if CurrGCommand.find(";Print a plane for wiping") != -1:
            # para.Switch_Tower_Type=1
            pass
        # print ("G1 Z" + str(round(CurrMax_Tower_Height+para.Z_Offset+3, 3)), file=GcodeExporter) #Avoid collision   

        if CurrGCommand.find("; LAYER_HEIGHT:") != -1:
            #记录当前层厚度
            Local_Thickness=Num_Strip(CurrGCommand)[0]
            Gcode_Storage.append("; Current Layer Thickness:"+ str(Local_Thickness))

        #输出后续塔代码
        if CurrGCommand.find("; update layer progress") != -1 and para.Use_Wiping_Towers.get()==True and Tower_Flag==True and First_layer_Tower_Flag==False and Current_Layer_Height!=para.First_Layer_Height:
            Tower_Flag=False
            Gcode_Storage.append("G1 F" + str(para.Travel_Speed*60))
            # print("G1 Z"+ str(round(Current_Layer_Height, 3))+";Tower Z", file=GcodeExporter)
            para.Tower_Extrude_Ratio=round(Suggested_LH / 0.2,3)
            #send a jump z command
            if Suggested_LH == (0.65*para.Nozzle_Diameter):
                Gcode_Storage.append(Process_GCode_Offset("G1 X20 Y20", para.Wiper_x-5, para.Wiper_y-5, CurrMax_Tower_Height+3,'tower').strip("\n")+" Z"+ str(round(Current_Layer_Height+0.6, 3))) #Move to Wiping Tower
            Gcode_Storage.append("; FEATURE: Inner wall")
            Gcode_Storage.append("; LINE_WIDTH: 0.42")
            Gcode_Storage.append(";Extruding Ratio: " + str(para.Tower_Extrude_Ratio))
            Gcode_Storage.append("; LAYER_HEIGHT: " + str(Suggested_LH))
            for j in range(len(para.Wiping_Gcode)):
                # if para.Wiping_Gcode[j].find("G1 ") != -1 and para.Wiping_Gcode[j].find("G1 E") == -1 and para.Wiping_Gcode[j].find("G1 F") == -1:
                if para.Wiping_Gcode[j].find("G1 F9600") != -1:#替换为用户自己的外墙速度
                    if para.Switch_Tower_Type<=3:
                        Gcode_Storage.append("G1 F" + str(min(para.WipeTower_Print_Speed,35)*60))
                    else:
                        Gcode_Storage.append("G1 F" + str(para.WipeTower_Print_Speed*60))
                        
                elif para.Wiping_Gcode[j].find("TOWER_ZP_ST") != -1:
                    pass
                elif para.Wiping_Gcode[j].find("NOZZLE_HEIGHT_ADJUST") != -1:
                    Gcode_Storage.append("G1 Z"+ str(CurrMax_Tower_Height)+";Tower Z")
                elif para.Wiping_Gcode[j].find("EXTRUDER_REFILL")!=-1:#补偿挤出
                    Gcode_Storage.append("G92 E0")
                    Gcode_Storage.append("G1 E"+str(para.Retract_Length))
                    Gcode_Storage.append("G92 E0")
                elif para.Wiping_Gcode[j].find("EXTRUDER_RETRACT")!=-1:#预防性回抽
                    Gcode_Storage.append("G92 E0")
                    Gcode_Storage.append("G1 E-"+str(round(abs(para.Retract_Length - 0.31), 3)))
                    Gcode_Storage.append("G92 E0")
                elif para.Wiping_Gcode[j].find("G1 E-.21 F5400") != -1:
                    Gcode_Storage.append("G1 E-.21 F5400")
                elif para.Wiping_Gcode[j].find("G1 E.3 F5400") != -1:
                    Gcode_Storage.append("G1 E.3 F5400")
                elif para.Wiping_Gcode[j].find("G92 E0") != -1:
                    Gcode_Storage.append("G92 E0")
                else:
                    if para.More_Extrude_Flag==True and Current_Layer_Height>=0.4:
                        if para.Wiping_Gcode[j].startswith("G1 X20 Y20 E"):
                            TowerGCTemp=Process_GCode_Offset("G1 X20 Y20 E.34 ;MoreExtrusion", para.Wiper_x-5, para.Wiper_y-5, 0,'tower')
                        elif para.Wiping_Gcode[j].startswith("G1 X29.81 Y20 E"):
                            TowerGCTemp=Process_GCode_Offset("G1 X29.81 Y20 E.34 ;MoreExtrusion", para.Wiper_x-5, para.Wiper_y-5, 0,'tower')
                        elif para.Wiping_Gcode[j].startswith("G1 X10.19 Y20 E"):
                            TowerGCTemp=Process_GCode_Offset("G1 X10.19 Y20 E.34 ;MoreExtrusion", para.Wiper_x-5, para.Wiper_y-5, 0,'tower')
                        else:
                            TowerGCTemp = Process_GCode_Offset(para.Wiping_Gcode[j], para.Wiper_x-5, para.Wiper_y-5, 0,'tower')
                    else:
                        TowerGCTemp = Process_GCode_Offset(para.Wiping_Gcode[j], para.Wiper_x-5, para.Wiper_y-5, 0,'tower')
                    Gcode_Storage.append(TowerGCTemp.strip("\n"))
            if para.Switch_Tower_Type<=3:
                para.Switch_Tower_Type+=1   
            if para.More_Extrude_Flag==True:
                para.More_Extrude_Flag=False
            Gcode_Storage.append("G1 F" + str(para.Travel_Speed*60))
            Gcode_Storage.append(Process_GCode_Offset("G1 X33 Y33", para.Wiper_x-5, para.Wiper_y-5, CurrMax_Tower_Height+0.7,'tower').strip("\n")+" Z"+ str(round(CurrMax_Tower_Height+0.7, 3))+" ;Leaving Wiping Tower") #Leaving Wiping Tower
            try:
                Gcode_Storage.append("; LAYER_HEIGHT: "+ str(Local_Thickness))
            except:
                pass
            para.Remove_G3_Flag = True
        if para.Remove_wrap_detect_flag!=True:
            Allow_Print_Flag=True
        # Allow_Print_Flag=True

        if CurrGCommand.startswith("; layer num/total_layer_count:"):
            if Collision_Walls!=[]:
                Collision_Check.append([Collision_Walls[:], None])
                Collision_Walls.clear()#清空上一层的墙数据
            if len(Collision_Check)>5:
                # print(Collision_Check[0])
                Collision_Check.pop(0)#删除最老的Wall数据
            # print(";Hello, this is the insert point",file=GcodeExporter)
            if Supports!=[]:
                Supports.clear()
        if CurrGCommand.startswith("; FEATURE: Outer wall"):
            para.Add_Wall_Collision_Line_Flag=True
        if para.Add_Wall_Collision_Line_Flag and CurrGCommand.startswith("G1 X") and "E" in CurrGCommand:
            Collision_Walls.append(CurrGCommand)

        if CurrGCommand.startswith("; FEATURE:") and (not CurrGCommand.startswith("; FEATURE: Outer wall")):
            para.Add_Wall_Collision_Line_Flag=False

        if CurrGCommand.startswith(";Prepare for next tower"):
            
            para.Remove_G3_Flag = True
            para.More_Extrude_Flag = True
            para.Switch_Tower_Type=1

            #紧急填充
            if Collision_Walls!=[]:
                Collision_Check.append([Collision_Walls[:], None])#把刚刚存储的墙数据加入Collision_Check
                Collision_Walls.clear()#清空上一层的墙数据
            if len(Collision_Check)>5:
                Collision_Check.pop(0)#删除最老的Wall数据

            #处理圆盘的生成
            if Supports!=[] and para.Use_Wiping_Towers.get()!=True:
                
                Gcode_Storage.append(";Find collision-disk")
                # ===== 使用已有参数 =====
                LAYER_HEIGHT = para.Typical_Layer_Height
                NOZZLE_DIAMETER = para.Nozzle_Diameter
                LINE_WIDTH = NOZZLE_DIAMETER * 1.1  # 通常线宽略大于喷嘴直径
                
                # 圆盘参数
                DISK_DIAMETER = 4.5
                DISK_RADIUS = DISK_DIAMETER / 2
                CHECK_RADIUS = DISK_RADIUS + 1.0  # 扩大1mm的安全检查半径
                EXTENSION_LENGTH = 4.0
                # MAX_DISKS = 1
                # CONNECTION_SPACING = 2.0  # 连接线间距 2mm
                
                # 十边形的10个顶点（用于碰撞检测）
                N_GON = 10  # 十边形
                polygon_angles = np.linspace(0, 2*np.pi, N_GON, endpoint=False)
                
                # 角度偏移列表：0度（法线方向），+30度，-30度
                ANGLE_OFFSETS = [0, 30, -30]  # 单位：度
                ANGLE_OFFSETS_RAD = [np.deg2rad(a) for a in ANGLE_OFFSETS]  # 转换为弧度
                
                # 计算需要打印的圈数（从内向外）
                circles = int(DISK_RADIUS / LINE_WIDTH)
                if circles < 2:
                    circles = 2
                
                # 喷嘴截面积（用于挤出量计算）
                NOZZLE_AREA = np.pi * (NOZZLE_DIAMETER/2)**2
                
                # 获取当前层的Z高度
                current_z = Current_Layer_Height
                
                # ===== 从Supports中解析所有支撑点 =====
                all_support_points = []
                for gcode_line in Supports:
                    if not gcode_line.startswith('G1 X') or 'E' not in gcode_line:
                        continue
                    x_match = re.search(r'X([\d\.-]+)', gcode_line)
                    y_match = re.search(r'Y([\d\.-]+)', gcode_line)
                    if x_match and y_match:
                        try:
                            x = float(x_match.group(1))
                            y = float(y_match.group(1))
                            all_support_points.append((x, y))
                        except:
                            continue
                   
                Supports.clear()#清空上一层的支撑点数据
                
                if len(all_support_points) >= 3:
                    # ===== 计算支撑多边形的凸包 =====
                    points_array = np.array(all_support_points)
                    hull = ConvexHull(points_array)
                    hull_points = points_array[hull.vertices]
                    center = np.mean(points_array, axis=0)
                    
                    # ===== 计算每个顶点的精确法线（基于相邻边夹角） =====
                    disk_positions = []  # 现在每个顶点对应多个备选位置
                    
                    for i, vertex in enumerate(hull_points):
                        # 获取当前顶点的前后顶点
                        prev_vertex = hull_points[i-1]
                        next_vertex = hull_points[(i+1) % len(hull_points)]
                        
                        # 计算两条边的向量
                        edge1 = vertex - prev_vertex
                        edge2 = next_vertex - vertex
                        
                        # 计算两条边的法线（垂直方向）
                        # 对于边 (dx, dy)，法线是 (-dy, dx) 指向左侧
                        normal1 = np.array([-edge1[1], edge1[0]])
                        normal2 = np.array([-edge2[1], edge2[0]])
                        
                        # 归一化法线
                        norm1 = np.linalg.norm(normal1)
                        norm2 = np.linalg.norm(normal2)
                        
                        if norm1 > 0:
                            normal1 = normal1 / norm1
                        if norm2 > 0:
                            normal2 = normal2 / norm2
                        
                        # 平均法线（两条边的角平分线方向）
                        if norm1 > 0 and norm2 > 0:
                            # 两条法线都有定义，取平均
                            avg_normal = (normal1 + normal2) / 2
                            avg_norm = np.linalg.norm(avg_normal)
                            if avg_norm > 0:
                                avg_normal = avg_normal / avg_norm
                            else:
                                # 如果两条法线相反，取第一条
                                avg_normal = normal1
                        elif norm1 > 0:
                            avg_normal = normal1
                        elif norm2 > 0:
                            avg_normal = normal2
                        else:
                            # 如果都无法计算，用从中心指向顶点的方向
                            avg_normal = vertex - center
                            avg_normal = avg_normal / np.linalg.norm(avg_normal)
                        
                        # 确保法线指向多边形外部
                        to_center = center - vertex
                        if np.dot(avg_normal, to_center) > 0:
                            # 法线指向内部，反转
                            avg_normal = -avg_normal
                        
                        # 计算垂直方向（用于生成左右两侧的连接线）
                        perpendicular = np.array([-avg_normal[1], avg_normal[0]])  # 顺时针垂直
                        
                        # **为每个顶点生成多个备选方向（法线方向 ±30°）**
                        for offset_idx, angle_rad in enumerate(ANGLE_OFFSETS_RAD):
                            # 旋转法线向量
                            cos_a = np.cos(angle_rad)
                            sin_a = np.sin(angle_rad)
                            # 二维旋转矩阵
                            rotated_normal = np.array([
                                avg_normal[0] * cos_a - avg_normal[1] * sin_a,
                                avg_normal[0] * sin_a + avg_normal[1] * cos_a
                            ])
                            
                            # 沿旋转后的方向伸出
                            disk_center = vertex + rotated_normal * EXTENSION_LENGTH
                            
                            # 计算对应这个方向的垂直方向（用于连接线）
                            rotated_perpendicular = np.array([-rotated_normal[1], rotated_normal[0]])
                            
                            disk_positions.append({
                                'vertex': vertex,
                                'center': disk_center,
                                'normal': rotated_normal,
                                'perpendicular': rotated_perpendicular,
                                'vertex_index': i,
                                'offset_angle': ANGLE_OFFSETS[offset_idx],  # 记录偏移角度
                                'offset_idx': offset_idx
                            })
                    
                    Gcode_Storage.append("; FEATURE: Top surface")
                    
                    # ===== 碰撞检测 - 使用扩大的十边形代替圆盘检查 =====
                    selected_disk = None
                    best_score = -1  # 评分标准：碰撞深度越大越好，完全无碰撞给一个大值
                    
                    # 遍历所有候选圆盘位置（现在包括不同角度偏移的）
                    for disk_idx, disk_info in enumerate(disk_positions):
                        center_x, center_y = disk_info['center']
                        vertex_index = disk_info['vertex_index']
                        offset_angle = disk_info['offset_angle']
                        
                        # 创建扩大的十边形（比实际圆盘大1mm）
                        check_polygon_points = []
                        for angle in polygon_angles:
                            x = center_x + CHECK_RADIUS * np.cos(angle)
                            y = center_y + CHECK_RADIUS * np.sin(angle)
                            check_polygon_points.append((x, y))
                        check_polygon_points.append(check_polygon_points[0])
                        check_polygon = Polygon(check_polygon_points)
                        
                        # 记录碰撞信息
                        collision_depths = []
                        
                        # 修改后的碰撞检测代码：
                        for depth, layer_data in enumerate(Collision_Check, 1):  # depth从1开始
                            layer_walls = layer_data[0]  # 原始G-code
                            layer_polygon = layer_data[1]  # 缓存的多边形
                            
                            # 如果还没有缓存多边形，则计算并存储
                            if layer_polygon is None:
                                wall_points = []
                                for wall_line in layer_walls:
                                    if wall_line.startswith('G1 X'):
                                        x_match = re.search(r'X([\d\.-]+)', wall_line)
                                        y_match = re.search(r'Y([\d\.-]+)', wall_line)
                                        if x_match and y_match:
                                            try:
                                                x = float(x_match.group(1))
                                                y = float(y_match.group(1))
                                                wall_points.append((x, y))
                                            except:
                                                continue
                                
                                if len(wall_points) >= 3:
                                    try:
                                        wall_array = np.array(wall_points)
                                        wall_hull = ConvexHull(wall_array)
                                        wall_hull_points = wall_array[wall_hull.vertices]
                                        layer_polygon = Polygon(wall_hull_points)
                                        # 缓存计算结果
                                        layer_data[1] = layer_polygon
                                    except:
                                        continue
                                else:
                                    continue
                            
                            # 直接使用缓存的多边形进行相交检测
                            if check_polygon.intersects(layer_polygon):
                                collision_depths.append(depth)
                        
                        # 计算这个备选位置的得分
                        if not collision_depths:
                            # 完全无碰撞：得分 = 100（高分）
                            score = 100
                            # Gcode_Storage.append(f"; 顶点{vertex_index} 角度{offset_angle}°: 完全无碰撞 ✓")
                        else:
                            min_depth = min(collision_depths)
                            max_depth = max(collision_depths)
                            # 得分 = 最小碰撞深度（越大越好，最大5）
                            score = min_depth
                            # Gcode_Storage.append(f"; 顶点{vertex_index} 角度{offset_angle}°: 第{min_depth}层开始碰撞")
                        
                        # 选择得分最高的
                        if score > best_score:
                            best_score = score
                            selected_disk = disk_info
                            # Gcode_Storage.append(f";  → 当前最佳 (得分{score})")
                    
                    # # 检查选中点是否满足要求（第3层无碰撞要求）
                    # if selected_disk:
                    #     # 重新检查选中点的碰撞情况
                    #     center_x, center_y = selected_disk['center']
                    #     check_polygon_points = []
                    #     for angle in polygon_angles:
                    #         x = center_x + CHECK_RADIUS * np.cos(angle)
                    #         y = center_y + CHECK_RADIUS * np.sin(angle)
                    #         check_polygon_points.append((x, y))
                    #     check_polygon_points.append(check_polygon_points[0])
                    #     check_polygon = Polygon(check_polygon_points)
                        
                    #     collision_in_depth_3 = False
                    #     for depth, layer_walls in enumerate(Collision_Check, 1):
                    #         if depth > 3:  # 只检查前3层
                    #             break
                                
                    #         wall_points = []
                    #         for wall_line in layer_walls:
                    #             if wall_line.startswith('G1'):
                    #                 x_match = re.search(r'X([\d\.-]+)', wall_line)
                    #                 y_match = re.search(r'Y([\d\.-]+)', wall_line)
                    #                 if x_match and y_match:
                    #                     try:
                    #                         x = float(x_match.group(1))
                    #                         y = float(y_match.group(1))
                    #                         wall_points.append((x, y))
                    #                     except:
                    #                         continue
                            
                    #         if len(wall_points) >= 3:
                    #             try:
                    #                 wall_array = np.array(wall_points)
                    #                 wall_hull = ConvexHull(wall_array)
                    #                 wall_hull_points = wall_array[wall_hull.vertices]
                    #                 wall_polygon = Polygon(wall_hull_points)
                                    
                    #                 if check_polygon.intersects(wall_polygon):
                    #                     collision_in_depth_3 = True
                    #                     break
                    #             except:
                    #                 continue
                        
                    #     if collision_in_depth_3:
                    #         Gcode_Storage.append(f"; 警告: 选中点在第3层内有碰撞")
                    #     else:
                    #         Gcode_Storage.append(f"; 选中点在第3层内无碰撞 ✓")
                        
                    #     Gcode_Storage.append(f"; 已选中: 顶点{selected_disk['vertex_index']} 角度{selected_disk['offset_angle']}°")
                    
                    # 如果所有位置都有碰撞（得分<=3），输出Complex Wipe
                    if best_score <3:
                        Gcode_Storage.append(f"; Complex Wipe - 最佳得分{best_score}，无法满足第3层无碰撞要求")
                        #立即在Gcode_storage开始向回查找最近的一个;Pre-glue preparation记作preglue_index
                        #找到之后，从preglue_index处向上查找最近的; Z_HEIGHT提取z，以及最近的; LAYER_HEIGHT:提取层高。
                        #最后算出来的值作为降温z高度
                        #从preglue_index开始向上查找，找到最近的一个; FEATURE: Support interface，记作support_index
                        #从support_index开始向下查找，找到第一个G1 X开头且含有E的命令，提取其XY
                        #开始插入：降温
                        #+0.3的跳z后空驶到该xy，再调整z。
                        #然后命令M109 S200，喷嘴降温。
                        #然后+0.3的跳z
                        #最后把上述内容插入Gcode_Storage中preglue_index的位置
                        #然后插入:复温
                        #在content【】从i向后查找到第一个含有G1 X且含有E的命令，然后从它开始向前查找第一个含有G1 X且不含有E的命令,提取其XY
                        #+0.3的跳z后空驶到该xy，再调整z。
                        #然后命令M109 S[temperature]，喷嘴复温。
                        #然后插入";复温"
                        #最后将上述内容直接append即可，不需要指定index
                        
                        # 立即在Gcode_storage开始向回查找最近的一个;Pre-glue preparation
                        preglue_index = -1
                        for idx in range(len(Gcode_Storage)-1, -1, -1):
                            if Gcode_Storage[idx].startswith(";Pre-glue preparation"):
                                preglue_index = idx
                                break
                        
                        if preglue_index >= 0:
                            # 找到之后，从preglue_index处向上查找最近的; Z_HEIGHT
                            z_height_value = None
                            for idx in range(preglue_index-1, -1, -1):
                                if Gcode_Storage[idx].startswith("; Z_HEIGHT:"):
                                    z_height_value = float(Gcode_Storage[idx].split(':')[1].strip())
                                    break
                            
                            # 以及最近的; LAYER_HEIGHT:提取层高
                            layer_height_value = None
                            for idx in range(preglue_index-1, -1, -1):
                                if Gcode_Storage[idx].startswith("; LAYER_HEIGHT:"):
                                    layer_height_value = float(Gcode_Storage[idx].split(':')[1].strip())
                                    break
                            
                            # 最后算出来的值作为降温z高度
                            cool_down_z = None
                            if z_height_value is not None and layer_height_value is not None:
                                cool_down_z = z_height_value + layer_height_value * 0.5  # 示例计算，您可以根据需要调整
                            
                            # 从preglue_index开始向上查找，找到最近的一个; FEATURE: Support interface
                            support_index = -1
                            for idx in range(preglue_index-1, -1, -1):
                                if Gcode_Storage[idx].startswith("; FEATURE: Support interface"):
                                    support_index = idx
                                    break
                            
                            # 从support_index开始向下查找，找到第一个G1 X开头且含有E的命令，提取其XY
                            target_x, target_y = None, None
                            if support_index >= 0:
                                for idx in range(support_index+1, len(Gcode_Storage)):
                                    line = Gcode_Storage[idx]
                                    if line.startswith('G1') and 'X' in line and 'Y' in line and 'E' in line:
                                        x_match = re.search(r'X([\d\.-]+)', line)
                                        y_match = re.search(r'Y([\d\.-]+)', line)
                                        if x_match and y_match:
                                            target_x = float(x_match.group(1))
                                            target_y = float(y_match.group(1))
                                            break
                            
                            # 构建降温指令列表
                            cool_down_commands = [
                            ]
                            
                            if target_x is not None and target_y is not None:
                                cool_down_commands.extend([
                                    f"G1 Z{cool_down_z + 0.3:.2f} F1200" if cool_down_z else f"G1 Z{current_z + 0.3:.2f} F1200",
                                    f"G1 X{target_x:.3f} Y{target_y:.3f} F{para.Travel_Speed*60}",
                                    f"G1 Z{cool_down_z:.2f}" if cool_down_z else f"G1 Z{current_z:.2f}"
                                ])
                            if para.Filament_Type == "PLA":
                                cool_down_commands.append(f"M109 S180")
                            elif para.Filament_Type == "ABS":
                                cool_down_commands.append(f"M104 S210")
                            elif para.Filament_Type == "PETG":
                                cool_down_commands.append(f"M109 S210")
                            
                            # cool_down_commands.append(f"M109 S200")
                            cool_down_commands.append(f"G1 Z{cool_down_z + 0.3:.2f}" if cool_down_z else f"G1 Z{current_z + 0.3:.2f}")
                            
                            # 插入降温指令
                            for line in reversed(cool_down_commands):
                                Gcode_Storage.insert(preglue_index, line)
                            
                            # ===== 复温部分 =====
                            # 从i向后查找到第一个含有G1 X且含有E的命令
                            resume_x, resume_y = None, None
                            for idx in range(i, len(content)):
                                line = content[idx]
                                if line.startswith('G1') and 'X' in line and 'Y' in line and 'E' in line:
                                    x_match = re.search(r'X([\d\.-]+)', line)
                                    y_match = re.search(r'Y([\d\.-]+)', line)
                                    if x_match and y_match:
                                        resume_x = float(x_match.group(1))
                                        resume_y = float(y_match.group(1))
                                    break
                            
                            # 构建复温指令
                            resume_commands = [
                            ]
                            
                            if resume_x is not None and resume_y is not None:
                                resume_commands.extend([
                                    f"G1 Z{cool_down_z + 0.3:.2f}" if cool_down_z else f"G1 Z{current_z + 0.3:.2f}",
                                    f"G1 X{resume_x:.3f} Y{resume_y:.3f} F{para.Travel_Speed*60}",
                                    f"G1 Z{cool_down_z:.2f}" if cool_down_z else f"G1 Z{current_z:.2f}"
                                ])
                            
                            # resume_commands.append(f"M109 S"+str((para.Nozzle_Switch_Tempature-15)))
                            resume_commands.append(f"M104 S"+str((para.Nozzle_Switch_Tempature)))
                            resume_commands.append(para.Refill_Extrude_Command)
                            
                            # 直接append复温指令
                            Gcode_Storage.extend(resume_commands)
                        selected_disk = None
                        
                    
                    # ===== 使用选中的圆盘生成G-code（实际圆盘，不是扩大的） =====
                    if selected_disk:
                        Is_First_Layer_Disk=False
                        
                        LAYER_HEIGHT=round(0.75*para.Nozzle_Diameter,2)
                        Gcode_Storage.append(f"; LAYER_HEIGHT: "f"{LAYER_HEIGHT:.2f}")
                        # para.Support_Layer=selected_disk的score
                        para.Support_Layer=best_score
                        if not last_selected_disk:
                            LAYER_HEIGHT=round(0.75*para.Nozzle_Diameter,2)
                            if Disk_history==[]:
                                #这玩意是第一个disk
                                if Last_Layer_Height==para.First_Layer_Height:
                                    LAYER_HEIGHT=para.First_Layer_Height
                                    Is_First_Layer_Disk=True
                                    best_score=0


                        last_selected_disk =selected_disk
                        Disk_history.append((selected_disk, Current_Layer_Height))
                        if len(Disk_history)>19:
                            Disk_history.pop(0)
                        #接下来分析是否与前几层的Disk出现重叠，如果x,y坐标在1mm内，就判定为可能重叠。需要根据可能重叠的disk与当前disk的高度值的差值/para.Typical_Layer_Height计算出差多少层。如果这个数字小于5，那么best_score=这个数字
                        # 分析是否与前几层的Disk出现重叠
                        for disk_data, layer_height in reversed(Disk_history[:-1]):
                            if disk_data is None:
                                continue
                                
                            # 计算坐标差
                            dx = abs(disk_data['center'][0] - selected_disk['center'][0])
                            dy = abs(disk_data['center'][1] - selected_disk['center'][1])
                            
                            # 如果在1mm内，判定为可能重叠
                            if dx <= 2.0 and dy <= 2.0:
                                
                                # 计算层数差
                                layer_diff = abs(Current_Layer_Height - layer_height) / para.Typical_Layer_Height
                                layer_diff = int(round(layer_diff))
                                layer_diff=layer_diff-1#因为层差1层，值就应该为0
                                # 如果层数差小于5，更新best_score
                                if layer_diff < 5:
                                    best_score = min(best_score, layer_diff)
                                    if best_score==0:
                                        LAYER_HEIGHT=max(Current_Layer_Height-Last_Layer_Height,0.04)
                                    # print(f"; 与下层圆盘重叠，层数差{layer_diff}，更新best_score={best_score}")
                                    # Gcode_Storage.append(f"; 与下层圆盘重叠，层数差{layer_diff}，更新best_score={best_score}")
                                break
                            
                        center_x, center_y = selected_disk['center']
                        vertex_x, vertex_y = selected_disk['vertex']
                        normal = selected_disk['normal']
                        perpendicular = selected_disk['perpendicular']
                        Gcode_Storage.append(f"; 生成Disk - 从顶点{selected_disk['vertex_index']} 角度{selected_disk['offset_angle']}°伸出")
                        Gcode_Storage.append(f"; 中心: ({center_x:.2f}, {center_y:.2f})")
                        
                        
                        # 计算左右两侧的偏移量（间距为0，完全贴合）
                        left_offset = perpendicular * (LINE_WIDTH/2)  # 偏移一个线宽
                        right_offset = -perpendicular * (LINE_WIDTH/2)  # 负方向偏移一个线宽

                        # 四个顶点（顺时针方向）
                        p1 = (vertex_x + left_offset[0], vertex_y + left_offset[1])      # 支撑端左侧
                        p2 = (center_x + left_offset[0], center_y + left_offset[1])      # 圆盘端左侧
                        p3 = (center_x + right_offset[0], center_y + right_offset[1])    # 圆盘端右侧
                        p4 = (vertex_x + right_offset[0], vertex_y + right_offset[1])    # 支撑端右侧

                        # 回到p1闭合
                        # p1 -> p2 -> p3 -> p4 -> p1 形成一个闭合长方形

                        Gcode_Storage.append("; 绘制闭合长方形连接")
                        
                        # 计算每边的挤出量
                        edge_length = EXTENSION_LENGTH  # 纵向边长度
                        edge_volume = edge_length * LAYER_HEIGHT * LINE_WIDTH
                        filament_area = np.pi * (1.75/2)**2
                        edge_extrusion = edge_volume / filament_area

                        cross_length = LINE_WIDTH * 2  # 横向边长度（两个线宽）
                        cross_volume = cross_length * LAYER_HEIGHT * LINE_WIDTH
                        cross_extrusion = cross_volume / filament_area

                        #只有当Current_Layer_Height=First_Layer_Height时，才执行
                        # if Current_Layer_Height==para.First_Layer_Height:
                        #     LAYER_HEIGHT=para.First_Layer_Height
                        #     # 计算每边的挤出量
                        #     edge_length = EXTENSION_LENGTH  # 纵向边长度
                        #     edge_volume = edge_length * LAYER_HEIGHT * LINE_WIDTH
                        #     filament_area = np.pi * (1.75/2)**2
                        #     edge_extrusion = edge_volume / filament_area

                        #     cross_length = LINE_WIDTH * 2  # 横向边长度（两个线宽）
                        #     cross_volume = cross_length * LAYER_HEIGHT * LINE_WIDTH
                        #     cross_extrusion = cross_volume / filament_area

                        #     # 这一层的连接线：
                        #     # p1 -> p2 (左侧纵向)
                        #     Gcode_Storage.append(f"G1 X{p1[0]:.3f} Y{p1[1]:.3f} F"+str(para.Travel_Speed*60))
                        #     Gcode_Storage.append(f"G1 X{p2[0]:.3f} Y{p2[1]:.3f} E{edge_extrusion:.6f} F500")

                        #     # p2 -> p3 (上侧横向)
                        #     Gcode_Storage.append(f"G1 X{p3[0]:.3f} Y{p3[1]:.3f} E{cross_extrusion:.6f} F500")

                        #     # p3 -> p4 (右侧纵向)
                        #     Gcode_Storage.append(f"G1 X{p4[0]:.3f} Y{p4[1]:.3f} E{edge_extrusion:.6f} F500")

                        #     # p4 -> p1 (下侧横向) - 回到起点，闭合长方形
                        #     Gcode_Storage.append(f"G1 X{p1[0]:.3f} Y{p1[1]:.3f} E{cross_extrusion:.6f} F500")
                         # ===== 4. 先画圆盘（从内向外）=====
                        Gcode_Storage.append(";Paint Disk")
                        # 移动到圆盘中心
                        
                        
                        Gcode_Storage.append(f"G1 X{center_x:.3f} Y{center_y:.3f} F"+str(para.Travel_Speed*60))
                        Gcode_Storage.append(f"G1 Z{current_z+0.2:.2f}")
                        # Gcode_Storage.append(f"M109 S{para.Nozzle_Switch_Tempature}")
                        Gcode_Storage.append(f"M109 S{para.Nozzle_Switch_Tempature}")#温度回升
                        # Gcode_Storage.append("; LAYER_HEIGHT: "+str(LAYER_HEIGHT))
                        Gcode_Storage.append("; LINE_WIDTH: "+str(round(LINE_WIDTH,3)))

                        Gcode_Storage.append(para.Refill_Extrude_Command)#临时填充
                        # if LAYER_HEIGHT>=0.65*para.Nozzle_Diameter:
                        #     Gcode_Storage.append(f"G1 E{para.Retract_Length:.6f}")#增加填充
                        # Gcode_Storage.append(f"G1 E{para.Extrude_Length:.6f}")
                        # 绘制螺旋线（从内向外连续打印）
                        # 螺旋线参数
                        total_angle = 2 * np.pi * circles  # 总角度（圈数×2π）
                        steps = int(total_angle * 3)  # 每弧度5个点，保证平滑

                        # 移动到中心点
                        Gcode_Storage.append(f"G1 X{center_x:.3f} Y{center_y:.3f} F"+str(para.Travel_Speed*60))
                        Gcode_Storage.append(f"G1 E{para.Retract_Length:.6f}")#增加填充
                        #解释层高为LAYER_HEIGHT:
                        Gcode_Storage.append(f"; LAYER_HEIGHT: "+str(LAYER_HEIGHT))
                        Gcode_Storage.append(f"G1 Z{current_z:.2f}")
                        # print(LAYER_HEIGHT)
                        filament_area = np.pi * (1.75/2)**2  # filament截面积
                        Temp_Speed_disk=500
                        Temp_Speed_Add_Speed=0
                        # if not(LAYER_HEIGHT>=0.65*para.Nozzle_Diameter):
                        #     Temp_Speed_disk=1800
                        if LAYER_HEIGHT>=0.65*para.Nozzle_Diameter and current_z-LAYER_HEIGHT>para.First_Layer_Height:
                            for step in range(30, steps + 1):
                                t = step / steps  # 0→1
                                if t>0.86:
                                    pass
                                    # Temp_Speed_Add_Speed+=30
                                    # Temp_Speed_disk=600+Temp_Speed_Add_Speed
                                # 当前半径：从0线性增加到DISK_RADIUS
                                r = t * DISK_RADIUS
                                
                                # 当前角度：从0增加到total_angle
                                angle = t * total_angle
                                
                                # 计算当前点坐标
                                x = center_x + r * np.cos(angle)
                                y = center_y + r * np.sin(angle)
                                
                                if step == 30:
                                    # 第一个点只移动不挤出
                                    Gcode_Storage.append(f"G1 X{x:.3f} Y{y:.3f} F500")
                                    Gcode_Storage.append(f"G1 Z{current_z:.2f}")
                                else:
                                    # 计算上一圈半径和角度
                                    t_prev = (step - 1) / steps
                                    r_prev = t_prev * DISK_RADIUS
                                    angle_prev = t_prev * total_angle
                                    
                                    # 计算线段长度
                                    x_prev = center_x + r_prev * np.cos(angle_prev)
                                    y_prev = center_y + r_prev * np.sin(angle_prev)
                                    length = np.sqrt((x - x_prev)**2 + (y - y_prev)**2)
                                    
                                    # 挤出量 = 长度 × 层高 × 线宽 / filament截面积
                                    extrusion = (length * LAYER_HEIGHT * LINE_WIDTH) / filament_area
                                    
                                    Gcode_Storage.append(f"G1 X{x:.3f} Y{y:.3f} E{extrusion:.6f} F"+str(Temp_Speed_disk))

                        if LAYER_HEIGHT>=0.65*para.Nozzle_Diameter:
                            # if LAYER_HEIGHT >= 0.65 * para.Nozzle_Diameter:
                            if para.Filament_Type!="TPU":
                                Temp_Speed_disk =6000
                            else:
                                Temp_Speed_disk = 1800
                            
                            # ===== 绘制圆盘 - 平行直线填充 =====
                            Gcode_Storage.append("; 绘制圆盘 - 平行直线填充")
                            
                            # 移动到圆盘中心
                            Gcode_Storage.append(f"G1 X{center_x:.3f} Y{center_y:.3f} F"+str(para.Travel_Speed*60))
                            
                            # 计算圆盘的边界
                            x_min = center_x - DISK_RADIUS
                            x_max = center_x + DISK_RADIUS
                            y_min = center_y - DISK_RADIUS
                            y_max = center_y + DISK_RADIUS
                            
                            # 计算需要多少条填充线
                            line_spacing = LINE_WIDTH  # 线宽作为填充间距
                            num_lines = int(DISK_DIAMETER / line_spacing) + 1
                            
                            # 层高（用于挤出量计算）
                            fill_layer_height = 0.4 * para.Nozzle_Diameter
                            
                            # 从下到上逐行填充
                            for line_idx in range(num_lines):
                                # 当前行的Y坐标
                                y = y_min + line_idx * line_spacing
                                if y > y_max:
                                    break
                                
                                # 计算当前行与圆盘的交点X范围
                                dy = y - center_y
                                if abs(dy) > DISK_RADIUS - 0.01:
                                    continue
                                
                                dx = np.sqrt(DISK_RADIUS**2 - dy**2)
                                x_start = center_x - dx
                                x_end = center_x + dx
                                
                                # 根据行号决定填充方向（来回走）
                                if line_idx % 2 == 0:
                                    # 偶数行从左到右
                                    line_x_start = x_start
                                    line_x_end = x_end
                                else:
                                    # 奇数行从右到左
                                    line_x_start = x_end
                                    line_x_end = x_start
                                
                                # 移动到当前行的起点
                                Gcode_Storage.append(f"G1 X{line_x_start:.3f} Y{y:.3f} F"+str(para.Travel_Speed*60))
                                
                                # 计算本行长度和挤出量
                                line_length = abs(x_end - x_start)
                                if line_length < 0.05:
                                    continue
                                
                                # 挤出量 = 长度 × 层高 × 线宽 / filament截面积
                                extrusion = (line_length * fill_layer_height * LINE_WIDTH) / filament_area
                                
                                # 画填充线
                                Gcode_Storage.append(f"G1 X{line_x_end:.3f} Y{y:.3f} E{extrusion:.6f} F{Temp_Speed_disk}")
                            
                            # 最后画最外圈封边
                            Gcode_Storage.append("; 绘制最外圈封边")
                            
                            # 移动到圆的最右侧开始画圆
                            start_x = center_x + DISK_RADIUS
                            start_y = center_y
                            Gcode_Storage.append(f"G1 X{start_x:.3f} Y{start_y:.3f} F"+str(para.Travel_Speed*60))

                            # 计算外圈周长和挤出量
                            circumference = 2 * np.pi * DISK_RADIUS
                            total_extrusion = (circumference * fill_layer_height * LINE_WIDTH) / filament_area

                            # 用小线段画圆
                            segments = max(32, int(circumference / 0.5))  # 每0.3mm一个点，最少32段
                            segment_extrusion = total_extrusion / segments

                            for seg in range(1, segments + 1):
                                angle = 2 * np.pi * seg / segments
                                x = center_x + DISK_RADIUS * np.cos(angle)
                                y = center_y + DISK_RADIUS * np.sin(angle)
                                
                                Gcode_Storage.append(f"G1 X{x:.3f} Y{y:.3f} E{segment_extrusion:.6f} F{Temp_Speed_disk}")
                            
                            # 回到圆盘中心
                            Gcode_Storage.append(f"G1 X{center_x:.3f} Y{center_y:.3f} F"+str(para.Travel_Speed*60))

                        if LAYER_HEIGHT<0.65*para.Nozzle_Diameter:
                             # if LAYER_HEIGHT >= 0.65 * para.Nozzle_Diameter:
                            # Temp_Speed_disk = 1800
                            if para.Filament_Type!="TPU":
                                Temp_Speed_disk =6000
                            else:
                                Temp_Speed_disk = 1800
                            
                            # ===== 绘制圆盘 - 平行直线填充 =====
                            Gcode_Storage.append("; 绘制圆盘 - 平行直线填充")
                            
                            # 移动到圆盘中心
                            Gcode_Storage.append(f"G1 X{center_x:.3f} Y{center_y:.3f} F"+str(para.Travel_Speed*60))
                            
                            # 计算圆盘的边界
                            x_min = center_x - DISK_RADIUS
                            x_max = center_x + DISK_RADIUS
                            y_min = center_y - DISK_RADIUS
                            y_max = center_y + DISK_RADIUS
                            
                            # 计算需要多少条填充线
                            line_spacing = LINE_WIDTH  # 线宽作为填充间距
                            num_lines = int(DISK_DIAMETER / line_spacing) + 1
                            
                            # 层高（用于挤出量计算）
                            fill_layer_height = LAYER_HEIGHT
                            
                            # 从下到上逐行填充
                            for line_idx in range(num_lines):
                                # 当前行的Y坐标
                                y = y_min + line_idx * line_spacing
                                if y > y_max:
                                    break
                                
                                # 计算当前行与圆盘的交点X范围
                                dy = y - center_y
                                if abs(dy) > DISK_RADIUS - 0.01:
                                    continue
                                
                                dx = np.sqrt(DISK_RADIUS**2 - dy**2)
                                x_start = center_x - dx
                                x_end = center_x + dx
                                
                                # 根据行号决定填充方向（来回走）
                                if line_idx % 2 == 0:
                                    # 偶数行从左到右
                                    line_x_start = x_start
                                    line_x_end = x_end
                                else:
                                    # 奇数行从右到左
                                    line_x_start = x_end
                                    line_x_end = x_start
                                
                                # 移动到当前行的起点
                                Gcode_Storage.append(f"G1 X{line_x_start:.3f} Y{y:.3f} F"+str(para.Travel_Speed*60))
                                
                                # 计算本行长度和挤出量
                                line_length = abs(x_end - x_start)
                                if line_length < 0.05:
                                    continue
                                
                                # 挤出量 = 长度 × 层高 × 线宽 / filament截面积
                                extrusion = (line_length * fill_layer_height * LINE_WIDTH) / filament_area
                                
                                # 画填充线
                                Gcode_Storage.append(f"G1 X{line_x_end:.3f} Y{y:.3f} E{extrusion:.6f} F{Temp_Speed_disk}")
                            
                            # 最后画最外圈封边
                            Gcode_Storage.append("; 绘制最外圈封边")
                            
                            # 移动到圆的最右侧开始画圆
                            start_x = center_x + DISK_RADIUS
                            start_y = center_y
                            Gcode_Storage.append(f"G1 X{start_x:.3f} Y{start_y:.3f} F"+str(para.Travel_Speed*60))

                            # 计算外圈周长和挤出量
                            circumference = 2 * np.pi * DISK_RADIUS
                            total_extrusion = (circumference * fill_layer_height * LINE_WIDTH) / filament_area

                            # 用小线段画圆
                            segments = max(32, int(circumference / 0.5))  # 每0.3mm一个点，最少32段
                            segment_extrusion = total_extrusion / segments

                            for seg in range(1, segments + 1):
                                angle = 2 * np.pi * seg / segments
                                x = center_x + DISK_RADIUS * np.cos(angle)
                                y = center_y + DISK_RADIUS * np.sin(angle)
                                
                                Gcode_Storage.append(f"G1 X{x:.3f} Y{y:.3f} E{segment_extrusion:.6f} F{Temp_Speed_disk}")

                            # 回到圆盘中心
                            Gcode_Storage.append(f"G1 X{center_x:.3f} Y{center_y:.3f} F"+str(para.Travel_Speed*60))

                        Gcode_Storage.append(f"; WIPE_START")
                        # 螺旋线参数
                        total_angle = 2 * np.pi * circles  # 总角度
                        wipe_angle = total_angle / 15  # 1/3圈的角度

                        # 继续沿着螺旋线走1/3圈用于擦拭
                        start_angle = total_angle
                        end_angle = total_angle + wipe_angle
                        wipe_steps = int(wipe_angle * 3)  # 每弧度10个点

                        for step in range(1, wipe_steps + 1):
                            t = step / wipe_steps
                            angle = start_angle + t * wipe_angle
                            r = DISK_RADIUS-para.Nozzle_Diameter
                            
                            x = center_x + r * np.cos(angle)
                            y = center_y + r * np.sin(angle)
                            
                            if step == 1:
                                # 第一段：移动+回抽70%
                                Gcode_Storage.append(f"G1 X{x:.3f} Y{y:.3f} E-{0.7*para.Retract_Length:.4f} F"+str(min(60*200,60*para.Wall_Print_Speed)))
                            elif step == wipe_steps:
                                # 最后一段：移动+回抽30%
                                Gcode_Storage.append(f"; WIPE_END")
                                Gcode_Storage.append(f"G1 E-{0.3*para.Retract_Length:.4f}")
                            else:
                                # 中间段：只移动
                                Gcode_Storage.append(f"G1 X{x:.3f} Y{y:.3f} F"+str(min(60*200,60*para.Wall_Print_Speed)))
                        # Gcode_Storage.append(f"G1 Z{current_z + 0.3:.2f} F1200")
                        
                        Gcode_Storage.append("G1 Z"+str(round(Current_Layer_Height+0.2,2)))#Z连接线
                        #向下查找最近的挤出，并且要求该段挤出的速度执行调速
                        para.Speed_Smooth_Sum=1
                        # print(best_score)
                        # ===== 向下复制best_score层连接线 =====
                        if best_score > 0:
                            # 从后往前遍历，找到就插入，不影响前面未遍历的索引
                            i = len(Gcode_Storage) - 1
                            while i >= 0:
                                if Gcode_Storage[i].startswith("; Z_HEIGHT:"):
                                    j=i+1
                                    while j<=len(Gcode_Storage)-1:
                                        if Gcode_Storage[j].startswith("; WIPE_END"):
                                            j=j+2
                                            break
                                        j=j+1
                                        if j>i+20 or j>len(Gcode_Storage)-1 or Gcode_Storage[j].startswith(";Pre-glue preparation"):
                                            j=i
                                            break
                                    
                                    Temp_Z = float(Gcode_Storage[i].split(':')[1].strip())
                                    
                                    if Temp_Z<para.First_Layer_Height+0.2:
                                        Temp_Z=Temp_Z+0.2
                                    # 确定这一层的层高
                                    layer_height = 0.7 * para.Nozzle_Diameter
                                    
                                    # 计算各段挤出量
                                    filament_area = np.pi * (1.75/2)**2
                                    
                                    # 正方形边长 = 2 × 喷嘴直径
                                    square_size = 1* NOZZLE_DIAMETER
                                    
                                    # 移动步长 = 喷嘴直径
                                    step_size = NOZZLE_DIAMETER
                                    
                                    # 长边长度（从起点到终点）
                                    len_long = square_size
                                    vol_long = len_long * layer_height * LINE_WIDTH
                                    extr_long = vol_long / filament_area
                                    
                                    # 转角线长度（线宽）
                                    len_corner = LINE_WIDTH
                                    vol_corner = len_corner * layer_height * LINE_WIDTH
                                    extr_corner = vol_corner / filament_area
                                    
                                    # 计算方向向量
                                    center_to_vertex = np.array([vertex_x - center_x, vertex_y - center_y])
                                    center_to_vertex_length = np.linalg.norm(center_to_vertex)
                                    direction_long = center_to_vertex / center_to_vertex_length
                                    
                                    # 垂直方向（用于双线偏移）
                                    perp_long = np.array([-direction_long[1], direction_long[0]])
                                    
                                    # 双线间距 = 喷嘴直径
                                    line_spacing = NOZZLE_DIAMETER
                                    
                                    # 总长度（支撑端到中心）
                                    total_length = EXTENSION_LENGTH

                                    # 想要延伸到的目标长度（超过中心的部分）
                                    TARGET_LENGTH = total_length + 2.0  # 例如，超过中心2mm

                                    # 计算需要的正方形数量（向上取整）
                                    num_squares = int(np.ceil(TARGET_LENGTH / step_size))
                                    # # 计算需要多少个正方形
                                    # num_squares = int(total_length / step_size)
                                    
                                    # 构建连接线列表
                                    connection_lines = []
                                    if para.Filament_Type == "PLA":
                                        connection_lines.extend([f"M104 S"+str(para.Nozzle_Switch_Tempature-40)])
                                    elif para.Filament_Type == "ABS" or para.Filament_Type == "PETG":
                                        connection_lines.extend([f"M104 S"+str(para.Nozzle_Switch_Tempature-30)])
                                    if para.Filament_Type == "PLA" or para.Filament_Type == "PETG":
                                        if MachineType_Main == "A1" or MachineType_Main == "A1Mini":
                                            connection_lines.extend([f"M106 S255"])
                                        else:
                                            connection_lines.extend([f"M106 P1 S255"])
                                    connection_lines.extend([f"G1 Z{(Temp_Z+0.3):.2f}"])
                                    # 先移动到第一个正方形的起点
                                    if num_squares > 0:
                                        current_offset = 0
                                        start_x = vertex_x - direction_long[0] * current_offset
                                        start_y = vertex_y - direction_long[1] * current_offset
                                        
                                        start1 = (start_x + perp_long[0] * (line_spacing/2),
                                                start_y + perp_long[1] * (line_spacing/2))
                                        
                                        connection_lines.extend([
                                            f"G1 X{start1[0]:.3f} Y{start1[1]:.3f} F"+str(para.Travel_Speed*60)
                                        ])
                                    # connection_lines.extend([f"G1 X{start1[0]:.3f} Y{start1[1]:.3f} F"+str(para.Travel_Speed*60)])
                                    Temp_Z_Adjust = max(para.First_Layer_Height, Temp_Z-para.First_Layer_Height)
                                    connection_lines.extend(["; FEATURE: Top surface"])
                                    connection_lines.extend([f"G1 Z{Temp_Z_Adjust:.2f}"])
                                    connection_lines.extend([f"G1 E{para.Retract_Length:.3f}"])
                                    Z_Accumulate = 0
                                    
                                    # 从支撑端开始，依次叠正方形
                                    for square_idx in range(num_squares):
                                        if Z_Accumulate<0.19:
                                            Z_Accumulate+=0.06
                                        # 当前正方形的起点偏移（向支撑侧内部移动）
                                        current_offset = square_idx * step_size
                                        if current_offset >= TARGET_LENGTH:
                                            break
                                        
                                        # 计算当前正方形的起点（从顶点向支撑侧内部移动current_offset）
                                        start_x = vertex_x - direction_long[0] * current_offset
                                        start_y = vertex_y - direction_long[1] * current_offset
                                        
                                        # 正方形的终点（向圆盘方向移动square_size）- 注意这里是负号
                                        end_x = start_x - direction_long[0] * square_size
                                        end_y = start_y - direction_long[1] * square_size
                                        
                                        # 起点双线
                                        start1 = (start_x + perp_long[0] * (line_spacing/2),
                                                start_y + perp_long[1] * (line_spacing/2))
                                        start2 = (start_x - perp_long[0] * (line_spacing/2),
                                                start_y - perp_long[1] * (line_spacing/2))
                                        
                                        # 终点双线
                                        end1 = (end_x + perp_long[0] * (line_spacing/2),
                                                end_y + perp_long[1] * (line_spacing/2))
                                        end2 = (end_x - perp_long[0] * (line_spacing/2),
                                                end_y - perp_long[1] * (line_spacing/2))
                                        
                                        connection_lines.extend([
                                            f"; 正方形 {square_idx+1} - 偏移 {current_offset:.2f}mm - 层高{layer_height:.2f}mm",
                                            f"G1 X{start1[0]:.3f} Y{start1[1]:.3f} F"+str(para.Travel_Speed*60),  # 移动到起点1
                                            f"G1 X{end1[0]:.3f} Y{end1[1]:.3f} E{extr_long:.6f} F500",  # 从起点1到终点1（向圆盘方向）
                                            f"G1 Z{(Temp_Z_Adjust)+Z_Accumulate:.2f}",
                                            f"G1 X{end2[0]:.3f} Y{end2[1]:.3f} E{extr_corner:.6f} F500",  # 转到终点2
                                            f"G1 Z{(Temp_Z_Adjust)+Z_Accumulate-0.03:.2f}",
                                            f"G1 X{start2[0]:.3f} Y{start2[1]:.3f} E{extr_long:.6f} F500",  # 从终点2回到起点2（向支撑方向）
                                            f"G1 X{start1[0]:.3f} Y{start1[1]:.3f} E{extr_corner:.6f} F500", # 转回起点1（闭合）

                                            f"G1 Z{(Temp_Z_Adjust)+Z_Accumulate:.2f}"
                                        ])
                                    # connection_lines.extend([f"G1 E-{para.Retract_Length:.3f}"])
                                    if connection_lines:
                                        # 最后一个正方形的终点位置（end1）作为擦拭起点
                                        last_end1 = end1  # 最后一个正方形的终点1
                                        
                                        # 向支撑侧方向擦拭1mm（速度慢一点，防止撞断）
                                        wipe_x = last_end1[0] + direction_long[0] * 1.0  # 向支撑侧移动1mm
                                        wipe_y = last_end1[1] + direction_long[1] * 1.0
                                        
                                        connection_lines.extend([
                                            f"; WIPE_START",
                                            f"G1 X{wipe_x:.3f} Y{wipe_y:.3f} E-{para.Retract_Length:.3f} F1800",
                                            f"; WIPE_END"
                                        ])
                                    # 在找到的; Z_HEIGHT前面插入连接线
                                    for line in reversed(connection_lines):
                                        Gcode_Storage.insert(j, line)
                                    break
                                i-=1
                        elif best_score == 0:
                            # print("找到常规接触面")
                            #best_score = 0说明下面存在常规接触面,或者是首层。如果这时候发现Is_First_Layer_Disk==True，则说明是第一层，进行连接，但是以普通闭合长方形。长度相同
                            if Is_First_Layer_Disk:
                                # 从后往前遍历，找到就插入，不影响前面未遍历的索引
                                i = len(Gcode_Storage) - 1
                                while i >= 0:
                                    if Gcode_Storage[i].startswith("; Z_HEIGHT:"):
                                        j=i+1
                                        while j<=len(Gcode_Storage)-1:
                                            if Gcode_Storage[j].startswith("; WIPE_END"):
                                                j=j+2
                                                break
                                            j=j+1
                                            if j>i+20 or j>len(Gcode_Storage)-1 or Gcode_Storage[j].startswith(";Pre-glue preparation"):
                                                j=i
                                                break
                                            
                                        Temp_Z = float(Gcode_Storage[i].split(':')[1].strip())
                                        
                                        # 确定这一层的层高
                                        layer_height = para.First_Layer_Height
                                        
                                        # 计算各段挤出量
                                        filament_area = np.pi * (1.75/2)**2
                                        
                                        # 延长长度2mm
                                        EXTRA_LENGTH = 2.0
                                        
                                        # 总长度（支撑端到中心 + 延长2mm）
                                        total_length = EXTENSION_LENGTH + EXTRA_LENGTH
                                        
                                        # 长边长度
                                        len_long = total_length
                                        vol_long = len_long * layer_height * LINE_WIDTH
                                        extr_long = vol_long / filament_area
                                        
                                        # 转角线长度（线宽）
                                        len_corner = LINE_WIDTH
                                        vol_corner = len_corner * layer_height * LINE_WIDTH
                                        extr_corner = vol_corner / filament_area
                                        
                                        # 计算方向向量
                                        center_to_vertex = np.array([vertex_x - center_x, vertex_y - center_y])
                                        center_to_vertex_length = np.linalg.norm(center_to_vertex)
                                        direction_long = center_to_vertex / center_to_vertex_length
                                        
                                        # 垂直方向（用于双线偏移）
                                        perp_long = np.array([-direction_long[1], direction_long[0]])
                                        
                                        # 双线间距 = 喷嘴直径
                                        line_spacing = NOZZLE_DIAMETER
                                        
                                        # 计算终点（延长2mm）
                                        end_x = vertex_x - direction_long[0] * total_length
                                        end_y = vertex_y - direction_long[1] * total_length
                                        
                                        # 起点双线
                                        start1 = (vertex_x + perp_long[0] * (line_spacing/2),
                                                vertex_y + perp_long[1] * (line_spacing/2))
                                        start2 = (vertex_x - perp_long[0] * (line_spacing/2),
                                                vertex_y - perp_long[1] * (line_spacing/2))
                                        
                                        # 终点双线
                                        end1 = (end_x + perp_long[0] * (line_spacing/2),
                                                end_y + perp_long[1] * (line_spacing/2))
                                        end2 = (end_x - perp_long[0] * (line_spacing/2),
                                                end_y - perp_long[1] * (line_spacing/2))
                                        
                                        # 构建连接线
                                        connection_lines = [
                                            f"; 第一层连接线 - 层高{layer_height:.2f}mm (延长2mm)",
                                            f"G1 Z{para.First_Layer_Height+0.2:.2f}",
                                            f"G1 X{start1[0]:.3f} Y{start1[1]:.3f} F"+str(para.Travel_Speed*60),
                                            f"G1 E{para.Retract_Length:.3f}",
                                            f"G1 Z{para.First_Layer_Height:.2f}",
                                            f"G1 X{end1[0]:.3f} Y{end1[1]:.3f} E{extr_long:.6f} F500",
                                            f"G1 X{end2[0]:.3f} Y{end2[1]:.3f} E{extr_corner:.6f} F500",
                                            f"G1 X{start2[0]:.3f} Y{start2[1]:.3f} E{extr_long:.6f} F500",
                                            f"G1 X{start1[0]:.3f} Y{start1[1]:.3f} E{extr_corner:.6f} F500",

                                        ]
                                        
                                        # 在找到的; Z_HEIGHT前面插入连接线
                                        for line in reversed(connection_lines):
                                            Gcode_Storage.insert(j, line)
                                        
                                        break  # 只处理找到的第一个Z_HEIGHT
                                    
                                    i -= 1
                            else:
                                #直线用于加强连接，但是不是加长2mm，而是短2mm。其余与刚刚构造的常规闭合相同，它也需要Wipe.但是速度可以是str(para.Travel_Speed*60)
                                i = len(Gcode_Storage) - 1
                                while i >= 0:
                                    if Gcode_Storage[i].startswith("; Z_HEIGHT:"):
                                        Temp_Z = float(Gcode_Storage[i].split(':')[1].strip())
                                        if Temp_Z >= para.First_Layer_Height+0.2:
                                            Temp_Z = Temp_Z - 0.1
                                        j=i+1
                                        while j<=len(Gcode_Storage)-1:
                                            if Gcode_Storage[j].startswith("; WIPE_END"):
                                                j=j+2
                                                break
                                            j=j+1   
                                            if j>i+20 or j>len(Gcode_Storage)-1 or Gcode_Storage[j].startswith(";Pre-glue preparation"):
                                                j=i
                                                break
                                        # 确定这一层的层高
                                        layer_height = max(Current_Layer_Height-Last_Layer_Height,0.04)
                                        
                                        # 计算各段挤出量
                                        filament_area = np.pi * (1.75/2)**2
                                        
                                        # 缩短长度2mm
                                        SHORTEN_LENGTH = 2.0
                                        
                                        # 总长度（支撑端到中心 - 缩短2mm）
                                        total_length = max(0.1, EXTENSION_LENGTH - SHORTEN_LENGTH)  # 确保不为负
                                        
                                        # 长边长度
                                        len_long = total_length
                                        vol_long = len_long * layer_height * LINE_WIDTH
                                        extr_long = vol_long / filament_area
                                        
                                        # 转角线长度（线宽）
                                        len_corner = LINE_WIDTH
                                        vol_corner = len_corner * layer_height * LINE_WIDTH
                                        extr_corner = vol_corner / filament_area
                                        
                                        # 计算方向向量
                                        center_to_vertex = np.array([vertex_x - center_x, vertex_y - center_y])
                                        center_to_vertex_length = np.linalg.norm(center_to_vertex)
                                        direction_long = center_to_vertex / center_to_vertex_length
                                        
                                        # 垂直方向（用于双线偏移）
                                        perp_long = np.array([-direction_long[1], direction_long[0]])
                                        
                                        # 双线间距 = 喷嘴直径
                                        line_spacing = NOZZLE_DIAMETER
                                        
                                        # 计算终点（缩短2mm）
                                        end_x = vertex_x - direction_long[0] * total_length
                                        end_y = vertex_y - direction_long[1] * total_length
                                        
                                        # 起点双线
                                        start1 = (vertex_x + perp_long[0] * (line_spacing/2),
                                                vertex_y + perp_long[1] * (line_spacing/2))
                                        start2 = (vertex_x - perp_long[0] * (line_spacing/2),
                                                vertex_y - perp_long[1] * (line_spacing/2))
                                        
                                        # 终点双线
                                        end1 = (end_x + perp_long[0] * (line_spacing/2),
                                                end_y + perp_long[1] * (line_spacing/2))
                                        end2 = (end_x - perp_long[0] * (line_spacing/2),
                                                end_y - perp_long[1] * (line_spacing/2))
                                        
                                        # 构建连接线
                                        connection_lines = [
                                            f"; 加强连接线 - 层高{layer_height:.2f}mm (缩短2mm)",
                                            f"G1 Z{Temp_Z+0.3:.3f}",
                                            f"G1 E{para.Retract_Length:.3f}",
                                            f"G1 X{start1[0]:.3f} Y{start1[1]:.3f} F"+str(para.Travel_Speed*60),
                                            f"G1 Z{Temp_Z:.3f}",
                                            f"G1 X{end1[0]:.3f} Y{end1[1]:.3f} E{extr_long:.6f} F500",
                                            f"G1 X{end2[0]:.3f} Y{end2[1]:.3f} E{extr_corner:.6f} F500",
                                            f"G1 X{start2[0]:.3f} Y{start2[1]:.3f} E{extr_long:.6f} F500",
                                            f"G1 X{start1[0]:.3f} Y{start1[1]:.3f} E{extr_corner:.6f} F500",
                                            f"; WIPE_START",
                                            f"G1 X{end1[0]:.3f} Y{end1[1]:.3f} E-{para.Retract_Length:.3f} F"+str(para.Travel_Speed*60),
                                            f"; WIPE_END"
                                        ]
                                        
                                        # 在找到的; Z_HEIGHT前面插入连接线
                                        for line in reversed(connection_lines):
                                            Gcode_Storage.insert(j, line)
                                        
                                        break  # 只处理找到的第一个Z_HEIGHT
                                    
                                    i -= 1    
                    Gcode_Storage.append("; LAYER_HEIGHT: "+str(para.Typical_Layer_Height))
                    Gcode_Storage.append("; FEATURE: Inner wall")
                    Gcode_Storage.append("; 支撑圆盘生成完成")
                
        # if para.Speed_Smooth_Sum==1 and LastGCommand.find("G1 F") != -1:
        #     Gcode_Storage.append(";Adjusting speed after printing tower")
        #     Gcode_Storage.append("G1 F"+str((max(35*60,para.Support_Interface_Speed/2*60))))
        #     para.Speed_Smooth_Sum=0

        if para.Remove_G3_Flag==True and CurrGCommand.find("G1 X") != -1 and "E" in CurrGCommand:
            para.Remove_G3_Flag = False

        if para.Remove_G3_Flag==True and CurrGCommand.find("G3 Z") != -1:
            para.Remove_G3_Flag = False
            Allow_Print_Flag=False#不允许输出G3指令
        if CurrGCommand.startswith("; SKIPTYPE: head_wrap_detect"):
            Allow_Print_Flag=False
            # print("Gtriggered head wrap detect：CurrGCommand:"+CurrGCommand)
            para.Remove_wrap_detect_flag=True
        if para.Remove_wrap_detect_flag==True and CurrGCommand.find("; SKIPPABLE_END") != -1:
            para.Remove_wrap_detect_flag=False
            Allow_Print_Flag=True
        # if Recent_Tower_Print_Flag==True and CurrGCommand.find("; BEFORE_LAYER_CHANGE") != -1:
        #     Allow_Print_Flag=False
        # if Recent_Tower_Print_Flag==True and LastGCommand.find(";WIPE_END") != -1:
        #     Recent_Tower_Print_Flag=False
        #     Allow_Print_Flag=True

        if Allow_Print_Flag==True:
            Gcode_Storage.append(CurrGCommand)
        if CurrGCommand.find(";Lower pentip") != -1:
            Gcode_Storage.append("G1 Z" + str(round(CurrMax_Tower_Height+para.Z_Offset, 3)))    
        if CurrGCommand.find(";Shielding Nozzle") != -1:
            Gcode_Storage.append(Process_GCode_Offset("G1 X25 Y25", para.Wiper_x-5, para.Wiper_y-5, Current_Layer_Height+3,'normal').strip("\n"))
            Gcode_Storage.append("G1 Z"+ str(round(LastMax_Tower_Height, 3))) #adjust z
            Variable_Wipe_Code="G1 X15 Y2"+get_pseudo_random()
            if para.Filament_Type=="PLA":
                Gcode_Storage.append(Process_GCode_Offset(Variable_Wipe_Code, para.Wiper_x-5, para.Wiper_y-5, CurrMax_Tower_Height+3,'normal').strip("\n")) #Wipe*1
                Gcode_Storage.append(Process_GCode_Offset("G1 X25 Y25", para.Wiper_x-5, para.Wiper_y-5, CurrMax_Tower_Height+3,'normal').strip("\n")) #Wipe*2
                Gcode_Storage.append(Process_GCode_Offset(Variable_Wipe_Code, para.Wiper_x-5, para.Wiper_y-5, CurrMax_Tower_Height+3,'normal').strip("\n")) #Wipe*3
                Gcode_Storage.append(Process_GCode_Offset("G1 X25 Y25", para.Wiper_x-5, para.Wiper_y-5, CurrMax_Tower_Height+3,'normal').strip("\n")) #Wipe*4
            Gcode_Storage.append(Process_GCode_Offset(Variable_Wipe_Code, para.Wiper_x-5, para.Wiper_y-5, CurrMax_Tower_Height+3,'normal').strip("\n")) #Wipe*5
            Gcode_Storage.append(Process_GCode_Offset("G1 X25 Y25", para.Wiper_x-5, para.Wiper_y-5, CurrMax_Tower_Height+3,'normal').strip("\n")) #Wipe*6
            Gcode_Storage.append(Process_GCode_Offset(Variable_Wipe_Code, para.Wiper_x-5, para.Wiper_y-5, CurrMax_Tower_Height+3,'normal').strip("\n")) #Wipe*7
            Gcode_Storage.append(Process_GCode_Offset("G1 X15 Y15", para.Wiper_x-5, para.Wiper_y-5, CurrMax_Tower_Height+3,'normal').strip("\n")) #Wipe*8
            Gcode_Storage.append(Process_GCode_Offset("G1 X20"+" Y1"+get_pseudo_random(), para.Wiper_x-5, para.Wiper_y-5, Current_Layer_Height+3,'normal').strip("\n"))
        

        if CurrGCommand.find("Lift-z") != -1:
            #从CurrGCommand中提取z轴高度，格式是;Lift-z:0.5
            Lift_z=Num_Strip(CurrGCommand)[0]
            #与接下来要调整的Z高度比较，如果小于擦嘴塔round(CurrMax_Tower_Height+2, 3)则输出提升指令，否则不输出
            if round(CurrMax_Tower_Height+2, 3)>Lift_z:
                Gcode_Storage.append("G1 Z"+ str(round(CurrMax_Tower_Height+2, 3))+";Compensation") #Avoid collision
        
        if CurrGCommand.find(";Prepare for next tower") != -1 and para.Use_Wiping_Towers.get()==True:
            Gcode_Storage.append("G1 Z"+ str(round(CurrMax_Tower_Height, 3))) #Avoid collision
            # print(Process_GCode_Offset("G1 X25 Y25", para.Wiper_x-5, para.Wiper_y-5, Current_Layer_Height+3,'normal').strip("\n"), file=GcodeExporter)
            # print("G1 Z"+ str(round(LastMax_Tower_Height, 3)), file=GcodeExporter) #adjust z
            Variable_Wipe_Code="G1 X15 Y2"+get_pseudo_random()
            if para.Filament_Type=="PLA":
                Gcode_Storage.append(Process_GCode_Offset(Variable_Wipe_Code, para.Wiper_x-5, para.Wiper_y-5, CurrMax_Tower_Height+3,'normal').strip("\n")) #Wipe*1
                Gcode_Storage.append(Process_GCode_Offset("G1 X25 Y25", para.Wiper_x-5, para.Wiper_y-5, CurrMax_Tower_Height+3,'normal').strip("\n")) #Wipe*2
                Gcode_Storage.append(Process_GCode_Offset(Variable_Wipe_Code, para.Wiper_x-5, para.Wiper_y-5, CurrMax_Tower_Height+3,'normal').strip("\n")) #Wipe*3
                Gcode_Storage.append(Process_GCode_Offset("G1 X25 Y25", para.Wiper_x-5, para.Wiper_y-5, CurrMax_Tower_Height+3,'normal').strip("\n")) #Wipe*4
            Gcode_Storage.append(Process_GCode_Offset(Variable_Wipe_Code, para.Wiper_x-5, para.Wiper_y-5, CurrMax_Tower_Height+3,'normal').strip("\n")) #Wipe*5
            Gcode_Storage.append(Process_GCode_Offset("G1 X25 Y25", para.Wiper_x-5, para.Wiper_y-5, CurrMax_Tower_Height+3,'normal').strip("\n")) #Wipe*6
            Gcode_Storage.append(Process_GCode_Offset(Variable_Wipe_Code, para.Wiper_x-5, para.Wiper_y-5, CurrMax_Tower_Height+3,'normal').strip("\n")) #Wipe*7
            Gcode_Storage.append(Process_GCode_Offset("G1 X15 Y15", para.Wiper_x-5, para.Wiper_y-5, CurrMax_Tower_Height+3,'normal').strip("\n")) #Wipe*8
            Gcode_Storage.append(Process_GCode_Offset("G1 X20"+" Y1"+get_pseudo_random(), para.Wiper_x-5, para.Wiper_y-5, Current_Layer_Height+3,'normal').strip("\n"))
        if CurrGCommand.find(";Adjust cooling distance") != -1:
            Gcode_Storage.append("G1 Z"+ str(round(CurrMax_Tower_Height+2, 3)))

    #现在把Gcode_Storage中的Gcode写入文件
    for i in Gcode_Storage:
        print(i, file=GcodeExporter)        
    GcodeExporter.close()
    #输出偏移校准测试
    #倒序查找;Precise Calibration或者;Rough Calibration或者;ZOffset Calibration
    Mode=""
    def show_info_dialog(title, message):
        """自定义信息弹窗"""
        # 创建弹窗
        dialog = ctk.CTkToplevel()
        dialog.title(title)  # 设置标题
        dialog.after(201, lambda :dialog.iconbitmap(mkpicon_path))  # 解决某些系统图标不显示的问题
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
        def select_xy_calibration_range(parent_dialog):
            parent_dialog.withdraw()
            """
            XY校准前的范围选择对话框。
            
            参数:
                parent_dialog: 父窗口
                
            返回:
                (selected_x_values_list, selected_y_values_list, user_confirmed)
                - selected_x_values_list: 选中的X轴偏移值列表
                - selected_y_values_list: 选中的Y轴偏移值列表
                - user_confirmed: True=用户点击确定，False=超时/取消
            """
            popup = ctk.CTkToplevel(parent_dialog)
            popup.title("选择校准范围" if lang_setting != "EN" else "Select Calibration Range")
            popup.after(201, lambda: popup.iconbitmap(mkpicon_path))
            popup.geometry(CenterWindowToDisplay(popup, 720, 600, popup._get_window_scaling()))
            popup.maxsize(720, 600)
            popup.minsize(720, 600)
            popup.configure(fg_color='#1a1a1a')
            popup.attributes('-alpha', 0.93)
            popup.attributes('-topmost', True)
            
            # 主框架
            main_frame = ctk.CTkFrame(popup, fg_color='#1a1a1a')
            main_frame.pack(fill="both", expand=True, pady=10)
            
            # 标题
            title_label = ctk.CTkLabel(
                main_frame,
                text="默认为全偏移值测试（打印+涂胶）。如需细调（仅涂胶），请框选需要测试的校准线。\n\n6秒后如不选择，则执行全偏移值测试。" if lang_setting != "EN" 
                else "Default: full offset test (printing + gluing). For fine-tuning (gluing only), please select the blocks to test.\n\nIf no selection is made within 6 seconds, full offset test will be executed.",
                font=("SimHei", 13, "bold"),
                text_color='#ffffff',
                justify="center"
            )
            title_label.pack(pady=10)
            
            # 创建画布框架
            canvas_frame = ctk.CTkFrame(main_frame, fg_color='#1a1a1a', width=720, height=450)
            canvas_frame.pack()
            canvas_frame.pack_propagate(False)
            
            import tkinter as tk_canvas
            from PIL import Image, ImageDraw, ImageFilter, ImageTk
            import numpy as np
            
            canvas = tk_canvas.Canvas(
                canvas_frame,
                width=720,
                height=450,
                bg='#1a1a1a',
                highlightthickness=0,
                bd=0
            )
            canvas.pack()
            
            # 定义原点坐标（左下角）
            origin_x = 120
            origin_y = 450
            
            # 定义参数
            num_lines = 11
            line_spacing = 40
            line_length_normal = 40
            line_length_center = 55
            
            # 存储X轴和Y轴的线
            x_lines = []
            y_lines = []
            
            # 绘制X轴主轴线 - 从原点向右
            canvas.create_line(
                origin_x, origin_y,
                origin_x + (num_lines-1) * line_spacing + 41, origin_y,
                fill='#00ff00',
                width=2
            )
            
            # 绘制Y轴主轴线 - 从原点向上
            canvas.create_line(
                origin_x, origin_y,
                origin_x, origin_y - (num_lines-1) * line_spacing - 41,
                fill='#00ff00',
                width=2
            )
            
            # 绘制X轴方向的线 - 从X轴向上生长
            for i in range(num_lines):
                x_pos = origin_x + 39 + i * line_spacing
                value = -1.0 + i * 0.2
                
                if i == 5:
                    line_length = line_length_center
                    line_color = '#ffffff'
                else:
                    line_length = line_length_normal
                    line_color = '#ffffff'
                
                line_id = canvas.create_line(
                    x_pos, origin_y,
                    x_pos, origin_y - line_length,
                    fill=line_color,
                    width=4,
                    tags=f"x_line_{i}"
                )
                
                text_id = canvas.create_text(
                    x_pos, origin_y - line_length - 12,
                    text="" if abs(value + 1.0) < 0.001 else f"{value:.1f}", 
                    fill='#cccccc',
                    font=("SimHei", 12),
                    tags=f"x_text_{i}"
                )
                
                x_lines.append({
                    'id': line_id,
                    'text_id': text_id,
                    'value': value,
                    'x': x_pos,
                    'y_top': origin_y - line_length,
                    'y_bottom': origin_y,
                    'index': i,
                    'axis': 'x',
                    'selected': False
                })
                
                # 点击区域
                click_padding = 20
                click_id = canvas.create_rectangle(
                    x_pos - click_padding, origin_y - line_length - click_padding,
                    x_pos + click_padding, origin_y + click_padding,
                    outline='',
                    fill='',
                    tags=f"x_click_{i}"
                )
                
                def make_x_click_handler(idx):
                    return lambda event: on_line_click(idx, 'x', event)
                
                canvas.tag_bind(f"x_click_{i}", '<Button-1>', make_x_click_handler(i))
            
            # 绘制Y轴方向的线 - 从Y轴向右生长
            for i in range(num_lines):
                y_pos = origin_y - 39 - i * line_spacing
                value = -1.0 + i * 0.2
                
                if i == 5:
                    line_length = line_length_center
                    line_color = '#ffffff'
                else:
                    line_length = line_length_normal
                    line_color = '#ffffff'
                
                line_id = canvas.create_line(
                    origin_x, y_pos,
                    origin_x + line_length, y_pos,
                    fill=line_color,
                    width=4,
                    tags=f"y_line_{i}"
                )
                
                text_id = canvas.create_text(
                    origin_x + line_length + 24, y_pos,
                    text="" if abs(value + 1.0) < 0.001 else f"{value:.1f}", 
                    fill='#cccccc',
                    font=("SimHei", 12),
                    tags=f"y_text_{i}"
                )
                
                y_lines.append({
                    'id': line_id,
                    'text_id': text_id,
                    'value': value,
                    'y': y_pos,
                    'x_left': origin_x,
                    'x_right': origin_x + line_length,
                    'index': i,
                    'axis': 'y',
                    'selected': False
                })
                
                click_padding = 10
                click_id = canvas.create_rectangle(
                    origin_x - click_padding, y_pos - click_padding,
                    origin_x + line_length + click_padding, y_pos + click_padding,
                    outline='',
                    fill='',
                    tags=f"y_click_{i}"
                )
                
                def make_y_click_handler(idx):
                    return lambda event: on_line_click(idx, 'y', event)
                
                canvas.tag_bind(f"y_click_{i}", '<Button-1>', make_y_click_handler(i))
            
            # 超时计时器
            timeout_id = [None]
            
            def reset_timeout():
                if timeout_id[0] is not None:
                    canvas.after_cancel(timeout_id[0])
                timeout_id[0] = canvas.after(6000, on_timeout)
            def kill_timeout():
                if timeout_id[0] is not None:
                    canvas.after_cancel(timeout_id[0])
                timeout_id[0] = canvas.after(30000, on_timeout)
            def on_timeout():
                if popup.winfo_exists():
                    confirm_result[0] = False
                    popup.destroy()
                    # parent_dialog.deiconify()
            
            # 框选支持
            select_rect = None
            select_start_x = select_start_y = 0
            is_dragging = False
            
            def on_mouse_down(event):
                nonlocal select_rect, select_start_x, select_start_y, is_dragging
                reset_timeout()
                
                # 检查是否点击在线条上
                x, y = canvas.canvasx(event.x), canvas.canvasy(event.y)
                for line in x_lines + y_lines:
                    if line['axis'] == 'x':
                        if abs(x - line['x']) <= 25 and line['y_top'] - 15 <= y <= line['y_bottom'] + 15:
                            return
                    else:
                        if abs(y - line['y']) <= 15 and line['x_left'] - 15 <= x <= line['x_right'] + 25:
                            return
                
                is_dragging = True
                select_start_x = x
                select_start_y = y
                if select_rect:
                    canvas.delete(select_rect)
                select_rect = canvas.create_rectangle(
                    select_start_x, select_start_y, select_start_x, select_start_y,
                    outline='#ff0000', width=2, dash=(4, 2), fill=''
                )
            
            def on_mouse_move(event):
                if is_dragging and select_rect:
                    cur_x = canvas.canvasx(event.x)
                    cur_y = canvas.canvasy(event.y)
                    canvas.coords(select_rect, select_start_x, select_start_y, cur_x, cur_y)
            
            def on_mouse_up(event):
                nonlocal select_rect, is_dragging
                if is_dragging and select_rect:
                    end_x = canvas.canvasx(event.x)
                    end_y = canvas.canvasy(event.y)
                    x1, y1, x2, y2 = select_start_x, select_start_y, end_x, end_y
                    if x1 > x2: x1, x2 = x2, x1
                    if y1 > y2: y1, y2 = y2, y1
                    
                    # 框选X轴线条
                    for line in x_lines:
                        # 线条的位置：x坐标固定，y范围从y_top到y_bottom
                        line_x = line['x']
                        line_y_center = (line['y_top'] + line['y_bottom']) / 2
                        
                        if (x1 <= line_x <= x2 and y1 <= line_y_center <= y2):
                            if not line['selected']:
                                line['selected'] = True
                                canvas.itemconfig(line['id'], fill='#ff4444')
                                start_breathing(line['index'], 'x')
                    
                    # 框选Y轴线条
                    for line in y_lines:
                        # 线条的位置：y坐标固定，x范围从x_left到x_right
                        line_y = line['y']
                        line_x_center = (line['x_left'] + line['x_right']) / 2
                        
                        if (x1 <= line_x_center <= x2 and y1 <= line_y <= y2):
                            if not line['selected']:
                                line['selected'] = True
                                canvas.itemconfig(line['id'], fill='#ff4444')
                                start_breathing(line['index'], 'y')
                    
                    canvas.delete(select_rect)
                    select_rect = None
                    is_dragging = False
                    
                    # update_selection_display()
            canvas.bind('<Button-1>', on_mouse_down)
            canvas.bind('<B1-Motion>', on_mouse_move)
            canvas.bind('<ButtonRelease-1>', on_mouse_up)
            # 呼吸效果管理
            breathing_animations = {}
            breathing_photos = {}
            
            def start_breathing(idx, axis):
                key = f"{axis}_{idx}"
                if key in breathing_animations:
                    stop_breathing(idx, axis)
                
                lines = x_lines if axis == 'x' else y_lines
                line = lines[idx]
                if not line['selected']:
                    return
                
                step = [0]
                direction = [1]
                
                def update_breath():
                    if not line['selected']:
                        return
                    step[0] += direction[0] * 0.5
                    if step[0] > 0:
                        direction[0] = -1
                    elif step[0] < -2:
                        direction[0] = 1
                    
                    padding = 8 + step[0]
                    opacity = 200
                    
                    glow_img = Image.new("RGBA", (720, 450), (0, 0, 0, 0))
                    draw = ImageDraw.Draw(glow_img)
                    
                    if axis == 'x':
                        x, y_top, y_bottom = line['x'], line['y_top'], line['y_bottom']
                        draw.rectangle(
                            [x-padding, y_top-padding, x+padding, y_bottom+padding],
                            fill=(255, 30, 30, opacity)
                        )
                    else:
                        x_left, x_right, y = line['x_left'], line['x_right'], line['y']
                        draw.rectangle(
                            [x_left-padding, y-padding, x_right+padding, y+padding],
                            fill=(255, 30, 30, opacity)
                        )
                    
                    glow_img = glow_img.filter(ImageFilter.GaussianBlur(8))
                    glow_array = np.array(glow_img).astype(np.float32) / 255.0
                    glow_array[..., :3] *= 1.5
                    glow_array = np.clip(glow_array, 0, 1)
                    glow_img = Image.fromarray((glow_array * 255).astype(np.uint8), "RGBA")
                    glow_photo = ImageTk.PhotoImage(glow_img)
                    
                    breathing_photos[key] = glow_photo
                    
                    if hasattr(canvas, f'glow_{key}'):
                        canvas.delete(getattr(canvas, f'glow_{key}'))
                    glow_item = canvas.create_image(0, 0, anchor='nw', image=glow_photo)
                    canvas.tag_lower(glow_item)
                    setattr(canvas, f'glow_{key}', glow_item)
                    
                    breathing_animations[key] = canvas.after(400, update_breath)
                
                update_breath()
            
            def stop_breathing(idx, axis):
                key = f"{axis}_{idx}"
                if key in breathing_animations:
                    canvas.after_cancel(breathing_animations[key])
                    del breathing_animations[key]
                if key in breathing_photos:
                    del breathing_photos[key]
                if hasattr(canvas, f'glow_{key}'):
                    canvas.delete(getattr(canvas, f'glow_{key}'))
                    delattr(canvas, f'glow_{key}')
            
            

            # 单选逻辑（Ctrl+点击切换）
            def on_line_click(idx, axis, event):
                kill_timeout()
                lines = x_lines if axis == 'x' else y_lines
                line = lines[idx]
                
                if event.state & 0x0004:  # Ctrl键
                    if line['selected']:
                        line['selected'] = False
                        canvas.itemconfig(line['id'], fill='#ffffff')
                        stop_breathing(idx, axis)
                    else:
                        line['selected'] = True
                        canvas.itemconfig(line['id'], fill='#ff4444')
                        start_breathing(idx, axis)
                else:
                    # 无修饰键：清空同轴其他，只选中当前
                    for l in lines:
                        if l['index'] == idx:
                            if not l['selected']:
                                l['selected'] = True
                                canvas.itemconfig(l['id'], fill='#ff4444')
                                start_breathing(idx, axis)
                        else:
                            if l['selected']:
                                l['selected'] = False
                                canvas.itemconfig(l['id'], fill='#ffffff')
                                stop_breathing(l['index'], axis)
            
            # 按钮框架
            button_frame = ctk.CTkFrame(main_frame, fg_color='#1a1a1a',height=50)
            button_frame.pack(pady=10)
            
            confirm_result = [False]
            selected_x_values = []
            selected_y_values = []
            
            def confirm_selection():
                nonlocal selected_x_values, selected_y_values
                selected_x_values = [l['value'] for l in x_lines if l['selected']]
                selected_y_values = [l['value'] for l in y_lines if l['selected']]
                confirm_result[0] = True
                popup.destroy()
                # parent_dialog.deiconify()
            
            def cancel_selection():
                confirm_result[0] = False
                popup.destroy()
                # parent_dialog.deiconify()
            
            confirm_button = ctk.CTkButton(
                button_frame,
                text="确定" if lang_setting != "EN" else "Confirm",
                command=confirm_selection,
                font=("SimHei", 14),
                width=100,
                fg_color='#aa0000',
                hover_color='#ff4444'
            )
            confirm_button.pack(side="left", padx=10)
            
            
            # 启动超时
            reset_timeout()
            
            popup.wait_window()
            return selected_x_values, selected_y_values, confirm_result[0]
        #和Z轴校准测试的调用差不多
        selected_x_list, selected_y_list, confirmed = select_xy_calibration_range(window)
        need_to_remove_printing_flag_xy=False
        if selected_x_list!=[] or selected_y_list!=[]:
            need_to_remove_printing_flag_xy=True
        #现在把偏移值转换成0-10的编号，参考selected_indices = [int((0.5 - val) / 0.1) for val in selected_values]
        selected_x_indices = [int((1.0 + val) / 0.2) for val in selected_x_list]
        selected_y_indices = [int((1.0 + val) / 0.2) for val in selected_y_list]
        selected_x_list=selected_x_indices[:]
        selected_y_list=selected_y_indices[:]
        
        # para.is_first_Z_Calibration_Flag=False
        # show_info_dialog(
        #     title="提示",
        #     message="正在输出XY偏移校准测试"+"\n"+"测试过程中如需中止请取消打印，请勿暂停"
        # )
        #现在设计一个对话框
        with open(GSourceFile, 'r', encoding='utf-8') as file:
            calibe = file.readlines()
        warnfool_flag=False
        for i in range(len(calibe)):
            if calibe[i].find("; Z_HEIGHT: 1") != -1:
                warnfool_flag=True
                CTkMessagebox(title='提示', message="笨蛋! 你在用Calibaration的3MF打印别的东西, 对不对?", icon="info")
                # tk.messagebox.showinfo(title='提示', message="笨蛋! 你在用Calibaration的3MF打印别的东西, 对不对?")
                # tk.messagebox.showinfo(title='提示', message="下次再犯我就会炸毛的")
                break
        # if warnfool_flag==False:
        #     tk.messagebox.showinfo(title='提示', message="正在输出XY偏移校准测试"+"\n\n"+"测试过程中如需中止请取消打印，请勿暂停")
        # os.remove(Output_Filename)
        CaliGcodeExporter = open(Output_Filename, "w", encoding="utf-8")
        MachineType = ""
        MachineType_Extra=""
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
            if calibe[i].find(";======== P2S start gcode==========") != -1:
                MachineType = "P1/P1S"
                MachineType_Extra="P2S"
                break
        
        if need_to_remove_printing_flag_xy==True:
            if MachineType_Extra=="":
            # if MachineType_Extra=="":
                #查找“;===== home after wipe mouth end”出现在哪一行，其后所有指令都去掉
                for i in range(len(calibe)):
                    if calibe[i].find(";===== home after wipe mouth end") != -1 and calibe[i].find("; machine_start_gcode =") == -1:
                        calibe[i:]=[]
                        break
                calibe.append("; MACHINE_START_GCODE_END")
                calibe.append("; filament start gcode")
                calibe.append("; FEATURE: Outer wall")
                calibe.append("; Z_HEIGHT: 0.2")
                calibe.append("; LAYER_HEIGHT: 0.2")
                calibe.append("; LINE_WIDTH: 0.5")
                calibe.append("; filament end gcode")
            else:
                #查找“;===== bed leveling end”出现在哪一行，其后所有指令都去掉
                for i in range(len(calibe)):
                    if calibe[i].find(";===== bed leveling end") != -1 and calibe[i].find("; machine_start_gcode =") == -1:
                        calibe[i:]=[]
                        break
                calibe.append("; filament end gcode")
            # for i in range(len(calibe)):
            #     if calibe[i].find("M622 J1")!=-1 and calibe[i].find("=")==-1:
            #         #从这里开始，往下找，直到找到"M623",中间的所有指令变成“”
            #         j=i+1
            #         while calibe[j].find("M623")==-1:
            #             j+=1
            #         calibe[i:j+1]=[""] * (j - i + 1)

        #输出文件
        for i in range(len(calibe)):
            print(calibe[i].strip("\n"), file=CaliGcodeExporter)
            if calibe[i].find("; filament end gcode") != -1 and calibe[i].find("=") == -1 and Mode!="ZOffset":
                calibe[i]=";Start XY Offset Calibration Test\n"
                #输出偏移校准
                #挂载胶箱
                print("G1 X100 Y100 Z10 F3000", file=CaliGcodeExporter)
                print(";Rising nozzle to avoid collision", file=CaliGcodeExporter)
                print("G1 Z" + str(round(para.First_Layer_Height+para.Z_Offset+6, 3)), file=CaliGcodeExporter)
                print(";Mounting Toolhead", file=CaliGcodeExporter)
                # print(para.Custom_Mount_Gcode.strip("\n"), file=CaliGcodeExporter)
                if need_to_remove_printing_flag_xy==False:
                    print(para.Custom_Mount_Gcode.strip("\n"), file=CaliGcodeExporter)
                else:
                    for line in para.Custom_Mount_Gcode.splitlines():
                        if line.find("G1 E")==-1:
                            print(line.strip("\n"), file=CaliGcodeExporter)
                        

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
                #提示哪些线会被用到，也就是selected_x_list和selected_y_list的值,请认真看这个Messagebox的语法实现！
                # MKPMessagebox.show_info(title="Selected Calibration Ranges", message="Selected X Offsets: " + ", ".join([f"{x:.1f}" for x in selected_x_list]) + "\nSelected Y Offsets: " + ", ".join([f"{y:.1f}" for y in selected_y_list]))
                # MKPMessagebox.show_info("Selected X Offsets: " + ", ".join([f"{x:.1f}" for x in selected_x_list]) + "\nSelected Y Offsets: " + ", ".join([f"{y:.1f}" for y in selected_y_list])
                #Y校准运行次数
                Y_Line=11
                X_GCommand=[]
                Y_GCommand=[]
                #运行十次：
                for i in range(Y_Line):
                    #空驶到指定位置的调速F
                    # print("G1 F" + str(para.Travel_Speed*60), file=CaliGcodeExporter)
                    X_GCommand.append("G1 F" + str(para.Travel_Speed*60))
                    #G1 X到指定位,Y渐增
                    OriginCaliLine="G1 X" + str(round(Y_Cali_Line_DefaultX, 3)) + " Y" + str(round(Y_Cali_Line_DefaultY+Offset_Accumulate, 3))#指定原值
                    # print(Process_GCode_Offset(OriginCaliLine, para.X_Offset, para.Y_Offset+Cali_Accumulate,para.Z_Offset,'normal').strip("\n"), file=CaliGcodeExporter)#进行偏移
                    X_GCommand.append(Process_GCode_Offset(OriginCaliLine, para.X_Offset, para.Y_Offset+Cali_Accumulate,para.Z_Offset,'normal').strip("\n"))
                    # print("G1 Z" + str(round(para.First_Layer_Height+para.Z_Offset+3, 3)), file=CaliGcodeExporter)#Adjust Z
                    X_GCommand.append("G1 Z" + str(round(para.First_Layer_Height+para.Z_Offset+3, 3)))
                    #开始校准的调速F
                    if para.Max_Speed>10:
                        # print("G1 F300", file=CaliGcodeExporter)
                        X_GCommand.append("G1 F300")
                    else:
                        # print("G1 F" + str(para.Max_Speed), file=CaliGcodeExporter)
                        X_GCommand.append("G1 F" + str(para.Max_Speed))
                    #G1 X渐增
                    OriginCaliLine="G1 X" + str(round(Y_Cali_Line_DefaultX_End, 3)) + " Y" + str(round(Y_Cali_Line_DefaultY+Offset_Accumulate, 3))+" Z"+ str(round(para.First_Layer_Height+para.Z_Offset, 3))
                    # print(Process_GCode_Offset(OriginCaliLine, para.X_Offset, para.Y_Offset+Cali_Accumulate,0,'normal').strip("\n"), file=CaliGcodeExporter)#进行偏移
                    X_GCommand.append(Process_GCode_Offset(OriginCaliLine, para.X_Offset, para.Y_Offset+Cali_Accumulate,0,'normal').strip("\n"))
                    Offset_Accumulate+=4
                    if Mode=="Precise":
                        Cali_Accumulate+=0.2
                    elif Mode=="Rough":
                        Cali_Accumulate+=0.5
                    #抬升Z
                    # print("G1 Z" + str(round(para.First_Layer_Height+para.Z_Offset+3, 3)), file=CaliGcodeExporter)
                    X_GCommand.append("G1 Z" + str(round(para.First_Layer_Height+para.Z_Offset+3, 3)))
                    # if need_to_remove_printing_flag==True:
                    #     if i not in selected_indices:   
                    #         ZOffset_Temp_GCommand.clear()
                    # if ZOffset_Temp_GCommand!=[]:
                    #     for k in range(len(ZOffset_Temp_GCommand)):
                    #         print(ZOffset_Temp_GCommand[k], file=CaliGcodeExporter)
                    #     ZOffset_Temp_GCommand.clear()
                    if need_to_remove_printing_flag_xy==True:
                        if i not in selected_x_list:   
                            X_GCommand.clear()
                    if X_GCommand!=[]:
                        for k in range(len(X_GCommand)):
                            print(X_GCommand[k], file=CaliGcodeExporter)
                        X_GCommand.clear()
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
                    # print("G1 F" + str(para.Travel_Speed*60), file=CaliGcodeExporter)
                    Y_GCommand.append("G1 F" + str(para.Travel_Speed*60))
                    #空驶到指定位置
                    #G1 Y到指定位,X渐增
                    OriginCaliLine="G1 X" + str(round(X_Cali_Line_DefaultX+Offset_Accumulate, 3)) + " Y" + str(round(X_Cali_Line_DefaultY, 3))#指定原值
                    # print(Process_GCode_Offset(OriginCaliLine, para.X_Offset+Cali_Accumulate, para.Y_Offset,para.Z_Offset,'normal').strip("\n"), file=CaliGcodeExporter)#进行偏移
                    Y_GCommand.append(Process_GCode_Offset(OriginCaliLine, para.X_Offset+Cali_Accumulate, para.Y_Offset,para.Z_Offset,'normal').strip("\n"))
                    # print("G1 Z" + str(round(para.First_Layer_Height+para.Z_Offset+3, 3)), file=CaliGcodeExporter)#Adjust Z
                    Y_GCommand.append("G1 Z" + str(round(para.First_Layer_Height+para.Z_Offset+3, 3)))
                    #开始校准的调速F
                    if para.Max_Speed>10:
                        # print("G1 F300", file=CaliGcodeExporter)
                        Y_GCommand.append("G1 F300")
                    else:
                        # print("G1 F" + str(para.Max_Speed), file=CaliGcodeExporter)
                        Y_GCommand.append("G1 F" + str(para.Max_Speed))
                    #G1 X渐增
                    OriginCaliLine="G1 X" + str(round(X_Cali_Line_DefaultX+Offset_Accumulate, 3)) + " Y" + str(round(X_Cali_Line_DefaultY_End, 3))+" Z"+ str(round(para.First_Layer_Height+para.Z_Offset, 3))
                    # print(Process_GCode_Offset(OriginCaliLine, para.X_Offset+Cali_Accumulate, para.Y_Offset,0,'normal').strip("\n"), file=CaliGcodeExporter)#进行偏移
                    Y_GCommand.append(Process_GCode_Offset(OriginCaliLine, para.X_Offset+Cali_Accumulate, para.Y_Offset,0,'normal').strip("\n"))
                    Offset_Accumulate+=4
                    if Mode=="Precise":
                        Cali_Accumulate+=0.2
                    elif Mode=="Rough":
                        Cali_Accumulate+=0.5
                    #抬升Z 
                    # print("G1 Z" + str(round(para.First_Layer_Height+para.Z_Offset+3, 3)), file=CaliGcodeExporter)
                    Y_GCommand.append("G1 Z" + str(round(para.First_Layer_Height+para.Z_Offset+3, 3)))
                    if need_to_remove_printing_flag_xy==True:
                        if i not in selected_y_list:   
                            Y_GCommand.clear()
                    if Y_GCommand!=[]:
                        for k in range(len(Y_GCommand)):
                            print(Y_GCommand[k], file=CaliGcodeExporter)
                        Y_GCommand.clear()

                #卸载胶箱
                print(";Unmounting Toolhead", file=CaliGcodeExporter)
                # print(para.Custom_Unmount_Gcode.strip("\n"), file=CaliGcodeExporter)
                if need_to_remove_printing_flag_xy==False:
                    print(para.Custom_Unmount_Gcode.strip("\n"), file=CaliGcodeExporter)
                else:
                    for line in para.Custom_Unmount_Gcode.splitlines():
                        if line.find("G1 E")==-1:
                            print(line.strip("\n"), file=CaliGcodeExporter)
                print(";Toolhead Unmounted", file=CaliGcodeExporter)

                print("G1 X100 Y100 Z100 E0.1", file=CaliGcodeExporter)#空驶

                if MachineType=="A1mini" or MachineType=="A1":
                    print(Calibe_Sing, file=CaliGcodeExporter)#唱歌

                #补全结束
                print(calibe[i].strip("\n"), file=CaliGcodeExporter)
        if need_to_remove_printing_flag_xy==True:
            print("; EXECUTABLE_BLOCK_END", file=CaliGcodeExporter)
        CaliGcodeExporter.close()
    elif Mode=="ZOffset":
        # show_info_dialog(
        #     title="提示",
        #     message="正在输出Z偏移校准测试"+"\n"+"测试过程中如需中止请取消打印，请勿暂停"
        # )
        def select_calibration_range(parent_dialog):
            """
            校准前的范围选择对话框。
            
            参数:
                parent_dialog: 父窗口
                
            返回:
                (selected_values_list, user_confirmed)
                - selected_values_list: 选中方块对应的value列表
                - user_confirmed: True=用户点击确定，False=超时/取消/未选择
            """
            popup = ctk.CTkToplevel(parent_dialog)
            popup.after(201, lambda: popup.iconbitmap(mkpicon_path))
            popup.title("选择校准范围" if lang_setting != "EN" else "Select Calibration Range")
            # popup.geometry("720x450")
            popup.geometry(CenterWindowToDisplay(popup, 720, 450, popup._get_window_scaling()))
            popup.maxsize(720, 450)
            popup.minsize(720, 450)
            popup.configure(fg_color='#1a1a1a')
            popup.attributes('-alpha', 0.9)
            popup.attributes('-topmost', True)
            
            # 主框架
            main_frame = ctk.CTkFrame(popup, fg_color='#1a1a1a')
            main_frame.pack(fill="both", expand=True, padx=20, pady=50)
            
            # 标题
            title_label = ctk.CTkLabel(
                main_frame,
                text="默认为全偏移值测试(打印+涂胶)。如需细调(仅涂胶)，请框选需要测试的方块。\n\n6秒后如不选择，则执行全偏移值测试" if lang_setting != "EN" 
                else "Default: Full offset test (printing + gluing). For fine adjustment (gluing only), please select the squares to test.\nIf no selection is made within 6 seconds, the full offset test will be executed.",
                font=("SimHei", 14, "bold"),
                text_color='#ffffff'
            )
            title_label.pack(pady=(0, 30))
            
            # 创建画布框架
            canvas_frame = ctk.CTkFrame(main_frame, fg_color='#1a1a1a', width=720, height=230)
            canvas_frame.pack()
            canvas_frame.pack_propagate(False)
            
            import tkinter as tk_canvas
            from PIL import Image, ImageDraw, ImageFilter, ImageTk
            import numpy as np
            
            canvas = tk_canvas.Canvas(
                canvas_frame,
                width=720,
                height=230,
                bg='#1a1a1a',
                highlightthickness=0,
                bd=0
            )
            canvas.pack()
            
            # 计算方块参数
            num_blocks = 11
            block_size = 44
            spacing = 22
            total_width = num_blocks * (block_size + spacing) - spacing
            start_x = (720 - total_width) // 2
            y_position = 70
            
            blocks = []
            
            # 绘制长条
            long_bar_y = y_position + block_size
            long_bar_start_x = start_x 
            long_bar_end_x = start_x + num_blocks * (block_size + spacing) - spacing 
            canvas.create_rectangle(
                long_bar_start_x, long_bar_y,
                long_bar_end_x, long_bar_y + 12,
                fill='#ffffff',
                outline='#f0f0f0',
                width=1
            )
            
            # 绘制方块和刻度
            for i in range(num_blocks):
                x1 = start_x + i * (block_size + spacing)
                y1 = y_position
                x2 = x1 + block_size
                y2 = y1 + block_size
                value = 0.5 + i * (-0.1)
                
                block_id = canvas.create_rectangle(
                    x1, y1, x2, y2,
                    outline='',
                    width=0,
                    fill='#ffffff',
                    tags=f"block_{i}"
                )
                
                text_id = canvas.create_text(
                    x1 + block_size//2,
                    y1 + block_size//2,
                    text="",
                    fill='#333333',
                    font=("SimHei", 11, "bold")
                )
                
                blocks.append({
                    'id': block_id,
                    'text_id': text_id,
                    'value': value,
                    'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
                    'index': i,
                    'selected': False
                })
                
                # 点击区域
                click_padding = 10
                click_id = canvas.create_rectangle(
                    x1 - click_padding, y1 - click_padding,
                    x2 + click_padding, y2 + click_padding,
                    outline='',
                    fill='',
                    tags=f"click_{i}"
                )
                
                # 绑定点击事件
                def make_click_handler(idx):
                    return lambda event: on_single_click(idx, event)
                canvas.tag_bind(f"click_{i}", '<Button-1>', make_click_handler(i))
                
                # 悬停效果
                def make_enter_handler(idx):
                    return lambda event: on_hover_enter(idx)
                def make_leave_handler(idx):
                    return lambda event: on_hover_leave(idx)
                canvas.tag_bind(f"click_{i}", '<Enter>', make_enter_handler(i))
                canvas.tag_bind(f"click_{i}", '<Leave>', make_leave_handler(i))
                
                # 刻度线
                tick_x = x1 + block_size // 2
                tick_y = y1 - 8
                canvas.create_line(
                    tick_x, tick_y - 5,
                    tick_x, tick_y,
                    fill='#888888',
                    width=2
                )
                canvas.create_text(
                    tick_x, tick_y - 15,
                    text=f"{value:.1f}",
                    fill='#cccccc',
                    font=("SimHei", 12)
                )
            
            # 超时计时器相关
            timeout_id = [None]
            
            def reset_timeout():
                """重置超时计时器"""
                if timeout_id[0] is not None:
                    canvas.after_cancel(timeout_id[0])
                timeout_id[0] = canvas.after(6000, on_timeout)
            
            def kill_timeout():
                """重置超时计时器"""
                if timeout_id[0] is not None:
                    canvas.after_cancel(timeout_id[0])
                timeout_id[0] = canvas.after(30000, on_timeout)
            
            def on_timeout():
                """超时关闭"""
                if popup.winfo_exists():
                    confirm_result[0] = False
                    popup.destroy()
                    # parent_dialog.deiconify()
            
            # 框选多选支持（不需要按Shift）
            select_rect = None
            select_start_x = select_start_y = 0
            is_dragging = False
            
            def on_mouse_down(event):
                nonlocal select_rect, select_start_x, select_start_y, is_dragging
                # 重置超时
                kill_timeout()
                # 检查是否点击在方块点击区域上，如果是则不启动框选
                x, y = canvas.canvasx(event.x), canvas.canvasy(event.y)
                for blk in blocks:
                    if (blk['x1'] - 10 <= x <= blk['x2'] + 10 and
                        blk['y1'] - 10 <= y <= blk['y2'] + 10):
                        return  # 点击在方块上，不启动框选
                
                # 启动框选
                is_dragging = True
                select_start_x = x
                select_start_y = y
                if select_rect:
                    canvas.delete(select_rect)
                select_rect = canvas.create_rectangle(
                    select_start_x, select_start_y, select_start_x, select_start_y,
                    outline='#ff0000', width=2, dash=(4, 2), fill=''
                )
            
            def on_mouse_move(event):
                if is_dragging and select_rect:
                    cur_x = canvas.canvasx(event.x)
                    cur_y = canvas.canvasy(event.y)
                    canvas.coords(select_rect, select_start_x, select_start_y, cur_x, cur_y)
            
            def on_mouse_up(event):
                nonlocal select_rect, is_dragging
                if is_dragging and select_rect:
                    end_x = canvas.canvasx(event.x)
                    end_y = canvas.canvasy(event.y)
                    x1, y1, x2, y2 = select_start_x, select_start_y, end_x, end_y
                    if x1 > x2: x1, x2 = x2, x1
                    if y1 > y2: y1, y2 = y2, y1
                    
                    for blk in blocks:
                        # 检查方块是否在框选范围内
                        blk_center_x = (blk['x1'] + blk['x2']) / 2
                        blk_center_y = (blk['y1'] + blk['y2']) / 2
                        if (x1 <= blk_center_x <= x2 and y1 <= blk_center_y <= y2):
                            if not blk['selected']:
                                blk['selected'] = True
                                canvas.itemconfig(blk['id'], fill='#ff4444')
                                canvas.itemconfig(blk['text_id'], fill='#ffffff')
                                start_breathing(blk['index'])
                    
                    canvas.delete(select_rect)
                    select_rect = None
                    is_dragging = False
            
            canvas.bind('<Button-1>', on_mouse_down)
            canvas.bind('<B1-Motion>', on_mouse_move)
            canvas.bind('<ButtonRelease-1>', on_mouse_up)
            
            # 呼吸效果管理 - 修复版
            breathing_animations = {}  # index -> after_id
            breathing_photos = {}      # index -> photo引用，防止垃圾回收
            
            def start_breathing(idx):
                """为指定方块启动呼吸发光效果"""
                # 如果已经在呼吸，先停止
                if idx in breathing_animations:
                    stop_breathing(idx)
                
                blk = blocks[idx]
                if not blk['selected']:
                    return
                
                step = [0]
                direction = [1]
                
                def update_breath():
                    if not blk['selected']:
                        return
                    
                    step[0] += direction[0] * 0.5
                    if step[0] > 0:
                        direction[0] = -1
                    elif step[0] < -2:
                        direction[0] = 1
                    
                    x1, y1, x2, y2 = blk['x1'], blk['y1'], blk['x2'], blk['y2']
                    padding = 8 + step[0]
                    opacity = 200
                    
                    # 使用固定画布尺寸
                    glow_img = Image.new("RGBA", (720, 230), (0, 0, 0, 0))
                    draw = ImageDraw.Draw(glow_img)
                    draw.rectangle(
                        [x1-padding, y1-padding, x2+padding, y2+padding],
                        fill=(255, 30, 30, opacity)
                    )
                    glow_img = glow_img.filter(ImageFilter.GaussianBlur(8))
                    glow_array = np.array(glow_img).astype(np.float32) / 255.0
                    glow_array[..., :3] *= 1.5
                    glow_array = np.clip(glow_array, 0, 1)
                    glow_img = Image.fromarray((glow_array * 255).astype(np.uint8), "RGBA")
                    glow_photo = ImageTk.PhotoImage(glow_img)
                    
                    # 存储photo引用防止垃圾回收
                    breathing_photos[idx] = glow_photo
                    
                    # 删除旧的发光层
                    if hasattr(canvas, f'glow_{idx}'):
                        canvas.delete(getattr(canvas, f'glow_{idx}'))
                    
                    # 创建新的发光层
                    glow_item = canvas.create_image(0, 0, anchor='nw', image=glow_photo)
                    canvas.tag_lower(glow_item)
                    setattr(canvas, f'glow_{idx}', glow_item)
                    
                    # 继续动画
                    breathing_animations[idx] = canvas.after(150, update_breath)
                
                # 启动呼吸动画
                update_breath()
            
            def stop_breathing(idx):
                """停止指定方块的呼吸效果"""
                if idx in breathing_animations:
                    canvas.after_cancel(breathing_animations[idx])
                    del breathing_animations[idx]
                
                if idx in breathing_photos:
                    del breathing_photos[idx]
                
                if hasattr(canvas, f'glow_{idx}'):
                    canvas.delete(getattr(canvas, f'glow_{idx}'))
                    delattr(canvas, f'glow_{idx}')
            
            # 单选（Ctrl+点击切换，普通点击清空其他）
            def on_single_click(idx, event):
                # 重置超时
                kill_timeout()
                
                if event.state & 0x0004:  # Ctrl键按下，切换选中
                    blk = blocks[idx]
                    if blk['selected']:
                        blk['selected'] = False
                        canvas.itemconfig(blk['id'], fill='#ffffff')
                        canvas.itemconfig(blk['text_id'], fill='#333333')
                        stop_breathing(idx)
                    else:
                        blk['selected'] = True
                        canvas.itemconfig(blk['id'], fill='#ff4444')
                        canvas.itemconfig(blk['text_id'], fill='#ffffff')
                        start_breathing(idx)
                else:
                    # 无修饰键：清空其他，只选中当前
                    for i, blk in enumerate(blocks):
                        if i == idx:
                            if not blk['selected']:
                                blk['selected'] = True
                                canvas.itemconfig(blk['id'], fill='#ff4444')
                                canvas.itemconfig(blk['text_id'], fill='#ffffff')
                                start_breathing(idx)
                        else:
                            if blk['selected']:
                                blk['selected'] = False
                                canvas.itemconfig(blk['id'], fill='#ffffff')
                                canvas.itemconfig(blk['text_id'], fill='#333333')
                                stop_breathing(i)
            
            # 悬停效果
            hover_item = None
            
            def on_hover_enter(idx):
                nonlocal hover_item
                if blocks[idx]['selected']:
                    return
                if hover_item:
                    canvas.delete(hover_item)
                blk = blocks[idx]
                x1,y1,x2,y2 = blk['x1'], blk['y1'], blk['x2'], blk['y2']
                glow_img = Image.new("RGBA", (720, 230), (0,0,0,0))
                draw = ImageDraw.Draw(glow_img)
                padding = 10
                draw.rectangle([x1-padding, y1-padding, x2+padding, y2+padding], fill=(200,200,200,60))
                glow_img = glow_img.filter(ImageFilter.GaussianBlur(6))
                glow_photo = ImageTk.PhotoImage(glow_img)
                hover_item = canvas.create_image(0,0, anchor='nw', image=glow_photo)
                canvas.tag_lower(hover_item)
                canvas.hover_photo = glow_photo
            
            def on_hover_leave(idx):
                nonlocal hover_item
                if hover_item:
                    canvas.delete(hover_item)
                    hover_item = None
            
            # 按钮框架
            button_frame = ctk.CTkFrame(main_frame, fg_color='#1a1a1a')
            button_frame.pack(pady=10)
            
            confirm_result = [False]
            selected_values_result = []
            
            def confirm_selection():
                nonlocal selected_values_result
                selected_values_result = [blk['value'] for blk in blocks if blk['selected']]
                confirm_result[0] = True
                popup.destroy()
                # parent_dialog.deiconify()
            
            def cancel_selection():
                confirm_result[0] = False
                popup.destroy()
                # parent_dialog.deiconify()
            
            confirm_button = ctk.CTkButton(
                button_frame,
                text="确定" if lang_setting != "EN" else "Confirm",
                command=confirm_selection,
                font=("SimHei", 14),
                width=100,
                fg_color='#aa0000',
                hover_color='#ff4444'
            )
            confirm_button.pack(side="left", padx=10)
            
            # cancel_button = ctk.CTkButton(
            #     button_frame,
            #     text="取消" if lang_setting != "EN" else "Cancel",
            #     command=cancel_selection,
            #     font=("SimHei", 14),
            #     width=100,
            #     fg_color='#555555',
            #     hover_color='#888888'
            # )
            # cancel_button.pack(side="left", padx=10)
            
            parent_dialog.withdraw()
            
            # 启动超时计时器（60秒无操作自动关闭）
            reset_timeout()
            
            popup.wait_window()
            return selected_values_result, confirm_result[0]
        selected_values, confirmed = select_calibration_range(window)
        # if confirmed:
            # MKPMessagebox.show_info("title:selected_values", f"You selected: {selected_values}")
        need_to_remove_printing_flag=False
        if selected_values==[]:
            selected_values=[0,1,2,3,4,5,6,7,8,9,10]
            # MKPMessagebox.show_info("title:selected_values", f"You selected: {selected_values}")
        else:
            #将对应的偏移值转化为0-10的索引
            selected_indices = [int((0.5 - val) / 0.1) for val in selected_values]
            # MKPMessagebox.show_info("title:selected_indices", f"Selected indices: {selected_indices}")
            need_to_remove_printing_flag=True
        with open(GSourceFile, 'r', encoding='utf-8') as file:
            calibe = file.readlines()
        warnfool_flag=False
        for i in range(len(calibe)):
            if calibe[i].find("; Z_HEIGHT: 1") != -1:
                warnfool_flag=True
                CTkMessagebox(title='提示', message="笨蛋! 你在用Calibaration的3MF打印别的东西, 对不对?")
                # tk.messagebox.showinfo(title='提示', message="笨蛋! 你在用Calibaration的3MF打印别的东西, 对不对?")
                # tk.messagebox.showinfo(title='提示', message="gk")
                break
        # if warnfool_flag==False:
        #     tk.messagebox.showinfo(title='提示', message="正在输出Z偏移校准测试"+"\n\n"+"测试过程中如需中止请取消打印，请勿暂停")

        # os.remove(Output_Filename)
        CaliGcodeExporter = open(Output_Filename, "w", encoding="utf-8")
        MachineType = ""
        MachineType_Extra=""
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
            if calibe[i].find(";======== P2S start gcode==========") != -1:
                MachineType = "P1/P1S"
                MachineType_Extra="P2S"
                break
        # 接下来根据MachineType, 去掉不需要的打印指令
        if need_to_remove_printing_flag==True:
            if MachineType_Extra=="":
                #查找“;===== home after wipe mouth end”出现在哪一行，其后所有指令都去掉
                for i in range(len(calibe)):
                    if calibe[i].find(";===== home after wipe mouth end") != -1 and calibe[i].find("; machine_start_gcode =") == -1:
                        calibe[i:]=[]
                        break
                calibe.append("; filament end gcode")
            else:
                #查找“;===== bed leveling end”出现在哪一行，其后所有指令都去掉
                for i in range(len(calibe)):
                    if calibe[i].find(";===== bed leveling end") != -1 and calibe[i].find("; machine_start_gcode =") == -1:
                        calibe[i:]=[]
                        break
                calibe.append("; filament end gcode")
            # for i in range(len(calibe)):
            #     if calibe[i].find("M622 J1")!=-1 and calibe[i].find("=")==-1:
            #         #从这里开始，往下找，直到找到"M623",中间的所有指令变成“”
            #         j=i+1
            #         while calibe[j].find("M623")==-1:
            #             j+=1
            #         calibe[i:j+1]=[""] * (j - i + 1)


        # 输出文件
        for i in range(len(calibe)):
            print(calibe[i].strip("\n"), file=CaliGcodeExporter)
            if calibe[i].find("; filament end gcode") != -1 and calibe[i].find("=") == -1:
                #输出偏移校准
                #挂载胶箱
                print("G1 X100 Y100 Z10 F3000", file=CaliGcodeExporter)
                print(";Rising nozzle to avoid collision", file=CaliGcodeExporter)
                print("G1 Z" + str(round(para.First_Layer_Height+para.Z_Offset+6, 3)), file=CaliGcodeExporter)
                print(";Mounting Toolhead", file=CaliGcodeExporter)

                #这里不能直接全部输出了。如果need_to_remove_printing_flag为True，需要去掉Custom_Mount_Gcode中的指令。
                if need_to_remove_printing_flag!=True:
                    print(para.Custom_Mount_Gcode.strip("\n"), file=CaliGcodeExporter)
                else:
                    #移除含有G1 E的指令
                    for line in para.Custom_Mount_Gcode.split("\n"):
                        if line.find("G1 E")==-1:
                            print(line.strip("\n"), file=CaliGcodeExporter)
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

                ZOffset_Sing_SP=ZOffset_Sing.split("\n")
                ZOffset_Temp_GCommand=[]
                #运行十次：
                for i in range(11):
                    #空驶到指定位置的调速F
                    ZOffset_Temp_GCommand.append("G1 F" + str(para.Travel_Speed*60))
                    #移动到每一个的开始点：x+11,Y不变
                    OriginCaliLine="G1 X" + str(round(FR_Calibe_X_Start+Offset_Accumulate, 3)) + " Y" + str(round(FR_Calibe_Y_Start, 3))
                    #开始校准的调速F
                    ZOffset_Temp_GCommand.append(Process_GCode_Offset(ZOffset_Sing_SP[1], para.X_Offset+Offset_Accumulate+FR_Calibe_X_Start, para.Y_Offset+FR_Calibe_Y_Start,0,'normal').strip("\n"))
                    ZOffset_Temp_GCommand.append("G1 F" + str(para.Max_Speed))
                    ZOffset_Temp_GCommand.append("G1 Z" + str(round(0.4+para.Z_Offset+Z_Accumulate, 3)))
                    #做一个列表，把ZOffset_Sing按行化成列表
                    for j in range(len(ZOffset_Sing_SP)):
                        ZOffset_Temp_GCommand.append(Process_GCode_Offset(ZOffset_Sing_SP[j], para.X_Offset+Offset_Accumulate+FR_Calibe_X_Start, para.Y_Offset+FR_Calibe_Y_Start,0,'normal').strip("\n"))
                    if Mode=="ZMicro":
                        Z_Accumulate-=0.05
                    elif Mode=="ZOffset":
                        Z_Accumulate-=0.1
                    Offset_Accumulate+=11
                    # print("G1 Z" + str(round(para.Z_Offset+6, 3)), file=CaliGcodeExporter)                    #抬升Z
                    # print("G4 P10000", file=CaliGcodeExporter)
                    ZOffset_Temp_GCommand.append("G1 Z" + str(round(para.Z_Offset+6, 3)))
                    ZOffset_Temp_GCommand.append("G4 P10000")
                    if need_to_remove_printing_flag==True:
                        if i not in selected_indices:   
                            ZOffset_Temp_GCommand.clear()
                    if ZOffset_Temp_GCommand!=[]:
                        for k in range(len(ZOffset_Temp_GCommand)):
                            print(ZOffset_Temp_GCommand[k], file=CaliGcodeExporter)
                        ZOffset_Temp_GCommand.clear()
                #卸载胶箱
                print(";Unmounting Toolhead", file=CaliGcodeExporter)
                # print(para.Custom_Unmount_Gcode.strip("\n"), file=CaliGcodeExporter)
                #这里不能直接全部输出了。如果need_to_remove_printing_flag为True，需要去掉Custom_Unmount_Gcode中的指令。
                if need_to_remove_printing_flag!=True:
                    print(para.Custom_Unmount_Gcode.strip("\n"), file=CaliGcodeExporter)
                else:
                    #移除含有G1 E的指令
                    for line in para.Custom_Unmount_Gcode.split("\n"):
                        if line.find("G1 E")==-1:
                            print(line.strip("\n"), file=CaliGcodeExporter)
                print(";Toolhead Unmounted", file=CaliGcodeExporter)

                print("G1 X100 Y100 Z100", file=CaliGcodeExporter)#空驶

                if MachineType=="A1mini" or MachineType=="A1":
                    print(Calibe_Sing, file=CaliGcodeExporter)#唱歌

                #补全结束
                print(calibe[i].strip("\n"), file=CaliGcodeExporter)
        if need_to_remove_printing_flag==True:
            print("; EXECUTABLE_BLOCK_END", file=CaliGcodeExporter)
        CaliGcodeExporter.close()
    elif Mode=="Repetition":
        # tk.messagebox.showinfo(title='提示', message="正在输出精密度测试"+"\n\n"+"测试过程中如需中止请取消打印，请勿暂停")
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
                print("G1 Z" + str(round(para.First_Layer_Height+para.Z_Offset+6, 3)), file=CaliGcodeExporter)
                print(";Mounting Toolhead", file=CaliGcodeExporter)
                print(para.Custom_Mount_Gcode.strip("\n"), file=CaliGcodeExporter)
                print(";Toolhead Mounted", file=CaliGcodeExporter)
                print("G1 Z"+ str(round(para.First_Layer_Height+para.Z_Offset, 3)), file=CaliGcodeExporter)#Adjust Z
                if MachineType=="A1mini" or MachineType=="A1":
                    print(Calibe_Sing, file=CaliGcodeExporter)#唱歌

                #将LShape_Code中的每一行做偏移后输出
                print(";LShape Repetition Calibration", file=CaliGcodeExporter)
                print("G1 F" + str(para.Max_Speed), file=CaliGcodeExporter)
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
        if CCkcheck_flag!=True:
            #删除原文件
            os.remove(GSourceFile)
        os.remove(Output_Filename+'.te')
        if CCkcheck_flag!=True:
            os.rename(Output_Filename, GSourceFile)
    except Exception as e:
        window.withdraw()
        MKPMessagebox.show_info(title='警报', message='文件被占用，请重新切片:'+str(e))
    # except:
    #     # ctk.messagebox.showinfo(title='警报', message='错误')
    #     # ctk.Messagebox.showinfo(title='警报', message='无法删除临时文件，请手动删除：'+ Output_Filename +'.te')
    #     CTkMessagebox(title='警报', message='无法删除临时文件，请手动删除：'+ Output_Filename +'.te', icon="warning").show()
    exit(0)

if __name__ == "__main__":
    main()
# 等2秒再关闭
window.destroy()
window.mainloop()
exit(0)