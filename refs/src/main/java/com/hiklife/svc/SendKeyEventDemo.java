package com.hiklife.svc;

import javax.swing.*;

import refs.com.hiklife.svc.console.KVMCCloseCallBak;
import refs.com.hiklife.svc.console.KVMCInstance;

import refs.src.main.java.com.hiklife.svc.SendKeyEventDemo;
import refs.com.hiklife.svc.console.Key;
import refs.com.hiklife.svc.core.protocol.normal.KeyEventPacket;

import java.awt.*;

/**
 * 验证发送键盘事件
 */
public class SendKeyEventDemo {
    private KVMCInstance instance;
    public SendKeyEventDemo(){
        try {
            instance = Kvm4JSdk.connectKVMC("192.168.0.100", 5900, 0, "admin", "123456", 5000);
            instance.setKvmCCloseCallBak(new KVMCCloseCallBak() {
                @Override
                public void invoke(String s) {
                    System.out.println("connectKVMC close:" + s);
                    System.exit(0);
                }
            });

        } catch (Exception e) {
            System.out.println("connectKVMC error");
            System.exit(0);
        }
    }

    public static void main(String[] args) throws Exception {
        SendKeyEventDemo sendKeyEventDemo = new SendKeyEventDemo();
        for( int i=0; i<100; i++){
            //1键盘 循环发送100次
            sendKeyEventDemo.instance.sendKeyEvent(KeyEventPacket.DOWN, Key.KEY_1);
            sendKeyEventDemo.instance.sendKeyEvent(KeyEventPacket.UP, Key.KEY_1);
        }
        // 发送字符串
        sendKeyEventDemo.instance.autoSendEnChars("1234567890-=~!@#$%^&*()_+ qwertyuiopQWERTYUIOP");
        // 等待事件处理完成后退出
        try {
            Thread.sleep(1000);
            sendKeyEventDemo.instance.stopSession();
        } catch (InterruptedException e) {
            e.fillInStackTrace();
        }
    }
}
