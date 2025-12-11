/*     */ package com.hiklife.svc.core.protocol.normal.decoder;
/*     */ 
/*     */ import org.bytedeco.ffmpeg.avcodec.AVCodec;
/*     */ import org.bytedeco.ffmpeg.avcodec.AVCodecContext;
/*     */ import org.bytedeco.ffmpeg.avcodec.AVPacket;
/*     */ import org.bytedeco.ffmpeg.avutil.AVDictionary;
/*     */ import org.bytedeco.ffmpeg.avutil.AVFrame;
/*     */ import org.bytedeco.ffmpeg.global.avcodec;
/*     */ import org.bytedeco.ffmpeg.global.avutil;
/*     */ import org.bytedeco.javacpp.BytePointer;
/*     */ import org.slf4j.Logger;
/*     */ import org.slf4j.LoggerFactory;

import refs.com.hiklife.svc.core.protocol.normal.decoder.FFmpegDecoder;
import refs.com.hiklife.svc.core.protocol.normal.decoder.FFmpegG726Decoder;
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ public class FFmpegG726Decoder
/*     */   extends FFmpegDecoder
/*     */ {
/*  25 */   private static final Logger log = LoggerFactory.getLogger(FFmpegG726Decoder.class);
/*     */   
/*     */   private static final int CHANNELS = 1;
/*     */   
/*     */   private static final int BITS_PER_CODED_SAMPLE = 5;
/*     */   private static final int SAMPLE_RATE = 8000;
/*     */   private boolean isDestroy = false;
/*     */   
/*     */   public FFmpegG726Decoder() {
/*     */     try {
/*  35 */       init();
/*  36 */     } catch (Exception e) {
/*  37 */       log.error(e.toString());
/*     */     } 
/*     */   }
/*     */   
/*     */   private boolean isDecode = false;
/*     */   private boolean cantDecode = false;
/*     */   private AVCodecContext avContext;
/*     */   private AVFrame avFrame;
/*     */   private AVPacket avPacket;
/*     */   
/*     */   protected void init() throws FFmpegDecoder.FFmpegException {
/*  48 */     AVCodec avCodec = avcodec.avcodec_find_decoder(69643);
/*  49 */     if (avCodec == null) {
/*  50 */       throw new FFmpegDecoder.FFmpegException("Failed to load AV_CODEC_ID_ADPCM_G726");
/*     */     }
/*  52 */     this.avContext = avcodec.avcodec_alloc_context3(avCodec);
/*  53 */     if (this.avContext == null) {
/*  54 */       throw new FFmpegDecoder.FFmpegException("Failed to load avContext");
/*     */     }
/*  56 */     this.avContext.channels(1);
/*  57 */     this.avContext.bits_per_coded_sample(5);
/*  58 */     this.avContext.sample_rate(8000);
/*  59 */     this.avContext.sample_fmt(1);
/*  60 */     this.avContext.codec_type(1);
/*     */     
/*  62 */     AVDictionary options = new AVDictionary(null);
/*  63 */     if (avcodec.avcodec_open2(this.avContext, avCodec, options) < 0) {
/*  64 */       throw new FFmpegDecoder.FFmpegException("Failed to avcodec_open2");
/*     */     }
/*     */     
/*  67 */     this.avFrame = avutil.av_frame_alloc();
/*  68 */     if (this.avFrame == null) {
/*  69 */       throw new FFmpegDecoder.FFmpegException("Failed to load avFrame");
/*     */     }
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void destroy() {
/*  80 */     if (!this.isDecode) {
/*  81 */       this.cantDecode = true;
/*  82 */       avcodec.avcodec_close(this.avContext);
/*  83 */       avutil.av_frame_free(this.avFrame);
/*  84 */       avcodec.av_packet_free(this.avPacket);
/*     */     } else {
/*  86 */       this.isDestroy = true;
/*     */     } 
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   protected void finalize() throws Throwable {
/*  99 */     super.finalize();
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void decode(byte[] bytes, FFmpegDecoder.Event event) {
/* 110 */     if (this.cantDecode) {
/*     */       return;
/*     */     }
/* 113 */     this.isDecode = true;
/* 114 */     this.avPacket = avcodec.av_packet_alloc();
/* 115 */     avcodec.av_new_packet(this.avPacket, bytes.length);
/* 116 */     BytePointer pointer = new BytePointer(bytes);
/* 117 */     this.avPacket.data(pointer);
/*     */     
/* 119 */     int len = avcodec.avcodec_send_packet(this.avContext, this.avPacket);
/* 120 */     if (len < 0) {
/*     */       return;
/*     */     }
/* 123 */     while (avcodec.avcodec_receive_frame(this.avContext, this.avFrame) == 0) {
/* 124 */       if (event != null) {
/* 125 */         event.onDecodeFrame(this.avFrame);
/*     */       }
/*     */     } 
/* 128 */     avcodec.av_packet_free(this.avPacket);
/*     */     
/* 130 */     if (this.isDestroy) {
/* 131 */       avcodec.avcodec_close(this.avContext);
/* 132 */       avutil.av_frame_free(this.avFrame);
/* 133 */       avcodec.av_packet_free(this.avPacket);
/*     */     } 
/* 135 */     this.isDecode = false;
/*     */   }
/*     */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/core/protocol/normal/decoder/FFmpegG726Decoder.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */