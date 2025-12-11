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

import refs.com.hiklife.svc.core.protocol.normal.decoder.EncodingType;
import refs.com.hiklife.svc.core.protocol.normal.decoder.FFmpegDecoder;
import refs.com.hiklife.svc.core.protocol.normal.decoder.FFmpegVideoDecoder;
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
/*     */ public class FFmpegVideoDecoder
/*     */   extends FFmpegDecoder
/*     */ {
/*  29 */   private static final Logger log = LoggerFactory.getLogger(FFmpegVideoDecoder.class);
/*     */   
/*     */   private final EncodingType encodingType;
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
/*     */   public FFmpegVideoDecoder(EncodingType type) {
/*  55 */     this.encodingType = type;
/*     */     try {
/*  57 */       init();
/*  58 */     } catch (Exception e) {
/*  59 */       log.error(e.toString());
/*     */     } 
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void init() throws FFmpegDecoder.FFmpegException {
/*  69 */     int decoder = 0;
/*  70 */     switch (this.encodingType) {
/*     */       case H264:
/*  72 */         decoder = 27;
/*     */         break;
/*     */       case H265:
/*  75 */         decoder = 173;
/*     */         break;
/*     */       default:
/*  78 */         log.error("不支持该视频编码方式：{}", this.encodingType);
/*     */         return;
/*     */     } 
/*     */     
/*  82 */     AVCodec avCodec = avcodec.avcodec_find_decoder(decoder);
/*  83 */     if (avCodec == null) {
/*  84 */       throw new FFmpegDecoder.FFmpegException("Failed to load " + this.encodingType);
/*     */     }
/*  86 */     this.avContext = avcodec.avcodec_alloc_context3(avCodec);
/*  87 */     if (this.avContext == null) {
/*  88 */       throw new FFmpegDecoder.FFmpegException("Failed to load avContext");
/*     */     }
/*  90 */     AVDictionary options = new AVDictionary(null);
/*  91 */     if (avcodec.avcodec_open2(this.avContext, avCodec, options) < 0) {
/*  92 */       throw new FFmpegDecoder.FFmpegException("Failed to avcodec_open2");
/*     */     }
/*  94 */     this.avFrame = avutil.av_frame_alloc();
/*  95 */     if (this.avFrame == null) {
/*  96 */       throw new FFmpegDecoder.FFmpegException("Failed to load avFrame");
/*     */     }
/*  98 */     this.avFrameBGR = avutil.av_frame_alloc();
/*  99 */     if (this.avFrameBGR == null) {
/* 100 */       throw new FFmpegDecoder.FFmpegException("Failed to load avFrameBGR");
/*     */     }
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   protected void finalize() throws Throwable {
/* 109 */     super.finalize();
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void destroy() {
/* 118 */     if (!this.isDecode) {
/* 119 */       this.cantDecode = true;
/* 120 */       avcodec.avcodec_close(this.avContext);
/* 121 */       swscale.sws_freeContext(this.imgConvertCtx);
/* 122 */       avutil.av_frame_free(this.avFrame);
/*     */       
/* 124 */       if (this.avFrameBGR != null) {
/* 125 */         avutil.av_frame_free(this.avFrameBGR);
/*     */       }
/* 127 */       if (this.outBuffer != null) {
/* 128 */         avutil.av_free(this.outBuffer);
/*     */       }
/* 130 */       avcodec.av_packet_free(this.avPacket);
/*     */     } else {
/* 132 */       this.isDestroy = true;
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
/* 143 */     if (this.cantDecode) {
/*     */       return;
/*     */     }
/* 146 */     this.isDecode = true;
/* 147 */     this.avPacket = avcodec.av_packet_alloc();
/* 148 */     avcodec.av_new_packet(this.avPacket, bytes.length);
/* 149 */     BytePointer pointer = new BytePointer(bytes);
/* 150 */     this.avPacket.data(pointer);
/*     */     
/* 152 */     int len = avcodec.avcodec_send_packet(this.avContext, this.avPacket);
/* 153 */     if (len < 0) {
/*     */       return;
/*     */     }
/* 156 */     while (avcodec.avcodec_receive_frame(this.avContext, this.avFrame) == 0) {
/* 157 */       if (this.imgConvertCtx == null) {
/* 158 */         newImgConvertCtx();
/* 159 */       } else if (this.avContext.width() != this.lastWidth || this.avContext.height() != this.lastHeight) {
/* 160 */         changeImgConvertCtx();
/*     */       } 
/* 162 */       swscale.sws_scale(this.imgConvertCtx, this.avFrame.data(), this.avFrame.linesize(), 0, this.avContext
/* 163 */           .height(), this.avFrameBGR.data(), this.avFrameBGR.linesize());
/* 164 */       this.avFrameBGR.width(this.avContext.width());
/* 165 */       this.avFrameBGR.height(this.avContext.height());
/* 166 */       if (event != null) {
/* 167 */         event.onDecodeFrame(this.avFrameBGR);
/*     */       }
/*     */     } 
/* 170 */     avcodec.av_packet_free(this.avPacket);
/* 171 */     pointer = null;
/*     */     
/* 173 */     if (this.isDestroy) {
/* 174 */       avcodec.avcodec_close(this.avContext);
/* 175 */       swscale.sws_freeContext(this.imgConvertCtx);
/* 176 */       avutil.av_frame_free(this.avFrame);
/*     */       
/* 178 */       if (this.avFrameBGR != null) {
/* 179 */         avutil.av_frame_free(this.avFrameBGR);
/*     */       }
/* 181 */       if (this.outBuffer != null) {
/* 182 */         avutil.av_free(this.outBuffer);
/*     */       }
/* 184 */       avcodec.av_packet_free(this.avPacket);
/*     */     } 
/* 186 */     this.isDecode = false;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   private void newImgConvertCtx() {
/* 193 */     int avBGRsize = avutil.av_image_get_buffer_size(3, this.avContext.width(), this.avContext.height(), 1);
/* 194 */     this.lastWidth = this.avContext.width();
/* 195 */     this.lastHeight = this.avContext.height();
/* 196 */     if (this.outBuffer != null) {
/* 197 */       avutil.av_free(this.outBuffer);
/*     */     }
/* 199 */     this.outBuffer = avutil.av_malloc(avBGRsize);
/* 200 */     avutil.av_frame_free(this.avFrameBGR);
/* 201 */     this.avFrameBGR = avutil.av_frame_alloc();
/* 202 */     avutil.av_image_fill_arrays(this.avFrameBGR
/* 203 */         .data(), this.avFrameBGR
/* 204 */         .linesize(), new BytePointer(this.outBuffer), 3, this.avContext
/*     */ 
/*     */         
/* 207 */         .width(), this.avContext
/* 208 */         .height(), 1);
/*     */     
/* 210 */     if (this.imgConvertCtx != null) {
/* 211 */       swscale.sws_freeContext(this.imgConvertCtx);
/*     */     }
/* 213 */     this.imgConvertCtx = swscale.sws_getContext(this.avContext.width(), this.avContext.height(), this.avContext.pix_fmt(), this.avContext
/* 214 */         .width(), this.avContext.height(), 3, 2, null, null, (double[])null);
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   private void changeImgConvertCtx() {
/* 221 */     newImgConvertCtx();
/*     */   }
/*     */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/core/protocol/normal/decoder/FFmpegVideoDecoder.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */