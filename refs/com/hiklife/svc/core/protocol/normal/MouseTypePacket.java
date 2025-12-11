/*    */ package com.hiklife.svc.core.protocol.normal;

import refs.com.hiklife.svc.core.protocol.normal.WriteNormalType;

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
/*    */ 
/*    */ 
/*    */ public class MouseTypePacket
/*    */ {
/*    */   public static final int MOUSE_TYPE_ABS = 1;
/*    */   public static final int MOUSE_TYPE_REL = 0;
/*    */   public static final int LENGTH = 4;
/*    */   private int type;
/*    */   
/*    */   public MouseTypePacket(byte[] orgMsgBytes) {
/* 26 */     this.type = orgMsgBytes[1];
/*    */   }
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public MouseTypePacket(int type) {
/* 35 */     this.type = type;
/*    */   }
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public byte[] buildRFB() {
/* 44 */     byte[] bytes = new byte[4];
/* 45 */     bytes[0] = WriteNormalType.SetMouseType.getCode();
/* 46 */     bytes[1] = (byte)this.type;
/* 47 */     return bytes;
/*    */   }
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public int getType() {
/* 56 */     return this.type;
/*    */   }
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public void setType(int type) {
/* 65 */     this.type = type;
/*    */   }
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public String toString() {
/* 75 */     return String.valueOf(this.type);
/*    */   }
/*    */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/core/protocol/normal/MouseTypePacket.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */