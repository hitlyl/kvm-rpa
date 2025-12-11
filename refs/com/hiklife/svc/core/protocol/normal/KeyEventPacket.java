/*    */ package com.hiklife.svc.core.protocol.normal;
import refs.com.hiklife.svc.core.protocol.normal.WriteNormalType;
import refs.com.hiklife.svc.util.HexUtils;
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ public class KeyEventPacket
/*    */ {
/*    */   public static final int UP = 0;
/*    */   public static final int DOWN = 1;
/*    */   private static final int LENGTH = 8;
/*    */   private int down;
/*    */   private int key;
/*    */   
/*    */   public KeyEventPacket(int down, int key) {
/* 27 */     if (down != 0 && down != 1) {
/* 28 */       throw new IllegalArgumentException("down 参数必须为 UP(0) 或 DOWN(1)");
/*    */     }
/* 30 */     this.down = down;
/* 31 */     this.key = key;
/*    */   }
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public byte[] buildRFB() {
/* 40 */     byte[] bytes = new byte[8];
/* 41 */     bytes[0] = WriteNormalType.KeyEvent.getCode();
/* 42 */     bytes[1] = (byte)this.down;
/* 43 */     byte[] xBytes = HexUtils.intToBytesBigEndian(this.key);
/* 44 */     System.arraycopy(xBytes, 0, bytes, 4, 4);
/* 45 */     return bytes;
/*    */   }
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public int getDown() {
/* 54 */     return this.down;
/*    */   }
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public void setDown(int down) {
/* 63 */     this.down = down;
/*    */   }
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public int getKey() {
/* 72 */     return this.key;
/*    */   }
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public void setKey(int key) {
/* 81 */     this.key = key;
/*    */   }
/*    */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/core/protocol/normal/KeyEventPacket.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */