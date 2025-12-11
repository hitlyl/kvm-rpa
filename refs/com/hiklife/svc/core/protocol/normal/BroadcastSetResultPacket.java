/*    */ package com.hiklife.svc.core.protocol.normal;
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
/*    */ public class BroadcastSetResultPacket
/*    */ {
/*    */   public static final int LENGTH = 68;
/* 17 */   private byte[] status = new byte[64];
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   private boolean success;
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public BroadcastSetResultPacket(byte[] orgMsgBytes) {
/* 30 */     System.arraycopy(orgMsgBytes, 4, this.status, 0, 64);
/* 31 */     int status = orgMsgBytes[1];
/* 32 */     this.success = (status == 1);
/*    */   }
/*    */   
/*    */   public byte[] getStatus() {
/* 36 */     return this.status;
/*    */   }
/*    */   
/*    */   public void setStatus(byte[] status) {
/* 40 */     this.status = status;
/*    */   }
/*    */   
/*    */   public boolean getSuccess() {
/* 44 */     return this.success;
/*    */   }
/*    */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/core/protocol/normal/BroadcastSetResultPacket.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */