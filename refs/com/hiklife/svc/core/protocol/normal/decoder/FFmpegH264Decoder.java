/*     */ package com.hiklife.svc.core.protocol.normal.decoder;
/*     */ 
/*     */ import org.bytedeco.ffmpeg.avcodec.AVCodec;
/*     */ import org.bytedeco.ffmpeg.avcodec.AVCodecContext;
/*     */ import org.bytedeco.ffmpeg.avcodec.AVPacket;
/*     */ import org.bytedeco.ffmpeg.avutil.AVDictionary;
/*     */ import org.bytedeco.ffmpeg.avutil.AVFrame;
/*     */ import org.bytedeco.ffmpeg.global.avcodec;
/*     */ import org.bytedeco.ffmpeg.global.avutil;
/*     */ import org.bytedeco.ffmpeg.global.swscale;
/*     */ import org.bytedeco.ffmpeg.swscale.SwsContext;
/*     */ import org.bytedeco.javacpp.BytePointer;
/*     */ import org.bytedeco.javacpp.Pointer;
/*     */ import org.slf4j.Logger;
/*     */ import org.slf4j.LoggerFactory;

import refs.com.hiklife.svc.core.protocol.normal.decoder.FFmpegDecoder;
import refs.com.hiklife.svc.core.protocol.normal.decoder.FFmpegH264Decoder;
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ @Deprecated
/*     */ public class FFmpegH264Decoder
/*     */   extends FFmpegDecoder
/*     */ {
/*  30 */   private static final Logger log = LoggerFactory.getLogger(FFmpegH264Decoder.class);
/*     */   
/*     */   private static final int SWS_ALGORITHM = 2;
/*     */   
/*     */   private static final int RGB24 = 3;
/*     */   
/*     */   private boolean isDestroy = false;
/*     */   
/*     */   private boolean isDecode = false;
/*     */   
/*     */   private boolean cantDecode = false;
/*     */   
/*     */   private AVCodecContext avContext;
/*     */   
/*     */   private AVFrame avFrame;
/*     */   
/*     */   private AVPacket avPacket;
/*     */   private AVFrame avFrameBGR;
/*     */   private SwsContext imgConvertCtx;
/*     */   private Pointer outBuffer;
/*     */   private int lastWidth;
/*     */   private int lastHeight;
/*     */   
/*     */   public FFmpegH264Decoder() {
/*     */     try {
/*  55 */       init();
/*  56 */     } catch (Exception e) {
/*  57 */       log.error(e.toString());
/*     */     } 
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void init() throws FFmpegDecoder.FFmpegException {
/*  67 */     AVCodec avCodec = avcodec.avcodec_find_decoder(27);
/*  68 */     if (avCodec == null) {
/*  69 */       throw new FFmpegDecoder.FFmpegException("Failed to load AV_CODEC_ID_H264");
/*     */     }
/*  71 */     this.avContext = avcodec.avcodec_alloc_context3(avCodec);
/*  72 */     if (this.avContext == null) {
/*  73 */       throw new FFmpegDecoder.FFmpegException("Failed to load avContext");
/*     */     }
/*  75 */     AVDictionary options = new AVDictionary(null);
/*  76 */     if (avcodec.avcodec_open2(this.avContext, avCodec, options) < 0) {
/*  77 */       throw new FFmpegDecoder.FFmpegException("Failed to avcodec_open2");
/*     */     }
/*  79 */     this.avFrame = avutil.av_frame_alloc();
/*  80 */     if (this.avFrame == null) {
/*  81 */       throw new FFmpegDecoder.FFmpegException("Failed to load avFrame");
/*     */     }
/*  83 */     this.avFrameBGR = avutil.av_frame_alloc();
/*  84 */     if (this.avFrameBGR == null) {
/*  85 */       throw new FFmpegDecoder.FFmpegException("Failed to load avFrameBGR");
/*     */     }
/*     */   }
/*     */   
/*     */   protected void finalize() throws Throwable {
/*  90 */     super.finalize();
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void destroy() {
/*  99 */     if (!this.isDecode) {
/* 100 */       this.cantDecode = true;
/* 101 */       avcodec.avcodec_close(this.avContext);
/* 102 */       swscale.sws_freeContext(this.imgConvertCtx);
/* 103 */       avutil.av_frame_free(this.avFrame);
/*     */       
/* 105 */       if (this.avFrameBGR != null) {
/* 106 */         avutil.av_frame_free(this.avFrameBGR);
/*     */       }
/* 108 */       if (this.outBuffer != null) {
/* 109 */         avutil.av_free(this.outBuffer);
/*     */       }
/* 111 */       avcodec.av_packet_free(this.avPacket);
/*     */     } else {
/* 113 */       this.isDestroy = true;
/*     */     } 
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void decode(byte[] bytes, FFmpegDecoder.Event event) {
/* 124 */     if (this.cantDecode) {
/*     */       return;
/*     */     }
/* 127 */     this.isDecode = true;
/* 128 */     this.avPacket = avcodec.av_packet_alloc();
/* 129 */     avcodec.av_new_packet(this.avPacket, bytes.length);
/* 130 */     BytePointer pointer = new BytePointer(bytes);
/* 131 */     this.avPacket.data(pointer);
/*     */     
/* 133 */     int len = avcodec.avcodec_send_packet(this.avContext, this.avPacket);
/* 134 */     if (len < 0) {
/*     */       return;
/*     */     }
/* 137 */     while (avcodec.avcodec_receive_frame(this.avContext, this.avFrame) == 0) {
/* 138 */       if (this.imgConvertCtx == null) {
/* 139 */         newImgConvertCtx();
/* 140 */       } else if (this.avContext.width() != this.lastWidth || this.avContext.height() != this.lastHeight) {
/* 141 */         changeImgConvertCtx();
/*     */       } 
/* 143 */       swscale.sws_scale(this.imgConvertCtx, this.avFrame.data(), this.avFrame.linesize(), 0, this.avContext
/* 144 */           .height(), this.avFrameBGR.data(), this.avFrameBGR.linesize());
/* 145 */       this.avFrameBGR.width(this.avContext.width());
/* 146 */       this.avFrameBGR.height(this.avContext.height());
/* 147 */       if (event != null) {
/* 148 */         event.onDecodeFrame(this.avFrameBGR);
/*     */       }
/*     */     } 
/* 151 */     avcodec.av_packet_free(this.avPacket);
/* 152 */     pointer = null;
/*     */     
/* 154 */     if (this.isDestroy) {
/* 155 */       avcodec.avcodec_close(this.avContext);
/* 156 */       swscale.sws_freeContext(this.imgConvertCtx);
/* 157 */       avutil.av_frame_free(this.avFrame);
/*     */       
/* 159 */       if (this.avFrameBGR != null) {
/* 160 */         avutil.av_frame_free(this.avFrameBGR);
/*     */       }
/* 162 */       if (this.outBuffer != null) {
/* 163 */         avutil.av_free(this.outBuffer);
/*     */       }
/* 165 */       avcodec.av_packet_free(this.avPacket);
/*     */     } 
/* 167 */     this.isDecode = false;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   private void newImgConvertCtx() {
/* 174 */     int avBGRsize = avutil.av_image_get_buffer_size(3, this.avContext.width(), this.avContext.height(), 1);
/* 175 */     this.lastWidth = this.avContext.width();
/* 176 */     this.lastHeight = this.avContext.height();
/* 177 */     if (this.outBuffer != null) {
/* 178 */       avutil.av_free(this.outBuffer);
/*     */     }
/* 180 */     this.outBuffer = avutil.av_malloc(avBGRsize);
/* 181 */     avutil.av_frame_free(this.avFrameBGR);
/* 182 */     this.avFrameBGR = avutil.av_frame_alloc();
/* 183 */     avutil.av_image_fill_arrays(this.avFrameBGR
/* 184 */         .data(), this.avFrameBGR
/* 185 */         .linesize(), new BytePointer(this.outBuffer), 3, this.avContext
/*     */ 
/*     */         
/* 188 */         .width(), this.avContext
/* 189 */         .height(), 1);
/*     */     
/* 191 */     if (this.imgConvertCtx != null) {
/* 192 */       swscale.sws_freeContext(this.imgConvertCtx);
/*     */     }
/* 194 */     this.imgConvertCtx = swscale.sws_getContext(this.avContext.width(), this.avContext.height(), this.avContext.pix_fmt(), this.avContext
/* 195 */         .width(), this.avContext.height(), 3, 2, null, null, (double[])null);
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   private void changeImgConvertCtx() {
/* 202 */     newImgConvertCtx();
/*     */   }
/*     */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/core/protocol/normal/decoder/FFmpegH264Decoder.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */