#!/bin/sh
which screen >> /dev/null 2>&1
flag=$?
if [ $flag -ne 0 ] ; then
    echo "请先安装screen再运行启动脚本"
    exit 1
fi
screen -dmS telegram-bot python3 main.py
