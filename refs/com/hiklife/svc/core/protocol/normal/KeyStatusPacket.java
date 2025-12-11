/*     */ package com.hiklife.svc.core.protocol.normal;
import refs.com.hiklife.svc.core.protocol.normal.KeyStatusPacket;
import refs.com.hiklife.svc.jnative.NativeLibFactory;
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
/*     */ 
/*     */ 
/*     */ 
/*     */ public class KeyStatusPacket
/*     */ {
/*     */   public static final int LENGTH = 5;
/*     */   public static final byte SIGN = 7;
/*     */   private boolean scrollState;
/*     */   private boolean numState;
/*     */   private boolean capsState;
/*     */   
/*     */   public KeyStatusPacket(byte[] orgMsgBytes) {
/*  27 */     byte status = orgMsgBytes[4];
/*  28 */     String str = Integer.toBinaryString(status & 0x7);
/*  29 */     String completeStr = completePreZero(str, 3);
/*  30 */     char[] array = completeStr.toCharArray();
/*  31 */     this.capsState = (array[0] == '1');
/*  32 */     this.numState = (array[1] == '1');
/*  33 */     this.scrollState = (array[2] == '1');
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public KeyStatusPacket(boolean capsState, boolean numState, boolean scrollState) {
/*  44 */     this.capsState = capsState;
/*  45 */     this.numState = numState;
/*  46 */     this.scrollState = scrollState;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public boolean isScrollState() {
/*  55 */     return this.scrollState;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public boolean isNumState() {
/*  64 */     return this.numState;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public boolean isCapsState() {
/*  73 */     return this.capsState;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   private String completePreZero(String srcStr, int length) {
/*  84 */     int leaveSize = length - srcStr.length();
/*  85 */     StringBuilder result = new StringBuilder(srcStr);
/*  86 */     for (int i = 0; i < leaveSize; i++) {
/*  87 */       result.insert(0, "0");
/*     */     }
/*  89 */     return result.toString();
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public static KeyStatusPacket getLocalKeyStatus() {
/*  98 */     boolean[] lockKeyState = NativeLibFactory.createJnaLib().getLockKeyState();
/*  99 */     return new KeyStatusPacket(lockKeyState[0], lockKeyState[1], lockKeyState[2]);
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public String toString() {
/* 108 */     return "KeyStatus{capsState=" + this.capsState + ", numState=" + this.numState + ", scrollState=" + this.scrollState + '}';
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void setScrollState(boolean scrollState) {
/* 116 */     this.scrollState = scrollState;
/*     */   }
/*     */   
/*     */   public void setCapsState(boolean capsState) {
/* 120 */     this.capsState = capsState;
/*     */   }
/*     */   
/*     */   public void setNumState(boolean numState) {
/* 124 */     this.numState = numState;
/*     */   }
/*     */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/core/protocol/normal/KeyStatusPacket.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */