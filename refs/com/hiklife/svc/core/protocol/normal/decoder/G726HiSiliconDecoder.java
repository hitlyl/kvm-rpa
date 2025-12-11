/*    */ package com.hiklife.svc.core.protocol.normal.decoder;
/*    */ 
/*    */ import org.bytedeco.ffmpeg.avutil.AVFrame;
/*    */ import org.slf4j.Logger;
/*    */ import org.slf4j.LoggerFactory;

import refs.com.hiklife.svc.core.protocol.normal.decoder.EncodingType;
import refs.com.hiklife.svc.core.protocol.normal.decoder.FFmpegDecoder;
import refs.com.hiklife.svc.core.protocol.normal.decoder.FFmpegG726Decoder;
import refs.com.hiklife.svc.core.protocol.normal.decoder.G726Decoder;
import refs.com.hiklife.svc.core.protocol.normal.decoder.G726HiSiliconDecoder;
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ public class G726HiSiliconDecoder
/*    */   extends G726Decoder
/*    */ {
/* 14 */   private static final Logger log = LoggerFactory.getLogger(G726HiSiliconDecoder.class);
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/* 21 */   private final FFmpegG726Decoder fFmpegG726Decoder = new FFmpegG726Decoder();
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public void decode(byte[] bytes, final G726Decoder.Event event) {
/* 31 */     this.fFmpegG726Decoder.decode(bytes, new FFmpegDecoder.Event()
/*    */         {
/*    */           public void onDecodeFrame(AVFrame avFrame) {
/* 34 */             if (event != null) {
/* 35 */               byte[] des = new byte[avFrame.linesize(0)];
/* 36 */               avFrame.data(0).get(des);
/* 37 */               event.onAudioDecodeFrame(des);
/*    */             } 
/*    */           }
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */           
/*    */           public void onDecodeVideoRawStream(byte[] bytes, EncodingType type) {}
/*    */         });
/*    */   }
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public void destroy() {
/* 53 */     log.debug("fFmpegG726Decoder is to destroy");
/* 54 */     this.fFmpegG726Decoder.destroy();
/*    */   }
/*    */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/core/protocol/normal/decoder/G726HiSiliconDecoder.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */