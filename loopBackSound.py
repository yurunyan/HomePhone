#!/usr/bin/python
# -*- coding: utf-8 -*-
 
# モジュールをインポートする
import pyaudio
import RPi.GPIO as GPIO
#import time
import os
import sys
import threading

# ボタンチェックするか否か
BUTTON_CHECK=True
#BUTTON_CHECK=False

# ボタンが繋がったピン番号の定義
BUTTON=21

# ボタンのタイプ
BUTTON_TYPE=0 # プルダウン式
#BUTTON_TYPE=1 # プルアップ式

# チェックする間隔
INTERVAL=1

# daemon化するか否か
DAEMON=False
PID_FILE='/var/run/homePhone.pid'

# 音声処理のパラメータ
#RATE=88200
RATE=44100
#CHUNK=1024
CHUNK=128

#グローバル変数
#pinState=False # ボタンが押されているか否かを示す変数
#pinState=True # ボタンが押されているか否かを示す変数

pinState = 0 # ボタンが押されているか否かを示す変数

def buttonCallBack(self):
    global pinState
    if (1==GPIO.input(BUTTON)):
        pinState=1
    else:
        pinState=2

# GPIOのピンの設定
def setup(pin):
    # GPIOの初期化
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.add_event_detect(pin, GPIO.BOTH)
    GPIO.add_event_callback(pin, buttonCallBack)
    # 音声デバイスのオープン
    #return audio.open(   format = pyaudio.paInt16,
    #  #channels = 1,
    #  channels = 2,
    #  rate = rate,
    #  frames_per_buffer = chunk,
    #  input = True,
    #  output = True) # inputとoutputを同時にTrueにする

# なにかのエラーで終了する場合は，PIDファイルを消去，GPIOの設定をリセット, オーディオをクローズ
def finish(audio,pidFile):
    # オーディオデバイスをクローズ
    audio.terminate()
    # GPIO設定をリセット
    GPIO.cleanup()
    # ファイルを消す
    if os.path.exists(pidFile):
        os.remove(pidFile)
    sys.exit()

# daemon化する処理
def fork(pidFile,check,audio,chunk):
    pid = os.fork()
    if pid > 0:
        f = open(pidFile,'w')
        f.write(str(pid)+"\n")
        f.close()
        sys.exit()
    if pid == 0:
        loop(check,audio,chunk)

# ループの1ラウンド
def oneRound(instream,outstream,chunk):
    if (instream.is_active()):
        input = instream.read(CHUNK,False)
        play=threading.Thread(target=dataOut, name="play", args=(outstream,input,))
        play.start()
        #dataOut(outstream,input)
        #output = outstream.write(input)

# メインのループ
#def loop(check,chunk):
def loop(check,audio,chunk):
    global pinState
    while True:
        if check:
            if pinState==1:
                pinState=3
                #audio=pyaudio.PyAudio()
                # 音声入力デバイスのオープン
                instream= audio.open(   format = pyaudio.paInt16,
                    channels = 2,
                    rate = RATE,
                    frames_per_buffer = chunk,
                    input = True) 
                # 音声出力デバイスのオープン
                outstream= audio.open(   format = pyaudio.paInt16,
                    channels = 2,
                    rate = RATE,
                    frames_per_buffer = chunk,
                    output = True)
                oneRound(instream,outstream,chunk)
            if pinState==2:
                instream.stop_stream()
                instream.close()
                outstream.stop_stream()
                outstream.close()
                #audio.terminate()
            if pinState==3:
                oneRound(instream,outstream,chunk)
        else:
            oneRound(instream,outstream,chunk)

# パッファ分の音声を出力
def dataOut(stream,data):
    stream.write(data)

# メイン
if __name__ == '__main__':
    #setup(BUTTON)
    #audio=pyaudio.PyAudio()
    #loop(BUTTON_CHECK,audio,CHUNK)
    #loop(BUTTON_CHECK,CHUNK)
    try:
        stream=setup(BUTTON)
        audio=pyaudio.PyAudio()
    except:
        finish(audio,PID_FILE)
    if DAEMON:
        try:
            fork(PID_FILE,BUTTON_CHECK,audio,CHUNK)
        except:
            finish(audio,PID_FILE)
    else:
        try:
            loop(BUTTON_CHECK,audio,CHUNK)
        except:
            finish(audio,PID_FILE)


