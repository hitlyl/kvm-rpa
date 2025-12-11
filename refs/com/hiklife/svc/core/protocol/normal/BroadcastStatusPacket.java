/*    */ package com.hiklife.svc.core.protocol.normal;
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ public class BroadcastStatusPacket
/*    */ {
/*    */   public static final int LENGTH = 68;
/* 11 */   private byte[] status = new byte[64];
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public BroadcastStatusPacket(byte[] orgMsgBytes) {
/* 20 */     System.arraycopy(orgMsgBytes, 4, this.status, 0, 64);
/*    */   }
/*    */   public byte[] getStatus() {
/* 23 */     return this.status;
/*    */   }
/*    */   
/*    */   public void setStatus(byte[] status) {
/* 27 */     this.status = status;
/*    */   }
/*    */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/core/protocol/normal/BroadcastStatusPacket.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */