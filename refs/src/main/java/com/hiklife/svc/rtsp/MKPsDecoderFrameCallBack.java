package com.hiklife.svc.rtsp;

import static refs.com.hiklife.svc.PlayRtspDemo.ZLM_API;

import refs.com.aizuda.zlm4j.callback.IMKPsDecoderFrameCallBack;
import refs.com.aizuda.zlm4j.structure.MK_MEDIA;
import refs.com.sun.jna.CallbackThreadInitializer;
import refs.com.sun.jna.Native;
import refs.com.sun.jna.Pointer;

public class MKPsDecoderFrameCallBack implements IMKPsDecoderFrameCallBack {
    private MK_MEDIA mkMedia;
    private Boolean enableAudio;

    public MKPsDecoderFrameCallBack(MK_MEDIA mkMedia, Boolean enableAudio) {
        this.mkMedia = mkMedia;
        this.enableAudio = enableAudio;
        Native.setCallbackThreadInitializer(this, new CallbackThreadInitializer(false, false, "MKPsDecoderFrameCallBack"));
    }

    @Override
    public void invoke(Pointer user_data, int stream, int codecid, int flags, long pts, long dts, Pointer data, long bytes) {
        switch (codecid) {
            case 0: //H264
                ZLM_API.mk_media_input_h264(mkMedia, data, (int) bytes, dts, pts);
                break;
            case 1: //H265
                ZLM_API.mk_media_input_h264(mkMedia, data, (int) bytes, dts, pts);
                break;
            case 2: //aac
                if (enableAudio) {
                    ZLM_API.mk_media_input_aac(mkMedia, data, (int) bytes, dts, null);
                }
                break;
            case 3: // pcma
                if (enableAudio) {
                    ZLM_API.mk_media_input_audio(mkMedia, data, (int) bytes, dts);
                }
                break;
            case 4: //pcmu
                if (enableAudio) {
                    ZLM_API.mk_media_input_audio(mkMedia, data, (int) bytes, dts);
                }
                break;
            case 5: //opus
                if (enableAudio) {
                    ZLM_API.mk_media_input_audio(mkMedia, data, (int) bytes, dts);
                }
                break;
        }
        if (codecid == 0) {

        }
        Native.detach(false);
    }

    /**
     * 关闭资源
     */
    public void release() {
        ZLM_API.mk_media_release(mkMedia);
    }
}
