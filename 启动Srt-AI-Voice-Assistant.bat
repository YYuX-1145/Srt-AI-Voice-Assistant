chcp 65001
echo "启动脚本仅供参考；不会安装依赖请使用打包版"
runtime\python.exe Srt-AI-Voice-Assistant.py -p 0 :: -p 指定端口并覆盖程序内设置，0=自动 ，可选  -server_mode：锁定大多数在多人环境下可能产生冲突的功能
pause