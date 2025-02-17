<div align="center" style="margin: 30px 0 30px 0">
   <a href="https://github.com/YZcat2023/MKPSupport">
      <img width="80px" src="assets/icon_round.png" alt="icon">
   </a>
   <h3>MKP Support</h3>
   <p>更好的 FDM 打印打印支撑方案</p>
   <a href="README.md">English</a> |
   <a href="#"><b>中文(简体)</b></a>
   <p>
      <img src="https://img.shields.io/badge/build-uv-29AC47" alt="python">
      <img src="https://img.shields.io/badge/Python-3.12%2B-blue" alt="python">
      <img src="https://img.shields.io/badge/Pillow-10.2%2B-green" alt="pillow">
      <img src="https://img.shields.io/badge/tkinter-8.6%2B-green" alt="tkinter">
   </p>
   <p>
      <a href="https://github.com/YZcat2023/MKPSupport/blob/main/MKP%20Manual.pdf">
         <strong>Download MKP Manual »</strong>
      </a>
   </p>
</div>

## 关于本项目的一些想法

使用 [FDM 3D打印机](https://en.wikipedia.org/wiki/Fused_filament_fabrication#Fused_deposition_modeling) 打印零件时，
支撑总是一个让人头疼的问题。它们有时很难拆除，拆除支撑后的零件表面也不太平整。那么，降低支撑层与零件间的层粘也许是一个好主意？
试试看 [MKP Support](https://github.com/YZcat2023/MKPSupport) 吧，它能实现相当好的效果：

支撑面光滑平整不粘手，且颜色与零件主体没有区别。由于加入了熨烫支撑面的功能，也许效果比使用水溶支撑还要好。只需要四块磁铁，两个螺丝，一瓶液体胶等等，您就可以升级您的打印机。

我找来了一只马克笔涂抹支撑面，结果相当成功。接触面看上去很平滑。
不过，马克笔的方案并不十分令人满意：它似乎不能在 [CoreXY](https://en.wikipedia.org/wiki/CoreXY) 机器上工作。
于是我找来了一些*gluepen refills*(**点点胶替芯** in Chinese）。
胶水是透明的，因此接触面效果更加好了。不过，它似乎很容易就用完了。所以我设计了一个零件用来储存胶水，并且重新编写了程序。

### 想要达到的效果

- 减少时间与材料的浪费
- 提高接触面的表面效果
- 提高打印的成功率

## 演示

- 这是一些测试打印件, 可以从图片中看到支撑面打印效果

<img width="600px" src="images/blue.jpg" alt="sample">
<img width="600px" src="images/1739420103133.jpg" alt="sample">

## 准备工作

想要获取更多信息，请参阅 [MKP Manual.pdf](MKP%20Manual.pdf)

1. 准备材料:
   * 点点胶笔芯、透明液体状办公胶水
   * M2.5*5 螺丝 **x 2**
   * 直径4毫米，厚度1.5毫米的磁铁 **x 4**
2. 模型的打印与装配:
   * 下载我们准备好的3D模型并完成打印。
   * 将打印件组装后安装在3D打印机的合适位置。
   * 根据实际机型可能需要调整模型完成适配。
3. 软件配置
   * 请到 [Releases](https://github.com/YZcat2023/MKPSupport/releases/latest) 页面下载对应的程序。
   * 将下载后的文件放在合适的位置，然后打开程序，在弹出的对话框内填写必要的参数生成配置文件。
   * 复制刚刚下载的程序路径到 Orca Slicer 的后处理脚本中。
     ```gcode
     ; 例如
     "C:/User/name/mkp/mkp.exe"
     ```
   * 调整切片设置确保能够完成 `gcode` 的插入

## 计划列表 & 已知问题

- [ ] 多色打印支持
- [x] 熨烫支持选项

有关提议功能（和已知问题）的完整列表，请参阅 [issues](https://github.com/YZcat2023/MKPSupport/issues)

## 为此项目做出贡献

- 我们正在寻找有能力的开发人员加入我们，让此项目变的更好，如果您愿意加入我们，欢迎联系我们，我们非常欢迎。
- 您也可以帮助开发者提交  [PullRequests](https://github.com/YZcat2023/MKPSupport/pulls)！
  提交请求也是一种对此项目的贡献方式，我们会审阅您的提交，然后接管维护下去。
- 另请参阅 [issues](https://github.com/YZcat2023/MKPSupport/issues)

### 贡献名单

- Thanks to thyfk for programming supports and okookey for translating the English instructions

<!-- TODO: 贡献者成员名单 -->

## License

此项目采用 **The Unlicense** 许可授权。这意味着您可以自由使用、修改、分发本项目中的代码，有关信息请参阅 [`LICENSE`](../LICENSE)

## 联系我们

请发送邮件到 `Jhmodel01@outlook.com`
