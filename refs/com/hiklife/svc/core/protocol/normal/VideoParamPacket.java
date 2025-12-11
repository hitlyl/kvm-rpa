/*     */ package com.hiklife.svc.core.protocol.normal;
/*     */ import org.slf4j.Logger;
/*     */ import org.slf4j.LoggerFactory;

import refs.com.hiklife.svc.core.protocol.normal.VideoParamPacket;
import refs.com.hiklife.svc.core.protocol.normal.WriteNormalType;
import refs.com.hiklife.svc.util.HexUtils;
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
/*     */ public class VideoParamPacket
/*     */ {
/*  19 */   private static final Logger log = LoggerFactory.getLogger(VideoParamPacket.class);
/*     */ 
/*     */   
/*     */   public static final int LENGTH = 36;
/*     */ 
/*     */   
/*     */   private int brightness;
/*     */ 
/*     */   
/*     */   private int contrast;
/*     */ 
/*     */   
/*     */   private int verticalShift;
/*     */ 
/*     */   
/*     */   private int horizontalShift;
/*     */ 
/*     */   
/*     */   private int phase;
/*     */   
/*     */   private int pvq;
/*     */ 
/*     */   
/*     */   public VideoParamPacket(byte[] orgMsgBytes) {
/*  43 */     this.brightness = HexUtils.registersToInt(orgMsgBytes, 4);
/*  44 */     this.contrast = HexUtils.registersToInt(orgMsgBytes, 8);
/*  45 */     this.verticalShift = HexUtils.registersToInt(orgMsgBytes, 12);
/*  46 */     this.horizontalShift = HexUtils.registersToInt(orgMsgBytes, 16);
/*  47 */     this.phase = HexUtils.registersToInt(orgMsgBytes, 28);
/*  48 */     this.pvq = HexUtils.registersToInt(orgMsgBytes, 32);
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
/*     */   public VideoParamPacket(int brightness, int contrast, int verticalShift, int horizontalShift, int phase, int pvq) {
/*  62 */     this.brightness = brightness;
/*  63 */     this.contrast = contrast;
/*  64 */     this.verticalShift = verticalShift;
/*  65 */     this.horizontalShift = horizontalShift;
/*  66 */     this.phase = phase;
/*  67 */     this.pvq = pvq;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public byte[] buildRFB() {
/*  76 */     byte[] bytes = new byte[36];
/*  77 */     bytes[0] = WriteNormalType.SetCustomVideoParam.getCode();
/*  78 */     byte[] brightnessBytes = HexUtils.intToBytesBigEndian(this.brightness);
/*  79 */     System.arraycopy(brightnessBytes, 0, bytes, 4, 4);
/*  80 */     byte[] contrastBytes = HexUtils.intToBytesBigEndian(this.contrast);
/*  81 */     System.arraycopy(contrastBytes, 0, bytes, 8, 4);
/*  82 */     byte[] verticalShiftBytes = HexUtils.intToBytesBigEndian(this.verticalShift);
/*  83 */     System.arraycopy(verticalShiftBytes, 0, bytes, 12, 4);
/*  84 */     byte[] horizontalShiftBytes = HexUtils.intToBytesBigEndian(this.horizontalShift);
/*  85 */     System.arraycopy(horizontalShiftBytes, 0, bytes, 16, 4);
/*  86 */     byte[] phaseBytes = HexUtils.intToBytesBigEndian(this.phase);
/*  87 */     System.arraycopy(phaseBytes, 0, bytes, 28, 4);
/*  88 */     byte[] pvqBytes = HexUtils.intToBytesBigEndian(this.pvq);
/*  89 */     System.arraycopy(pvqBytes, 0, bytes, 32, 4);
/*  90 */     return bytes;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public int getBrightness() {
/*  99 */     return this.brightness;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void setBrightness(int brightness) {
/* 108 */     this.brightness = brightness;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public int getContrast() {
/* 117 */     return this.contrast;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void setContrast(int contrast) {
/* 126 */     this.contrast = contrast;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public int getVerticalShift() {
/* 135 */     return this.verticalShift;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void setVerticalShift(int verticalShift) {
/* 144 */     this.verticalShift = verticalShift;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public int getHorizontalShift() {
/* 153 */     return this.horizontalShift;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void setHorizontalShift(int horizontalShift) {
/* 162 */     this.horizontalShift = horizontalShift;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public int getPhase() {
/* 171 */     return this.phase;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void setPhase(int phase) {
/* 180 */     this.phase = phase;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public int getPvq() {
/* 189 */     return this.pvq;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void setPvq(int pvq) {
/* 198 */     this.pvq = pvq;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public String toString() {
/* 208 */     return String.format("brightness-%dcontrast-%dverticalShift-%dhorizontalShift-%dphase-%dpvq-%d", new Object[] {
/* 209 */           Integer.valueOf(this.brightness), Integer.valueOf(this.contrast), Integer.valueOf(this.verticalShift), Integer.valueOf(this.horizontalShift), Integer.valueOf(this.phase), Integer.valueOf(this.pvq)
/*     */         });
/*     */   }
/*     */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/core/protocol/normal/VideoParamPacket.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */