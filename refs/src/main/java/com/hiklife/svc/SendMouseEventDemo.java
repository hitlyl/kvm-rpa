package com.hiklife.svc;
import refs.com.hiklife.svc.console.KVMCCloseCallBak;
import refs.com.hiklife.svc.console.KVMCInst

import refs.src.main.java.com.hiklife.svc.SendMouseEventDemo;ance;

/**
 * 验证鼠标事件
 */
public class SendMouseEventDemo {
    private KVMCInstance instance;
    public SendMouseEventDemo(){
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

    public static void main(String[] args) throws InterruptedException {
        final int LEFT_BUTTON_MASK = 1;
        SendMouseEventDemo sendMouseEventDemo = new SendMouseEventDemo();

        // 按住鼠标左键对角线向下移动
       for(int i=0; i<50; i++){
           sendMouseEventDemo.instance.sendRELMouseEvent(4,4,LEFT_BUTTON_MASK);
       }
        // 按住鼠标左键对角线向上移动
       for(int i=0; i<50; i++){
           sendMouseEventDemo.instance.sendRELMouseEvent(-4,-4,LEFT_BUTTON_MASK);
       }
       // 松开左键
        sendMouseEventDemo.instance.sendRELMouseEvent(0,0,0);

       // 等待事件处理完成后退出
       try {
            Thread.sleep(1000);
           sendMouseEventDemo.instance.stopSession();
        } catch (InterruptedException e) {
            e.fillInStackTrace();
        }
    }
}
