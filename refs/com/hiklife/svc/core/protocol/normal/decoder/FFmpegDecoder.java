/*    */ package com.hiklife.svc.core.protocol.normal.decoder;
/*    */ import org.bytedeco.ffmpeg.avutil.AVFrame;
/*    */ import org.bytedeco.ffmpeg.global.avcodec;
/*    */ import org.bytedeco.ffmpeg.global.avformat;
/*    */ import org.bytedeco.ffmpeg.global.avutil;
/*    */ import org.bytedeco.ffmpeg.global.swscale;
/*    */ import org.bytedeco.javacpp.Loader;
/*    */ import org.slf4j.Logger;
/*    */ import org.slf4j.LoggerFactory;

import refs.com.hiklife.svc.core.protocol.normal.decoder.EncodingType;
import refs.com.hiklife.svc.core.protocol.normal.decoder.FFmpegDecoder;
/*    */ 
/*    */ public abstract class FFmpegDecoder {
/*    */   protected abstract void init() throws FFmpegException;
/*    */   
/*    */   public abstract void destroy();
/*    */   
/*    */   public abstract void decode(byte[] paramArrayOfbyte, Event paramEvent);
/*    */   
/* 18 */   private static final Logger log = LoggerFactory.getLogger(FFmpegDecoder.class); public static interface Event {
/*    */     void onDecodeFrame(AVFrame param1AVFrame); void onDecodeVideoRawStream(byte[] param1ArrayOfbyte, EncodingType param1EncodingType); } static {
/*    */     try {
/* 21 */       avutil.av_log_set_level(8);
/* 22 */       Loader.load(avutil.class);
/* 23 */       Loader.load(avcodec.class);
/* 24 */       Loader.load(avformat.class);
/* 25 */       Loader.load(swscale.class);
/* 26 */       avcodec.av_jni_set_java_vm(Loader.getJavaVM(), null);
/* 27 */     } catch (Throwable t) {
/* 28 */       log.error(t.toString());
/* 29 */       log.error("FFmpeg static library initialization failure");
/*    */     } 
/*    */   }
/*    */ 
/*    */   
/*    */   public static class FFmpegException
/*    */     extends Exception
/*    */   {
/*    */     public FFmpegException(String msg) {
/* 38 */       super(msg);
/*    */     }
/*    */     
/*    */     public FFmpegException() {}
/*    */   }
/*    */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/core/protocol/normal/decoder/FFmpegDecoder.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */