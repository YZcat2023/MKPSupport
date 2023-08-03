#coding=gb18030
import re, os,fileinput
#parameters
ztouch=xtouch=xoffset=yoffset=Nozzoff=atX=Filalen=FilaCom=zCom=Tem=Forcedz=0
input=output='NULL'
index=0;patndex=0
valid_file=False#ΪF���޿����ļ�
flag=flag1=flag2=False
reSignal=False
ZComcum=0
Gflag=False#��ֹ������ֵֹ�G92 E0��ƫ
CustomD="NULL"#�Զ������
CustomR="NULL"#�Զ�������
fcon = open("con.txt")
temp=fcon.read()
s = []
path=[]
currHeight=0#�洢��ǰ���ڵĸ߶�
currExtrude=0#�洢��ǰ�ļ���
item=""
s = re.findall("\d+\.?\d*", temp)
s = list(map(float,s))
ztouch=s[0];xtouch=s[1];xoffset=s[2];yoffset=s[3];atX=s[4];Filalen=s[5];FilaCom=s[6];Nozzoff=s[7];zCom=s[8];Tem=s[9];Forcedz=s[10]
#print(s)
#print(Tem)
s.clear()

for line1 in fileinput.input("con.txt"):
    #print( line1)
    if line1.find("X��ƫ��") != -1 and line1.find("-") != -1:
        xoffset=-xoffset
    if line1.find("Y��ƫ��") != -1 and line1.find("-") != -1:
        yoffset = -yoffset
    if line1.find("Z������") != -1 and line1.find("-") != -1:
        zCom= -zCom
    if line1.find("�س鲹��") != -1 and line1.find("-") != -1:
        FilaCom= -FilaCom
    if line1.find("�Զ�������")!=-1:
        index=line1.find("��")
        CustomD=line1[index+1:]
    if line1.find("�Զ������")!=-1:
        index=line1.find("��")
        CustomR=line1[index+1:]

for item in os.listdir():
    if item.find(".g") !=-1 or item.find(".x3g")!=-1:#ʶ��.G,.GCODE,.X3G,�������ļ�
        if item.find("Output")==-1:
            input=item
            valid_file=True
#�ҵ�gcode�ļ�����ȷ�����ļ��Ƿ��Ѵ�������ļ�
index=input.find(".")
output=input[0:index]+"_Output.gcode"

for item in os.listdir():
    if item == output:
        os.remove(item)
#�����һ�����ɵ��ļ�
if valid_file:
    with open(input, "r") as f:#��ȡ�����ļ�
        with open(output, "w") as f1:#����ļ�
            with open("log.txt", "w") as f2:  # �����־
                print("Find your Gcode Successfully", file=f2)  #��־˵����ʱ����
                print("CustomD: " + CustomD, file=f2)
                print("CustomR: " + CustomR, file=f2)
                for line in f.readlines():
                    line = line.strip('\n')#ȥ�����з�
                    if line.find("M104 S")!=-1:
                        index=line.find("S")
                        s = re.findall("\d+\.?\d*", line[index:])
                        Currtem=float(s[0])
                    if line.find(";LAYER_CHANGE")==-1:
                        print(line, file=f1)  # ������ԭ��д��
                        #����ģ��
                        if line.find("G1 Z") != -1:  # �������Z̧��������
                            if line.find(".")==4:
                                linetemp="G1 Z0"+line[4:]#�����.47����
                                s = re.findall("\d+\.?\d*", linetemp)
                                s = list(map(float, s))
                            else:
                                s = re.findall("\d+\.?\d*", line)
                                s = list(map(float, s))
                            currHeight = s[1]
                            print("Height Change: " + str(currHeight), file=f2)  # ��־��¼��ʱ������
                            #print(line, file=f2)  # ��־��¼��ʱ������
                            if reSignal==True:
                                print("G1 E" + str(format(float(currExtrude), '.3f')), file=f1)  # �س�
                                reSignal=False
                        if currHeight >= 0.47:  #��ģ����ǰ���㲻����ʹ��

                            # ������нӴ���ע��

                            if line.find(";TYPE:Support material interface") != -1:  # �������֧�ŽӴ����ע��
                                print("Support interface, Height: " + str(currHeight), file=f2)
                                #print("Check:"+line,file=f2)
                                flag = True  # ������ʾӦ����ʼ��¼�ο�·��
                                flag1=True#������Ҫʹ����˱�
                                path.clear()   
                            if flag == True:

                                if line.find("Perimeter") == -1 and line.find(";TYPE:Support material")==-1:
                                    path.append(line)  # ���������¼��������Ϊ��˱����е�·���ο�
                                    #print("OriginPath: " + line, file=f2)  # ˵����ԭ��·��
                                #if line.find("G92 E0")!=-1
                                #    count
                                if line.find("Perimeter") != -1 or (line.find(";TYPE:Support material")!=-1 and line.find("interface")==-1):
                                    path.append(line)#��¼����л�
                                    flag = False  # ����ʾȡ��
                                    #print(path,file=f2)
                                    print("Perimeter detected,stop copying", file=f2)  # ������־
                                    #print(";Perimeter detected,stop copying", file=f1)  # ������־

                        if line.find("G1")!=-1 and line.find("E")!=-1:
                            index=line.find("E")
                            s = re.findall("\d+\.?\d*",line[index:])
                            currExtrude=s[0]#��ǰ����
                    else:
                        if flag1 == True:
                            if Filalen!=0:  # ���Ҫ���˻س�Ĳ�
                               print(";Filament retracting:", file=f1)
                               print("G1 E" + str(format(float(currExtrude) - Filalen,'.3f')), file=f1)  # �س�
                               print("Filament retracted!", file=f2)  # ��־˵����ʱ�س�
                               print("G1 Z"+str(format(currHeight+0.5,'.3f')),file=f1)
                               reSignal = True  # ��ʾ�´ξ���Ҫװ�غĲ���

                            print(";TYPE:Markpen path", file=f1)  # д��ע��˵����Щ����˱ʵ�·��


                            if CustomR.find("undefined")!=-1:
                                if ztouch!=0:
                                    if atX == 1:
                                        print("G1 X0", file=f1)
                                    print("G1 Z" + str(ztouch), file=f1)  # lift nozzle
                                    # ��Z���������ܴ����ĸ߶ȣ�Zspx��ʾ����ٶȡ���ʱ�ǰ���
                                    print("G1 Z" + str(format(currHeight+Nozzoff+5,'.3f')), file=f1)  # lower nozzle
                                    # ���ظոռ��صĸ߶ȣ�Ҳ����currHeight���������¼�ĸ߶�,��5��ֹ��ͷ��Ⱦ�����ط�
                                elif xtouch!=0:
                                    print("G1 Z"+format(currHeight+Nozzoff,".3f"),file=f1)
                                    #���������Է��в�
                                    print("G1 X"+str(xtouch),file=f1)
                                    #ײ������
                                    print("G1 X"+str(xtouch-35),file=f1)
                                    #�ɿ�
                                if Tem != 0:
                                    print("M104 S" + str(Currtem - Tem), file=f1)
                                print("Default Deploy",file=f2)


                            else:
                                print(CustomD,file=f1)
                                print("Customized Deploy",file=f2)
                                if Tem != 0:
                                    print("M104 S" + str(Currtem - Tem), file=f1)
                            # ��־��¼

                            print("Markpen path starting", file=f2)  # д����־˵����Щ����˱ʵ�·��
                            #print(path,file=f2)
                            for pathindex,item in enumerate(path):
                                if item.find(";") != -1 or item.find("G1") == -1:
                                    print("Not valid Path: " + item, file=f2)
                                    if item.find("G92 E0")!=-1:
                                        print("G1 Z"+str(format(currHeight+Nozzoff+0.5,'.3f')),file=f1)#��΢����0.5������в�
                                        if path[pathindex+3].find("TYPE")==-1:  #��δ�л�����
                                            Gflag=True#��ʾ������Ҫ���͸߶�
                                        else:
                                            break#ʣ�µ�Ҳ���ؿ���


                                else:
                                    #����Ϊ��˱����·��
                                    s = re.findall("\d+\.?\d*", item)
                                    if item.find("X") != -1 and item.find("Y") != -1:  # X,Y������
                                        #print("Original: " + item, file=f2)  # д����־
                                        print("G1 X" + str(format(float(s[1]) + xoffset,'.3f')) + " Y" +
                                              str(format(float(s[2]) +yoffset,'.3f')), file=f1)
                                        #print("Modified:" + "G1 X" + str(format(float(s[1]) + xoffset, '.3f')) + " Y" + str(format(float(s[2]) + yoffset, '.3f')), file=f2)#д����־
                                        if flag2 == False:
                                            print("G1 Z" + str(format(currHeight+Nozzoff,'.3f')), file=f1)
                                            #print(";Path 1",file=f1)
                                            flag2=True
                                    if item.find("Y") == -1 and item.find("X") != -1:  # ֻ��X
                                        #print("Original: " + item, file=f2)  # д����־
                                        print("G1 X" + str(format(float(s[1]) + xoffset,'.3f')), file=f1)
                                        #print("Modified:" + "G1 X" + str(format(float(s[1]) + xoffset,'.3f')),file=f2)  # д����־
                                        if flag2 == False:
                                            print("G1 Z" + str(format(currHeight+Nozzoff,'.3f')), file=f1)
                                            #print(";Path 1", file=f1)
                                            flag2 = True
                                    if item.find("Y") != -1 and item.find("X") == -1:  # ֻ��Y
                                        #print("Original: " + item, file=f2)  # д����־
                                        print("G1 Y" + str(format(float(s[1]) + yoffset,'.3f')), file=f1)
                                        #print("Modified:" + "G1 Y" + str(format(float(s[1]) + yoffset,'.3f')),file=f1)
                                        if flag2 == False:
                                            print("G1 Z" + str(format(currHeight+Nozzoff,'.3f')), file=f1)

                                            flag2 = True
                                    if Gflag==True:
                                        print("G1 Z"+str(format(currHeight+Nozzoff,'.3f')),file=f1)
                                        Gflag=False

                            #path.clear()

                            print("G1 Z"+str(format(currHeight+Nozzoff+5,'.3f')),file=f1)#��΢����һ�´�ӡ������

                            #print(atX)

                            if Tem!=0:
                                print("M104 S"+str(Currtem),file=f1)
                            if CustomR.find("undefined")!=-1:
                                if ztouch!=0:
                                    if atX == 1:
                                        print("G1 X0", file=f1)
                                    if zCom!=0:
                                        print("G1 Z" + str(ztouch + ZComcum), file=f1)  # lift nozzle
                                        ZComcum+=zCom
                                    else:
                                        print("G1 Z" + str(ztouch), file=f1)  # lift nozzle
                                    # ��Z���������ܴ����ĸ߶ȣ�Zspx��ʾ����ٶȡ���ʱ�ǰ���
                                    print("G1 Z" + str(format(currHeight+Nozzoff+5,'.3f')), file=f1)  # lower nozzle
                                    # ���ظոռ��صĸ߶ȣ�Ҳ����currHeight���������¼�ĸ߶�,��5��ֹ��ͷ��Ⱦ�����ط�
                                    if zCom != 0:
                                        print("G1 Z" + str(currHeight + 1), file=f1)
                                        print("G92 Z" + str(currHeight + 1 - zCom), file=f1)
                                        print("ZCompensation:G92",file=f2)
                                    print(Forcedz)
                                    if Forcedz!=0:
                                        print("G28 Y",file=f1)
                                        print("G28 Z",file=f1)
                                        print("ZCompensation:G28",file=f2)
                                elif xtouch!=0:
                                    print("G1 Z"+format(currHeight+Nozzoff,".3f"),file=f1)
                                    #���������Է��в�
                                    print("G1 X"+str(xtouch),file=f1)
                                    #ײ������
                                    print("G1 X"+str(xtouch-35),file=f1)
                                    #�ɿ�
                                print("Default Retract",file=f2)

                            else:
                                print(CustomR,file=f1)
                                print("Customized Retract",file=f2)
                            # ��־��¼
                            flag1=False
                            flag2=False
    os.startfile(output)
    os.startfile("log.txt")
else:
    with open("log.txt", "w") as f2:  # �����־
        print("Error: No available GCODE",file=f2)#˵��������û�ļ��Ĵ���
