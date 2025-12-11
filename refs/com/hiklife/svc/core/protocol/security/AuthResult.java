/*    */ package com.hiklife.svc.core.protocol.security;
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
/*    */ public class AuthResult
/*    */ {
/*    */   private static final int OK = 0;
/*    */   private static final int FAILED = 1;
/*    */   private int result;
/*    */   private String failedMsg;
/*    */   
/*    */   public AuthResult(byte[] orgMsgBytes) {
/* 23 */     this.result = HexUtils.bytesToIntLittle(orgMsgBytes, 0);
/* 24 */     if (this.result == 1) {
/* 25 */       int length = HexUtils.bytesToIntLittle(orgMsgBytes, 4);
/* 26 */       this.failedMsg = HexUtils.bytesToAscii(orgMsgBytes, 8, length);
/*    */     } 
/*    */   }
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public boolean isSuccess() {
/* 36 */     return (this.result == 0);
/*    */   }
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public String getFailedMsg() {
/* 45 */     return this.failedMsg;
/*    */   }
/*    */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/core/protocol/security/AuthResult.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */