package com.hiklife.svc;

import org.bytedeco.ffmpeg.avutil.AVFrame;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.hiklife.svc.Kvm4JSdk;

import refs.com.aizuda.zlm4j.core.ZLMApi;
import refs.com.aizuda.zlm4j.structure.MK_EVENTS;
import refs.com.aizuda.zlm4j.structure.MK_INI;
import refs.com.aizuda.zlm4j.structure.MK_MEDIA;
import refs.com.hiklife.svc.console.KVMCAVFrameCallBack;
import refs.com.hiklife.svc.console.KVMCCloseCallBak;
import refs.com.hiklife.svc

import refs.src.main.java.com.hiklife.svc.PlayRtspDemo;

import refs.com.hiklife.svc.rtsp.FRealDataCallbackForPsEncode;
import refs.com.hiklife.svc.rtsp.MKLogCallBack;
import refs.com.hiklife.svc.rtsp.MKNoReaderCallBack;
import refs.com.hiklife.svc.rtsp.MKPublishCallBack;
import refs.com.sun.jna.Native;
import refs.com.sun.jna.Pointer;

public class PlayRtspDemo {
    private static final Logger log = LoggerFactory.getLogger(PlayRtspDemo.class);
    public static ZLMApi ZLM_API = Native.load("mk_api", ZLMApi.class);
    private static final short RTSP_PORT = 8554;
    private static final int SSH_ENABLE = 0;
    private static final int THREAD_NUM = 2; //线程数
    private static final int LOG_LEVEL = 1; //0：TRACE 1：DEBUG 2：INFO 3：WARN 4：ERROR
    private static final int LOG_MASK = 4; //日志输入 1：LOG_CONSOLE输出到控制台  2：LOG_FILE输入到文件 4：LOG_CALLBACK输出到回调函数
    private static final int LOG_FILE_DAYS = 0; //文件日志保存天数,设置为0关闭日志文件
    private static final int LOG_FILE_PATH = 0;  //配置文件是内容还是路径

    public void start() {
        //初始化sdk配置 SDK参数配置详见ZLM4J参数配置
        ZLM_API.mk_env_init2(THREAD_NUM, LOG_LEVEL, LOG_MASK, null,
                LOG_FILE_DAYS, LOG_FILE_PATH, null, 0, null, null);
        short rtsp_server_port = ZLM_API.mk_rtsp_server_start(RTSP_PORT, SSH_ENABLE);
        if(rtsp_server_port > 0 ){
            log.info("【MediaServer】RTSP server created success,port:{}", rtsp_server_port);
        } else {
            log.error("【MediaServer】RTSP server created error.");
            throw  new RuntimeException("【MediaServer】RTSP server created error.");
        }
        MK_INI mkIni = ZLM_API.mk_ini_create();
        ZLM_API.mk_ini_set_option(mkIni, "enable_rtsp", "1");
        ZLM_API.mk_ini_set_option(mkIni, "enable_rtmp", "0");
        ZLM_API.mk_ini_set_option(mkIni, "enable_hls", "0");
        ZLM_API.mk_ini_set_option(mkIni, "enable_ts", "0");
        ZLM_API.mk_ini_set_option(mkIni, "enable_fmp4", "0");
        ZLM_API.mk_ini_set_option_int(mkIni, "auto_close", 0);
        //#rtsp 转发是否使用低延迟模式，当开启时，不会缓存rtp包，来提高并发，可以降低一帧的延迟
        ZLM_API.mk_ini_set_option_int(mkIni, "rtsp.lowLatency", 1);
        //#rtsp拉流、推流代理是否是直接代理模式
        ZLM_API.mk_ini_set_option_int(mkIni, "rtsp.directProxy", 1);

        MK_EVENTS mk_event = new MK_EVENTS();
        mk_event.on_mk_log = new MKLogCallBack();
        mk_event.on_mk_media_no_reader = new MKNoReaderCallBack();
        mk_event.on_mk_media_publish = new MKPublishCallBack();

        //添加全局回调
        ZLM_API.mk_events_listen(mk_event);

        //创建媒体
        MK_MEDIA mkMedia = ZLM_API.mk_media_create2("__defaultVhost__", "live", "kvm", 0, mkIni);
        ZLM_API.mk_ini_release(mkIni);
        //这里分辨率、帧率、码率都可可以事先定义好 也可以放到回调里面判断编码类型让后再初始化这个 0是H264 1是h265
        ZLM_API.mk_media_init_video(mkMedia, 0, 1920, 1080, 30, 2500);
        ZLM_API.mk_media_init_complete(mkMedia);
        ZLM_API.mk_media_set_on_close(mkMedia, pointer -> {
            System.out.println("流关闭自动释放资源");
        }, Pointer.NULL);

        //-----------------------------------------------------------------------------------------------------

        // 上面是流媒体,下面是KVM
        KVMCInstance kvmcInstance = null;
        try {
            kvmcInstance = Kvm4JSdk.connectKVMC(
                    "192.168.0.100", 5900, 0, "admin", "123456", 5000);
        } catch (Exception e) {
            log.error("KVM关闭自动释放资源");
            ZLM_API.mk_media_release(mkMedia);
            ZLM_API.mk_stop_all_server();
            log.info("【MediaServer】Stop all server");
            throw new RuntimeException(e);
        }
        //裸流回调
        FRealDataCallbackForPsEncode fRealDataCallBack = new FRealDataCallbackForPsEncode(mkMedia);
        kvmcInstance.setKvmCRealRawCallBack(fRealDataCallBack);

        //图片帧回调
        kvmcInstance.setKvmCAVFrameCallBack(new KVMCAVFrameCallBack() {
            @Override
            public void invoke(AVFrame avFrame) {
                // 请使用图片帧
            }
        });
        //KVM连接断开回调
        kvmcInstance.setKvmCCloseCallBak(new KVMCCloseCallBak() {
            @Override
            public void invoke(String s) {
                System.out.println("KVM关闭自动释放资源");
                ZLM_API.mk_media_release(mkMedia);
                ZLM_API.mk_stop_all_server();
                System.exit(0);
            }
        });


        // 测试
        try {
            Thread.sleep(120000);
        } catch (InterruptedException e) {
            throw new RuntimeException(e);
        }
        // KVM关闭后会回调KVMCloseCallBak
        kvmcInstance.stopSession();
    }

    public static void main(String[] args) throws Exception {
        PlayRtspDemo server = new PlayRtspDemo();
        server.start();
    }
}
