/*    */ package com.hiklife.svc.core.protocol.normal;
/*    */ import org.slf4j.Logger;
/*    */ import org.slf4j.LoggerFactory;

import refs.com.hiklife.svc.core.protocol.normal.AudioParamPacket;
import refs.com.hiklife.svc.core.protocol.normal.WriteNormalType;
import refs.com.hiklife.svc.util.HexUtils;
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ public class AudioParamPacket
/*    */ {
/* 13 */   private static final Logger log = LoggerFactory.getLogger(AudioParamPacket.class);
/*    */ 
/*    */   
/*    */   public static final int LENGTH = 8;
/*    */ 
/*    */   
/*    */   private boolean mute;
/*    */ 
/*    */   
/*    */   public AudioParamPacket(byte[] orgMsgBytes) {
/* 23 */     this.mute = (HexUtils.registersToInt(orgMsgBytes, 4) == 0);
/*    */   }
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public AudioParamPacket(boolean mute) {
/* 32 */     this.mute = mute;
/*    */   }
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public byte[] buildRFB() {
/* 41 */     byte[] bytes = new byte[8];
/* 42 */     bytes[0] = WriteNormalType.SetCustomAudioParam.getCode();
/* 43 */     byte[] muteBytes = HexUtils.intToBytesBigEndian(isMute() ? 0 : 1);
/* 44 */     System.arraycopy(muteBytes, 0, bytes, 4, 4);
/* 45 */     return bytes;
/*    */   }
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public boolean isMute() {
/* 54 */     return this.mute;
/*    */   }
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public void setMute(boolean mute) {
/* 63 */     this.mute = mute;
/*    */   }
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public String toString() {
/* 73 */     return "mute-" + this.mute;
/*    */   }
/*    */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/core/protocol/normal/AudioParamPacket.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */