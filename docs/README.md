<div align="center" style="margin: 30px 0 30px 0">
   <a href="https://github.com/YZcat2023/MKPSupport">
      <img width="80px" src="assets/icon_round.png" alt="icon">
   </a>
   <h3>MKP Support</h3>
   
   <p>
      <img src="https://img.shields.io/badge/Python-3.8%2B-blue" alt="python">
      <img src="https://img.shields.io/badge/CTkMessagebox-2.4%2B-orange" alt="ctkmessagebox">
      <img src="https://img.shields.io/badge/customtkinter-5.2%2B-8A2BE2" alt="customtkinter">
      <img src="https://img.shields.io/badge/Pillow-10.0%2B-green" alt="pillow">
      <img src="https://img.shields.io/badge/license-MIT-brightgreen" alt="license">
   </p>
   
   <!-- 语言切换按钮 -->
   <div class="language-switcher">
      <button id="lang-en" class="lang-btn" onclick="switchLanguage('en')">English</button> |
      <button id="lang-zh" class="lang-btn active" onclick="switchLanguage('zh')"><b>中文(简体)</b></button>
   </div>
   
   <style>
      .language-switcher {
         margin: 15px 0;
      }
      .lang-btn {
         background: none;
         border: none;
         color: #0366d6;
         cursor: pointer;
         font-size: 16px;
         padding: 5px 10px;
         transition: color 0.3s;
      }
      .lang-btn:hover {
         color: #0550ae;
         text-decoration: underline;
      }
      .lang-btn.active {
         color: #000;
         font-weight: bold;
      }
      .lang-content {
         display: none;
      }
      .lang-content.active {
         display: block;
      }
   </style>
   
   <script>
      // 页面加载时默认显示中文
      document.addEventListener('DOMContentLoaded', function() {
         // 隐藏所有语言内容
         document.querySelectorAll('.lang-content').forEach(el => {
            el.style.display = 'none';
         });
         
         // 显示中文内容
         document.getElementById('content-zh').style.display = 'block';
         document.getElementById('content-en').style.display = 'none';
         
         // 设置按钮状态
         document.getElementById('lang-zh').classList.add('active');
         document.getElementById('lang-en').classList.remove('active');
      });
      
      function switchLanguage(lang) {
         // 更新内容显示
         document.getElementById('content-en').style.display = lang === 'en' ? 'block' : 'none';
         document.getElementById('content-zh').style.display = lang === 'zh' ? 'block' : 'none';
         
         // 更新按钮状态
         document.getElementById('lang-en').classList.toggle('active', lang === 'en');
         document.getElementById('lang-zh').classList.toggle('active', lang === 'zh');
         
         // 保存用户选择到本地存储
         localStorage.setItem('preferred-language', lang);
         
         return false;
      }
      
      // 检查本地存储中的语言偏好
      window.onload = function() {
         const savedLang = localStorage.getItem('preferred-language');
         if (savedLang && (savedLang === 'en' || savedLang === 'zh')) {
            switchLanguage(savedLang);
         } else {
            // 默认显示中文
            switchLanguage('zh');
         }
      };
   </script>
</div>

<!-- 中文内容 -->
<div id="content-zh" class="lang-content active">
   <h2>✨ 什么是MKP Support？</h2>
   <p>还在为3D打印的支撑难拆、留痕而烦恼吗？MKP Support让你的支撑变得像撕便利贴一样轻松！</p>
   <p><strong>简单来说</strong>：我们发明了一种在支撑面涂胶的方法，留下的接触面光滑平整，几乎看不出支撑痕迹，拆除轻松。</p>

   <h2>🖊️ 为什么比传统方法更好？</h2>
   <p><strong>相比普通支撑</strong>：不再需要用刀撬、用钳子拽，告别划伤手指，同时达到极为光滑的效果</p>
   <p><strong>相比水溶支撑</strong>：不需要专门购买水溶耗材，不需要担心受潮，效果几乎相同，成本却完全不一样</p>
   <p><strong>组装极为简单</strong>：零件仅需磁铁、螺丝、弹簧(P1/X1)、笔芯等</p>

   <h2>🎯 预期效果</h2>
   <p>✅ <strong>节省时间</strong>：拆支撑从几分钟缩短到几秒钟<br>
   ✅ <strong>节省材料</strong>：MKP不需要换料冲刷<br>
   ✅ <strong>完美表面</strong>：支撑接触面平整光滑<br>
   ✅ <strong>提高成功率</strong>：减少拆除支撑时损坏的风险</p>

   <h2>📸 效果展示</h2>
   <p>实际打印测试件展示，可以看到支撑面极其光滑：</p>
   <img width="600px" src="images/instr.png" alt="sample">

   <h2>📦 快速开始</h2>
   <h3>1. 准备材料</h3>
   <p>🛒 你需要购买对应机型的BOM表指示的配件。</p>

   <h3>2. 安装硬件</h3>
   <p>- <strong>下载并打印</strong>对应机型的零件。<br>
   - <strong>组装零件</strong>：按照说明书视频组装装置</p>

   <h3>3. 配置软件</h3>
   <p><strong>下载程序</strong>：<a href="https://github.com/YZcat2023/MKPSupport/releases">前往 Releases 页面</a></p>

   <h2>🛠️ 正在开发中</h2>
   <p>🔧 <strong>近期计划</strong>：</p>
   <p>- [x] 多色打印支持<br>
   - [x] 更多微调选项<br>
   - [ ] 更多打印机型号适配</p>
   <p>📋 <strong>查看完整清单</strong>：<a href="https://github.com/YZcat2023/MKPSupport/issues">Issues页面</a></p>
   <p>有关提议功能（和已知问题）的完整列表，请参阅 <a href="https://github.com/YZcat2023/MKPSupport/issues">issues</a></p>

   <h2>🤝 为此项目做出贡献</h2>
   <p>- 我们正在寻找有能力的开发人员加入我们，让此项目变的更好，如果您愿意加入我们，欢迎联系我们，我们非常欢迎。<br>
   - 您也可以帮助开发者提交 <a href="https://github.com/YZcat2023/MKPSupport/pulls">PullRequests</a>！<br>
     提交请求也是一种对此项目的贡献方式，我们会审阅您的提交，然后接管维护下去。<br>
   - 另请参阅 <a href="https://github.com/YZcat2023/MKPSupport/issues">issues</a></p>

   <h3>🙏 贡献名单</h3>
   <p>- Thanks to thyfk for programming supports and okookey for translating the English instructions</p>
   <!-- TODO: 贡献者成员名单 -->

   <h2>📄 License</h2>
   <p>此项目采用 <strong>The Unlicense</strong> 许可授权。这意味着您可以自由使用、修改、分发本项目中的代码，有关信息请参阅 <a href="../LICENSE"><code>LICENSE</code></a></p>

   <h2>📞 联系我们</h2>
   <p>请发送邮件到 <code>Jhmodel01@outlook.com</code> 或者加入QQ群：668350689</p>
</div>

<!-- 英文内容 -->
<div id="content-en" class="lang-content">
   <h2>✨ What is MKP Support?</h2>
   <p>Still troubled by hard-to-remove 3D printing supports and the marks they leave behind? MKP Support makes removing supports as easy as peeling off a sticky note!</p>
   <p><strong>In simple terms</strong>: We've invented a method of applying an adhesive layer on the support interface, which leaves the contact surface smooth and flat, almost invisible, and incredibly easy to remove.</p>

   <h2>🖊️ Why is it better than traditional methods?</h2>
   <p><strong>Compared to standard supports</strong>: No more prying with knives or pulling with pliers. Say goodbye to scratched fingers, while achieving an exceptionally smooth finish.</p>
   <p><strong>Compared to water-soluble supports</strong>: No need to buy specialized water-soluble filaments, no worries about moisture absorption. The results are nearly identical, but the cost is completely different.</p>
   <p><strong>Extremely simple assembly</strong>: The parts only require magnets, screws, springs (for P1/X1), pen refills, etc.</p>

   <h2>🎯 Expected Results</h2>
   <p>✅ <strong>Saves Time</strong>: Support removal goes from minutes to seconds.<br>
   ✅ <strong>Saves Material</strong>: MKP doesn't require material changes or flushing.<br>
   ✅ <strong>Perfect Surface</strong>: The support contact surface is flat and smooth.<br>
   ✅ <strong>Increases Success Rate</strong>: Reduces the risk of damage during support removal.</p>

   <h2>📸 Demo</h2>
   <p>Showcase of actual printed test pieces. Note the extremely smooth support surface:</p>
   <img width="600px" src="images/instr.png" alt="sample">

   <h2>📦 Quick Start</h2>
   <h3>1. Prepare Materials</h3>
   <p>🛒 You need to purchase the components indicated in the BOM list for your specific printer model.</p>

   <h3>2. Install Hardware</h3>
   <p>- <strong>Download and Print</strong> the parts for your printer model.<br>
   - <strong>Assemble the parts</strong>: Follow the instructional video to assemble the device.</p>

   <h3>3. Configure Software</h3>
   <p><strong>Download the program</strong>: <a href="https://github.com/YZcat2023/MKPSupport/releases">Go to the Releases page</a></p>

   <h2>🛠️ In Development</h2>
   <p>🔧 <strong>Planned for the near future</strong>:</p>
   <p>- [x] Multi-color printing support<br>
   - [x] More fine-tuning options<br>
   - [ ] Support for more printer models</p>
   <p>📋 <strong>See the full list</strong>: <a href="https://github.com/YZcat2023/MKPSupport/issues">Issues page</a></p>
   <p>For a complete list of proposed features (and known issues), please refer to the <a href="https://github.com/YZcat2023/MKPSupport/issues">issues</a>.</p>

   <h2>🤝 Contributing to This Project</h2>
   <p>- We are looking for capable developers to join us and make this project better. If you are willing to join, please feel free to contact us. We welcome you warmly.<br>
   - You can also help the developers by submitting <a href="https://github.com/YZcat2023/MKPSupport/pulls">Pull Requests</a>! Submitting a pull request is also a way to contribute to this project. We will review your submission and then take over maintenance.<br>
   - Also, please see the <a href="https://github.com/YZcat2023/MKPSupport/issues">issues</a>.</p>

   <h3>🙏 Contributors</h3>
   <p>- Thanks to thyfk for programming supports and okookey for translating the English instructions</p>
   <!-- TODO: Contributor List -->

   <h2>📄 License</h2>
   <p>This project is licensed under <strong>The Unlicense</strong>. This means you are free to use, modify, and distribute the code in this project. For more information, please refer to <a href="../LICENSE"><code>LICENSE</code></a>.</p>

   <h2>📞 Contact Us</h2>
   <p>Please send an email to <code>Jhmodel01@outlook.com</code> or join the QQ group: 668350689.</p>
</div>
