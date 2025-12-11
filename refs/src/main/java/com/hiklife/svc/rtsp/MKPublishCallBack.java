package com.hiklife.svc.rtsp;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import refs.com.aizuda.zlm4j.callback.IMKPublishCallBack;
import refs.com.aizuda.zlm4j.core.ZLMApi;
import refs.com.aizuda.zlm4j.structure.MK_INI;
import refs.com.aizuda.zlm4j.structure.MK_MEDIA_INFO;
import refs.com.aizuda.zlm4j.structure.MK_PUBLISH_AUTH_INVOKER;
import refs.com.aizuda.zlm

import refs.src.main.java.com.hiklife.svc.rtsp.MKPublishCallBack;

import refs.com.hiklife.svc.PlayRtspDemo;
import refs.com.sun.jna.CallbackThreadInitializer;
import refs.com.sun.jna.Native;

public class MKPublishCallBack implements IMKPublishCallBack {
    private static final Logger log = LoggerFactory.getLogger(MKPublishCallBack.class);
    public MKPublishCallBack() {
        //回调使用同一个线程
        Native.setCallbackThreadInitializer(this, new CallbackThreadInitializer(true, false, "MediaPublishThread"));
    }
    /**
     * 收到rtsp/rtmp推流事件广播，通过该事件控制推流鉴权
     *
     * @param url_info 推流url相关信息
     * @param invoker  执行invoker返回鉴权结果
     * @param sender   该tcp客户端相关信息
     */
    @Override
    public void invoke(MK_MEDIA_INFO url_info, MK_PUBLISH_AUTH_INVOKER invoker, MK_SOCK_INFO sender) {
        ZLMApi ZLM_API = PlayRtspDemo.ZLM_API;
        //通过ZLM_API.mk_media_info_get_*可以查询流的各种信息
        String app = ZLM_API.mk_media_info_get_app(url_info);
        String stream = ZLM_API.mk_media_info_get_stream(url_info);
        String schema = ZLM_API.mk_media_info_get_schema(url_info);
        String host = ZLM_API.mk_media_info_get_host(url_info);
        int port = ZLM_API.mk_media_info_get_port(url_info);

        log.info("MKPublishCallBack {}://{}:{}/{}/{}",schema,host,port,app, stream );
        String param = ZLM_API.mk_media_info_get_params(url_info);
        MK_INI option = ZLM_API.mk_ini_create();
        ZLM_API.mk_ini_set_option_int(option, "enable_mp4", 0);
        ZLM_API.mk_ini_set_option_int(option, "enable_audio", 0);
        ZLM_API.mk_ini_set_option_int(option, "enable_fmp4",0);
        ZLM_API.mk_ini_set_option_int(option, "enable_ts", 0);
        ZLM_API.mk_ini_set_option_int(option, "enable_hls",0);
        ZLM_API.mk_ini_set_option_int(option, "enable_rtsp", 1);
        ZLM_API.mk_ini_set_option_int(option, "enable_rtmp", 0);
        ZLM_API.mk_ini_set_option_int(option, "auto_close", 0);
//        ZLM_API.mk_ini_set_option_int(option, "mp4_max_second", 360);
        ZLM_API.mk_publish_auth_invoker_do2(invoker, "", option);
        ZLM_API.mk_ini_release(option);
    }
}
