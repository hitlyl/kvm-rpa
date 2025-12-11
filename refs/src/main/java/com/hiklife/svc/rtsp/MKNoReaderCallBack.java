package com.hiklife.svc.rtsp;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import refs.com.aizuda.zlm4j.callback.IMKNoReaderCallBack;
import refs.com.aizuda.zlm4j.core.ZLMApi;
import refs.com.aizuda.zlm

import refs.src.main.java.com.hiklife.svc.rtsp.MKNoReaderCallBack;

import refs.com.hiklife.svc.PlayRtspDemo;
import refs.com.sun.jna.CallbackThreadInitializer;
import refs.com.sun.jna.Native;


public class MKNoReaderCallBack implements IMKNoReaderCallBack {
    private static final Logger log = LoggerFactory.getLogger(MKNoReaderCallBack.class);
    public MKNoReaderCallBack() {
        Native.setCallbackThreadInitializer(this, new CallbackThreadInitializer(true, false,"MediaNoReaderThread"));
    }
    /**
     * 某个流无人消费时触发，目的为了实现无人观看时主动断开拉流等业务逻辑
     *
     * @param ctx 该MediaSource对象
     */
    @Override
    public void invoke(MK_MEDIA_SOURCE ctx) {
        ZLMApi ZLM_API = PlayRtspDemo.ZLM_API;
        String appValue = ZLM_API.mk_media_source_get_app(ctx);
        String streamValue = ZLM_API.mk_media_source_get_stream(ctx);
        String schemaValue = ZLM_API.mk_media_source_get_schema(ctx);
        log.info("onMediaNoReader:{}/{}/{}", appValue, streamValue, schemaValue);
    }
}
