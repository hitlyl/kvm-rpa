package com.hiklife.svc;

import org.bytedeco.ffmpeg.avutil.AVFrame;

import refs.com.hiklife.svc.console.KVMCAVFrameCallBack;
import refs.com.hiklife.svc.consol

import refs.src.main.java.com.hiklife.svc.PlayFrameDemo;

import refs.com.hiklife.svc.console.KVMCInstance;
import refs.com.hiklife.svc.util.UIKit;

import javax.swing.*;
import java.awt.*;
import java.awt.image.BufferedImage;

/**
 * 验证图片帧的延时
 */
public class PlayFrameDemo extends JFrame implements KVMCAVFrameCallBack {
    private final JComponent component;
    private BufferedImage lastImage;
    public PlayFrameDemo(){
        super("测试图片帧延时");
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setSize(960, 540);
        component = new JComponent() {
            @Override
            protected void paintComponent(Graphics g) {
                Graphics2D g2d = (Graphics2D) g;
                if (lastImage == null) {
                    g2d.setPaint(Color.BLACK);
                    g2d.fillRect(0, 0, getWidth(), getHeight());
                } else {
                    g2d.drawImage(lastImage, 0, 0, getWidth(), getHeight(), null);
                }
            }
        };
        setLayout(new BorderLayout());
        add(component,BorderLayout.CENTER);
        setVisible(true);
        try {
            KVMCInstance instance = Kvm4JSdk.connectKVMC("192.168.0.100", 5900, 0, "admin", "123456", 5000);
            instance.setKvmCAVFrameCallBack(this);
            instance.setKvmCCloseCallBak(new KVMCCloseCallBak() {
                @Override
                public void invoke(String s) {
                    System.out.println("connectKVMC error:" + s);
                    System.exit(0);
                }
            });

        } catch (Exception e) {
            System.out.println("connectKVMC error");
            System.exit(0);
        }
    }

    @Override
    public void invoke(AVFrame avFrame) {
        // 快速转为RGB图片
        lastImage = UIKit.getBufferedImage(avFrame, lastImage);
        component.repaint();
    }

    public static void main(String[] args){
        new PlayFrameDemo();
    }

}
