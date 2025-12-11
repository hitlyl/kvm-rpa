/*    */ package com.hiklife.svc.core.protocol.security;

import refs.com.hiklife.svc.core.protocol.security.SecurityType;

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
/*    */ public class SecurityInput
/*    */ {
/*    */   private SecurityType.Type type;
/*    */   private String account;
/*    */   private String password;
/*    */   
/*    */   public SecurityType.Type getType() {
/* 21 */     return this.type;
/*    */   }
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public void setType(SecurityType.Type type) {
/* 30 */     this.type = type;
/*    */   }
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public String getAccount() {
/* 39 */     return this.account;
/*    */   }
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public void setAccount(String account) {
/* 48 */     this.account = account;
/*    */   }
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public String getPassword() {
/* 57 */     return this.password;
/*    */   }
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */ 
/*    */   
/*    */   public void setPassword(String password) {
/* 66 */     this.password = password;
/*    */   }
/*    */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/core/protocol/security/SecurityInput.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */