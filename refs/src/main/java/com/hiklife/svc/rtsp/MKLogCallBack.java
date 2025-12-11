package com.hiklife.svc.rtsp;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;


import refs.src.main.java.com.hiklife.svc.rtsp.MKLogCallBack;

import refs.com.aizuda.zlm4j.callback.IMKLogCallBack;
import refs.com.sun.jna.CallbackThreadInitializer;
import refs.com.sun.jna.Native;

public class MKLogCallBack implements IMKLogCallBack {
    private static final Logger log = LoggerFactory.getLogger(MKLogCallBack.class);
    public MKLogCallBack() {
        Native.setCallbackThreadInitializer(this, new CallbackThreadInitializer(true, false,"MediaLogThread"));
    }
    /**
     * 日志输出广播
     *
     * @param level    日志级别
     * @param file     源文件名
     * @param line     源文件行
     * @param function 源文件函数名
     * @param message  日志内容
     */
    @Override
    public void invoke(int level, String file, int line, String function, String message) {
        switch (level) {
            case 0:
                log.trace("【MediaServer】{}", message);
                break;
            case 1:
                log.debug("【MediaServer】{}", message);
                break;
            case 2:
                log.info("【MediaServer】{}", message);
                break;
            case 3:
                log.warn("【MediaServer】{}", message);
                break;
            case 4:
                log.error("【MediaServer】{}", message);
                break;
            default:
                log.info("【MediaServer】{}", message);
                break;
        }
    }
}
