/*     */ package com.hiklife.svc.core.protocol.normal;
/*     */ import org.slf4j.Logger;
/*     */ import org.slf4j.LoggerFactory;

import refs.com.hiklife.svc.core.protocol.initialisation.ImageInfo;
import refs.com.hiklife.svc.core.protocol.normal.VideoFramePacket;
import refs.com.hiklife.svc.core.protocol.normal.decoder.EncodingType;
import refs.com.hiklife.svc.core.protocol.normal.decoder.FFmpegDecoder;
import refs.com.hiklife.svc.core.protocol.normal.decoder.FFmpegVideoDecoder;
import refs.com.hiklife.svc.util.HexUtils;
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ public class VideoFramePacket
/*     */ {
/*  17 */   private static final Logger log = LoggerFactory.getLogger(VideoFramePacket.class);
/*     */   
/*     */   public static final int HEAD_LENGTH = 4;
/*     */   
/*     */   public static final int IMAGE_SIZE_CHANGE_LENGTH = 16;
/*     */   
/*     */   public static final int FRAME_MIN_LENGTH = 20;
/*     */   
/*     */   public boolean resolutionIsChange;
/*     */   
/*     */   private ImageInfo imageInfo;
/*     */   public int IEncodingType;
/*     */   private final FFmpegDecoder.Event decoderEvent;
/*     */   public FFmpegVideoDecoder fFmpegVideoDecoder;
/*     */   
/*     */   public VideoFramePacket(FFmpegDecoder.Event event) {
/*  33 */     this.decoderEvent = event;
/*  34 */     this.imageInfo = new ImageInfo();
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public static int length01(byte[] orgMsgBytes) {
/*  44 */     if (isImageSizeChangeMsg(orgMsgBytes)) {
/*  45 */       return 16;
/*     */     }
/*  47 */     int imageSize = HexUtils.registersToInt(orgMsgBytes, 16);
/*  48 */     return imageSize + 20;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public static int length02(byte[] orgMsgBytes) {
/*  59 */     int imageSize = HexUtils.registersToInt(orgMsgBytes, 16);
/*  60 */     return imageSize + 20 + 12;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   private static boolean isImageSizeChangeMsg(byte[] orgMsgBytes) {
/*  70 */     return (orgMsgBytes[15] == 33 && orgMsgBytes[14] == -1 && orgMsgBytes[13] == -1 && orgMsgBytes[12] == -1);
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
/*     */ 
/*     */   
/*     */   private static int getEncodingType(byte[] orgMsgBytes, int off) {
/*  84 */     return orgMsgBytes[off + 3];
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   private void parseImageInfo(byte[] orgMsgBytes) {
/*  93 */     int width = HexUtils.registerToShort(orgMsgBytes, 0);
/*  94 */     int height = HexUtils.registerToShort(orgMsgBytes, 2);
/*  95 */     if (this.imageInfo.getHeight() != height || this.imageInfo.getWidth() != width) {
/*  96 */       this.imageInfo.setWidth(width);
/*  97 */       this.imageInfo.setHeight(height);
/*  98 */       this.resolutionIsChange = true;
/*     */     } 
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   private void parseImageStream(byte[] orgMsgBytes) {
/* 109 */     this.imageInfo.setWidth(HexUtils.registerToShort(orgMsgBytes, 8));
/* 110 */     this.imageInfo.setHeight(HexUtils.registerToShort(orgMsgBytes, 10));
/* 111 */     int encodingType = getEncodingType(orgMsgBytes, 12);
/* 112 */     EncodingType type = EncodingType.parse(encodingType);
/* 113 */     this.IEncodingType = orgMsgBytes[14];
/* 114 */     int imageSize = HexUtils.registersToInt(orgMsgBytes, 16);
/* 115 */     byte[] bytes = new byte[imageSize];
/* 116 */     System.arraycopy(orgMsgBytes, 20, bytes, 0, imageSize);
/* 117 */     this.resolutionIsChange = false;
/* 118 */     decode(bytes, type);
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void parse(byte[] orgMsgBytes) {
/* 127 */     if (orgMsgBytes[3] == 1) {
/* 128 */       if (isImageSizeChangeMsg(orgMsgBytes)) {
/* 129 */         byte[] bytes = new byte[12];
/* 130 */         System.arraycopy(orgMsgBytes, 4, bytes, 0, 12);
/* 131 */         parseImageInfo(bytes);
/*     */       } else {
/* 133 */         parseImageStream(orgMsgBytes);
/*     */       }
/*     */     
/* 136 */     } else if (orgMsgBytes[3] == 2) {
/* 137 */       byte[] bytes = new byte[12];
/* 138 */       System.arraycopy(orgMsgBytes, HexUtils.registersToInt(orgMsgBytes, 16) + 20, bytes, 0, 12);
/* 139 */       parseImageInfo(bytes);
/* 140 */       parseImageStream(orgMsgBytes);
/*     */     } 
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   private void decode(byte[] bytes, EncodingType type) {
/* 150 */     if (this.fFmpegVideoDecoder == null) {
/* 151 */       this.fFmpegVideoDecoder = new FFmpegVideoDecoder(type);
/*     */     }
/* 153 */     if (this.decoderEvent != null) {
/* 154 */       this.decoderEvent.onDecodeVideoRawStream(bytes, type);
/*     */     }
/* 156 */     this.fFmpegVideoDecoder.decode(bytes, this.decoderEvent);
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public ImageInfo getImageInfo() {
/* 165 */     return this.imageInfo;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void setImageInfo(ImageInfo imageInfo) {
/* 174 */     this.imageInfo = imageInfo;
/*     */   }
/*     */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/core/protocol/normal/VideoFramePacket.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */