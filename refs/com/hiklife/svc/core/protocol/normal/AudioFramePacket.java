/*     */ package com.hiklife.svc.core.protocol.normal;
/*     */ import org.slf4j.Logger;
/*     */ import org.slf4j.LoggerFactory;

import refs.com.hiklife.svc.core.protocol.InvalidRFBMessageException;
import refs.com.hiklife.svc.core.protocol.normal.AudioFramePacket;
import refs.com.hiklife.svc.core.protocol.normal.decoder.G726Decoder;
import refs.com.hiklife.svc.core.protocol.normal.decoder.G726HiSiliconDecoder;
import refs.com.hiklife.svc.core.protocol.normal.decoder.G726NormalDecoder;
import refs.com.hiklife.svc.util.HexUtils;
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ public class AudioFramePacket
/*     */ {
/*  18 */   private static final Logger log = LoggerFactory.getLogger(AudioFramePacket.class);
/*     */ 
/*     */   
/*     */   public static final int LENGTH = 12;
/*     */ 
/*     */   
/*     */   private final G726Decoder.Event decoderEvent;
/*     */ 
/*     */   
/*     */   public G726Decoder decoder;
/*     */ 
/*     */ 
/*     */   
/*     */   public AudioFramePacket(G726Decoder.Event event) {
/*  32 */     this.decoderEvent = event;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public static int length(byte[] orgMsgBytes) {
/*  42 */     int audioSize = HexUtils.registersToInt(orgMsgBytes, 4);
/*  43 */     return audioSize + 8;
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
/*     */   public void parse(int deviceType, byte[] orgMsgBytes) throws InvalidRFBMessageException {
/*  55 */     switch (deviceType) {
/*     */       
/*     */       case 18:
/*     */       case 61:
/*     */       case 66:
/*  60 */         parseHisiliconAudio(orgMsgBytes);
/*     */         return;
/*     */     } 
/*     */     
/*  64 */     parseEV4000AAudio(orgMsgBytes);
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
/*     */   private void parseHisiliconAudio(byte[] orgMsgBytes) throws InvalidRFBMessageException {
/*  76 */     int audioSize = HexUtils.registersToInt(orgMsgBytes, 4);
/*  77 */     byte[] bytes = new byte[audioSize - 4];
/*  78 */     System.arraycopy(orgMsgBytes, 12, bytes, 0, audioSize - 4);
/*  79 */     if (this.decoder == null) {
/*  80 */       this.decoder = (G726Decoder)new G726HiSiliconDecoder();
/*     */     }
/*  82 */     if (this.decoderEvent != null) {
/*  83 */       this.decoder.decode(bytes, this.decoderEvent);
/*     */     }
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   private void parseEV4000AAudio(byte[] orgMsgBytes) throws InvalidRFBMessageException {
/*  94 */     int audioSize = HexUtils.registersToInt(orgMsgBytes, 4);
/*  95 */     byte[] bytes = new byte[audioSize];
/*  96 */     System.arraycopy(orgMsgBytes, 8, bytes, 0, audioSize);
/*  97 */     if (this.decoder == null) {
/*  98 */       this.decoder = (G726Decoder)new G726NormalDecoder();
/*     */     }
/* 100 */     if (this.decoderEvent != null)
/* 101 */       this.decoder.decode(bytes, this.decoderEvent); 
/*     */   }
/*     */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/core/protocol/normal/AudioFramePacket.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */