确保系统已安装Python 3.9和以下依赖库：numpy、scipy、pyyaml >= 6.0、svgwrite、psutil、matplotlib、svgpathtools、cairoSVG、PySimpleGUI (仅限Windows)、wmi (仅限Windows)。若未安装，可使用命令行工具在conda虚拟环境中安装：

```bash
conda create -n garmentcode python=3.9  
conda activate garmentcode  
pip install numpy scipy pyaml svgwrite psutil matplotlib svgpathtools cairosvg pysimplegui wmi
```

打开虚拟环境，进入工程文件夹，可使用命令行工具打开GUI界面进行设计。例如：

```bash
1.C:\Users\灰>conda activate Gradprj
2.(Gradprj) C:\Users\灰>cd C:\Users\Public\GradPrj
3.(Gradprj) C:\Users\Public\GradPrj>python gui.py
```

点击“Save”按钮，保存当前的服装版片设计文件到文件输出路径，可以在控制台查看保存结果。若保存成功，控制台显示如下：

```bash
Success! Configured_design saved to C:\Users\Public\GradPrj\Logs\Configured_design
```

也可使用命令行工具直接进行批量生产服装版片，并通过控制台查看生成进度。命令行可用的配置参数：

- 使用到的人体尺寸文件，默认为`“thin”：-b type=str, choices=['avg', 'thin', 'full-bodied', 'man'], default='thin'`
- 输出路径，默认为工程文件下的Logs文件夹：`-o type=str, default='./Logs', help="Output file path.`
- 3、最多生成服装的件数，默认为10：`-p type=int, default=10, help='how many pieces you want to generate, to limit the number of pieces’`

示例：

```bash
C:\Users\灰>conda activate Gradprj
(Gradprj) C:\Users\灰>cd C:\Users\Public\GradPrj
(Gradprj) C:\Users\Public\GradPrj>python generate_all_possible_clothes.py -p 20
配置文件中一共有 3 种可变字段  
[DONE] 1 saved to ./Logs\1
[DONE] 2 saved to ./Logs\2
[DONE] 3 saved to ./Logs\3
[DONE] 4 saved to ./Logs\4
[DONE] 5 saved to ./Logs\5
[DONE] 6 saved to ./Logs\6
[DONE] 7 saved to ./Logs\7
[DONE] 8 saved to ./Logs\8
[DONE] 9 saved to ./Logs\9
[DONE] 10 saved to ./Logs\10
[DONE] 11 saved to ./Logs\11
[DONE] 12 saved to ./Logs\1
[DONE] 13 saved to ./Logs\13
[DONE] 14 saved to ./Logs\14
[DONE] 15 saved to ./Logs\15
[DONE] 16 saved to ./Logs\16
[DONE] 17 saved to ./Logs\17
[DONE] 18 saved to ./Logs\18
[DONE] 19 saved to ./Logs\19
[DONE] 20 saved to ./Logs\20
```

在输出路径文件夹（这里为./Log）中可以看到批量的生产服装版片。

![**输出文件夹**](attachment:de604f02-665e-4dc5-b382-23820e15efc8:图片6.png)

**输出文件夹**
