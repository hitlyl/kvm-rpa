package com.hiklife.svc.rtsp;

import static refs.com.hiklife.svc.PlayRtspDemo.ZLM_API;

import refs.com.aizuda.zlm4j.structure.MK_MEDIA;
import refs.com.hiklife.svc.console.KVMCRealRawCallBack;
import refs.com.hiklife.svc.core.protocol.normal.decoder.EncodingType;
import refs.com.sun.jna.Memory;

public class FRealDataCallbackForPsEncode implements KVMCRealRawCallBack {
    private final MK_MEDIA mkMedia;
    private long frameCount = 0;
    private final double frameInterval = 1000.0 / 30.0; // 30fps

    public FRealDataCallbackForPsEncode(MK_MEDIA mkMedia) {
        this.mkMedia = mkMedia;
    }
    @Override
    public void invoke(byte[] bytes, EncodingType encodingType) {
        new Thread(new Runnable() {
            @Override
            public void run() {
                Memory memory = new Memory(bytes.length);
                memory.write(0, bytes, 0, bytes.length);
                // 计算时间戳（从0开始，单位毫秒）
                long timestamp = (long) (frameCount * frameInterval);
                frameCount++;
                ZLM_API.mk_media_input_h264(mkMedia, memory, bytes.length, timestamp, timestamp);
            }
        }).start();
    }
}
